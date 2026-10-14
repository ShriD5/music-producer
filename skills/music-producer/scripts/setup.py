# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "soundfile"]
# ///
"""Setup + health check.

  uv run setup.py doctor        # what works right now, what each missing piece would unlock
  uv run setup.py ace           # install the free local music model (ACE-Step 1.5, MIT, ~10 GB incl. weights)
  uv run setup.py keys          # print where keys go and what they unlock

Put MUSIC_PRODUCER_HOME=/big/disk/music-producer in ~/.config/music-producer/keys.env to keep model weights off a small disk.
"""
import platform
import shutil
import subprocess
import sys

import _common as C
import providers as P

KEYS = [
    ("FREESOUND_API_KEY", "free", "better free SFX search (freesound.org/apiv2/apply, 1 minute)"),
    ("OPENROUTER_API_KEY", "free/paid", "ears: Gemini Flash critiques the mix (~$0.005 per film)"),
    ("FAL_KEY", "paid", "ElevenLabs Music plans, Lyria, MiniMax, Stable Audio, ElevenLabs SFX, video foley"),
    ("ELEVENLABS_API_KEY", "paid", "ElevenLabs Music + SFX direct on your own plan (music needs a paid plan)"),
]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def doctor():
    ok = lambda b: "ok " if b else "-- "
    print(f"music-producer doctor  ({platform.system()} {platform.machine()}, python {platform.python_version()})\n")
    ff = shutil.which("ffmpeg")
    print(f"{ok(ff)} ffmpeg {'' if ff else ' REQUIRED: brew install ffmpeg / apt install ffmpeg'}")
    print(f"{ok(shutil.which('uv'))} uv")
    ace = P.ace_dir()
    print(f"{ok(ace)} local music (ACE-Step 1.5): {ace or 'not installed -> uv run setup.py ace'}")
    print(f"ok  free SFX: openverse (no key)")
    for k, cost, what in KEYS:
        print(f"{ok(C.key(k, required=False))} {k:<20} [{cost}] {what}")
    ek = C.key("ELEVENLABS_API_KEY", required=False)
    if ek:
        try:
            sub = P.http("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": ek})
            tier_, used, lim = sub.get("tier"), sub.get("character_count", 0), sub.get("character_limit", 0)
            print(f"    ElevenLabs plan: {tier_}, {lim - used:,} credits left")
            if tier_ == "free":
                print("    ! free plan: no Music API, and SFX are non-commercial with attribution required "
                      "(credit elevenlabs.io). Use fal or a paid plan for anything you ship.")
        except SystemExit as e:
            print(f"    ElevenLabs key check failed: {e}")
    if C.key("FAL_KEY", required=False):
        print("    fal balance isn't readable via API; an empty balance shows up as a clear error on the first call")
    t = P.tier()
    print(f"\ntier: {t}  (MUSIC_PRODUCER_TIER=free|paid in ~/.config/music-producer/keys.env)")
    try:
        mp = P.pick_music("auto")
    except SystemExit as e:
        mp = f"none ({e})"
    print(f"  music -> {mp}\n  sfx   -> {P.pick_sfx('auto')}\n  mix/master/analysis -> local, free")
    if t == "free" and (C.key("FAL_KEY", required=False) or C.key("ELEVENLABS_API_KEY", required=False)):
        print("  (paid keys found; set MUSIC_PRODUCER_TIER=paid, or pass --provider eleven per call, to use them)")


def ace():
    if platform.system() == "Darwin" and platform.machine() != "arm64":
        print("warning: Intel Mac: ACE-Step runs on CPU only and will be very slow.")
    d = P.home() / "ace-step"
    d.parent.mkdir(parents=True, exist_ok=True)
    if not (d / ".git").exists():
        print(f"cloning ACE-Step 1.5 into {d} ...")
        r = run(["git", "clone", "--depth", "1", "https://github.com/ACE-Step/ACE-Step-1.5.git", str(d)])
        if r.returncode:
            sys.exit(r.stderr)
    print("installing its environment (torch etc., a few GB) ...")
    r = subprocess.run(["uv", "sync"], cwd=d)
    if r.returncode:
        sys.exit("uv sync failed (see above)")
    print("downloading weights on first generation (~6 GB turbo DiT + VAE + 0.6B planner) ...")
    print(f"done. `uv run music.py gen --plan audio/music/plan.json` now runs locally for free.")


def keys():
    print("Keys are read from: env vars, ./.env, ~/.config/music-producer/keys.env\n")
    for k, cost, what in KEYS:
        print(f"{k}=...   # [{cost}] {what}")
    print("MUSIC_PRODUCER_TIER=free   # or paid\nMUSIC_PRODUCER_HOME=~/.cache/music-producer   # model weights live here")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "doctor"
    {"doctor": doctor, "ace": ace, "keys": keys}.get(cmd, doctor)()

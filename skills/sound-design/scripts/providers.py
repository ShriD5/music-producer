"""Where audio comes from. Free first; paid only when the user has a key AND chose the paid tier.

Tiers (SOUND_DESIGN_TIER = free | paid, default free):
  music  free: ace (ACE-Step 1.5, local, MIT)            paid: eleven (fal or ElevenLabs direct), lyria, minimax, ...
  sfx    free: freesound (free key) > openverse (no key)  paid: eleven (fal or ElevenLabs direct), stable, sonilo
  ears   openrouter (any audio-capable model; free ones exist) - optional, analyze.py is the real QA

Keys/config are read from the environment, then ./.env, then ~/.config/sound-design/keys.env:
  FAL_KEY, ELEVENLABS_API_KEY, FREESOUND_API_KEY, OPENROUTER_API_KEY, SOUND_DESIGN_TIER, SOUND_DESIGN_HOME,
  SOUND_DESIGN_ELEVEN_ROUTE (fal|direct), SOUND_DESIGN_EARS_MODEL
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

import _common as C

# ---------------------------------------------------------------- registry
# cost(seconds) in USD; "route" says which key unlocks it
MUSIC = {
    "ace": {"cost": lambda s: 0.0, "route": "local", "plan": "caption", "note": "ACE-Step 1.5, local, free, MIT"},
    "eleven": {"cost": lambda s: 0.6 * s / 60, "route": "fal|elevenlabs", "plan": "sections",
               "note": "ElevenLabs Music v2.5 composition plan (section times locked to the cut)"},
    "lyria": {"cost": lambda s: 0.10, "route": "fal", "plan": "prompt", "endpoint": "google/lyria-3.5"},
    "lyria3pro": {"cost": lambda s: 0.08, "route": "fal", "plan": "prompt", "endpoint": "fal-ai/lyria3/pro"},
    "minimax": {"cost": lambda s: 0.002 * s, "route": "fal", "plan": "prompt", "endpoint": "minimax/music-3"},
    "stable": {"cost": lambda s: 0.0376, "route": "fal", "plan": "prompt",
               "endpoint": "fal-ai/stable-audio-3/medium/text-to-audio"},
    "sonilo": {"cost": lambda s: 0.009 * s, "route": "fal", "plan": "video", "endpoint": "sonilo/v1.1/video-to-music"},
}
SFX = {
    "openverse": {"cost": lambda s: 0.0, "route": "none", "kind": "library", "note": "CC0 recordings, no key"},
    "freesound": {"cost": lambda s: 0.0, "route": "freesound", "kind": "library", "note": "CC0 recordings, free key"},
    "eleven": {"cost": lambda s: 0.002 * s, "route": "fal|elevenlabs", "kind": "gen"},
    "stable": {"cost": lambda s: 0.0206, "route": "fal", "kind": "gen",
               "endpoint": "fal-ai/stable-audio-3/small/sfx/text-to-audio"},
    "sonilo": {"cost": lambda s: 0.0018 * s, "route": "fal", "kind": "gen",
               "endpoint": "sonilo/v1.1/text-to-sound-effects"},
}


def tier() -> str:
    return (C.key("SOUND_DESIGN_TIER", required=False) or "free").lower()


def home() -> pathlib.Path:
    h = C.key("SOUND_DESIGN_HOME", required=False)
    return pathlib.Path(h).expanduser() if h else pathlib.Path("~/.cache/sound-design").expanduser()


def ace_dir() -> pathlib.Path | None:
    d = home() / "ace-step"
    return d if (d / ".venv").exists() and (d / "acestep").exists() else None


def has(route: str) -> bool:
    return any({"local": ace_dir() is not None, "none": True, "fal": bool(C.key("FAL_KEY", required=False)),
                "elevenlabs": bool(C.key("ELEVENLABS_API_KEY", required=False)),
                "freesound": bool(C.key("FREESOUND_API_KEY", required=False))}[r] for r in route.split("|"))


def pick_music(name: str) -> str:
    if name != "auto":
        if not has(MUSIC[name]["route"]):
            sys.exit(f"music provider '{name}' needs {MUSIC[name]['route'].replace('|', ' or ')} "
                     "(run `uv run setup.py doctor`)")
        return name
    if tier() == "paid" and has(MUSIC["eleven"]["route"]):
        return "eleven"
    if ace_dir():
        return "ace"
    if has(MUSIC["eleven"]["route"]):
        sys.exit("free tier selected but local ACE-Step isn't installed. Run `uv run setup.py ace` (free, ~10 GB), "
                 "or set SOUND_DESIGN_TIER=paid to use your fal/ElevenLabs key.")
    sys.exit("no music provider available. Run `uv run setup.py ace` for the free local model.")


def pick_sfx(name: str) -> str:
    if name != "auto":
        if not has(SFX[name]["route"]):
            sys.exit(f"sfx provider '{name}' needs {SFX[name]['route'].replace('|', ' or ')}")
        return name
    if tier() == "paid" and has(SFX["eleven"]["route"]):
        return "eleven"
    return "freesound" if has("freesound") else "openverse"


# ---------------------------------------------------------------- http
def http(url, data=None, headers=None, method=None, timeout=300, raw=False):
    body = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
    h = {"User-Agent": "sound-design-skill/1.0"} | ({"Content-Type": "application/json"} if isinstance(data, (dict, list)) else {})
    h |= headers or {}
    req = urllib.request.Request(url, data=body, headers=h, method=method or ("POST" if data is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"{url.split('?')[0]} -> HTTP {e.code}: {e.read().decode(errors='ignore')[:600]}")
    return out if raw else json.loads(out)


# ---------------------------------------------------------------- ElevenLabs (fal or direct)
def eleven_via_fal() -> bool:
    """SOUND_DESIGN_ELEVEN_ROUTE=fal|direct; default fal when FAL_KEY exists, else your ElevenLabs key."""
    route = (C.key("SOUND_DESIGN_ELEVEN_ROUTE", required=False) or "").lower()
    if route in ("fal", "direct"):
        return route == "fal"
    return bool(C.key("FAL_KEY", required=False))


def eleven_music(plan_chunks: dict, seed: int, dest: pathlib.Path) -> str:
    """composition_plan {"chunks": [...]} -> wav. Uses fal when FAL_KEY exists, else ElevenLabs direct."""
    if eleven_via_fal():
        res = C.fal_run("elevenlabs/music/v2.5", {"composition_plan": plan_chunks, "output_format": "pcm_48000",
                                                   "seed": seed})
        C.download(C.fal_audio_url(res), dest.with_suffix(".raw"))
        route = "fal"
    else:
        audio = http("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128",
                     {"composition_plan": plan_chunks, "model_id": "music_v2_5", "seed": seed},
                     {"xi-api-key": C.key("ELEVENLABS_API_KEY")}, raw=True, timeout=600)
        dest.with_suffix(".raw").write_bytes(audio)
        route = "elevenlabs"
    C.to_wav48(dest.with_suffix(".raw"), dest)
    dest.with_suffix(".raw").unlink()
    return route


def eleven_sfx(text: str, dur: float | None, influence: float, loop: bool, dest: pathlib.Path) -> str:
    if eleven_via_fal():
        p = {"text": text, "prompt_influence": influence, "output_format": "pcm_48000", "loop": loop}
        if dur:
            p["duration_seconds"] = max(0.5, min(22, dur))
        res = C.fal_run("fal-ai/elevenlabs/sound-effects/v2", p, quiet=True)
        C.download(C.fal_audio_url(res), dest)
        return "fal"
    p = {"text": text, "prompt_influence": influence, "loop": loop, "model_id": "eleven_text_to_sound_v2"}
    if dur:
        p["duration_seconds"] = max(0.5, min(30, dur))
    dest.write_bytes(http("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128", p,
                          {"xi-api-key": C.key("ELEVENLABS_API_KEY")}, raw=True))
    return "elevenlabs"


# ---------------------------------------------------------------- local ACE-Step
def ace_generate(req: dict) -> list[dict]:
    d = ace_dir()
    if not d:
        sys.exit("ACE-Step not installed: `uv run setup.py ace`")
    req = {"ace_dir": str(d), **req}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(req, fh)
    driver = pathlib.Path(__file__).parent / "backends" / "ace_gen.py"
    env = {**__import__("os").environ, "HF_HOME": str(home() / "hf")}
    p = subprocess.Popen(["uv", "run", "--project", str(d), "python", str(driver), fh.name], cwd=str(d), env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outs, errs = [], []
    for line in p.stdout:
        line = line.strip()
        if line.startswith("{"):
            outs.append(json.loads(line))
            print(f"  ace take done in {outs[-1]['secs']}s", file=sys.stderr)
    err = p.stderr.read()
    if p.wait() != 0 or not outs:
        lines = [l for l in err.splitlines() if l.strip()]
        key_lines = [l for l in lines if l.startswith("ACE_ERROR") or "Error:" in l][-3:]
        sys.exit("ACE-Step failed:\n" + "\n".join(key_lines or lines[-15:]))
    return outs


# ---------------------------------------------------------------- recorded libraries (free)
LICENSE_OK = {"cc0": "Creative Commons 0", "by": "Attribution"}


def library_search(provider: str, query: str, dur: float | None, n: int, licenses=("cc0",)) -> list[dict]:
    """Search CC recordings. Returns [{url, title, author, license, page, duration}] best first."""
    if provider == "freesound":
        lic = " OR ".join(f'"{LICENSE_OK[l]}"' for l in licenses)
        flt = f"license:({lic})"
        if dur:
            flt += f" duration:[{max(0.05, dur * 0.3):.2f} TO {max(dur * 4, dur + 2):.2f}]"
        q = urllib.parse.urlencode({"query": query, "filter": flt, "sort": "score", "page_size": max(15, n * 4),
                                    "fields": "id,name,username,license,duration,previews,url,avg_rating,num_downloads",
                                    "token": C.key("FREESOUND_API_KEY")})
        res = http(f"https://freesound.org/apiv2/search/?{q}").get("results", [])
        rows = [{"url": r["previews"]["preview-hq-mp3"], "title": r["name"], "author": r["username"],
                 "license": r["license"], "page": r["url"], "duration": r.get("duration"),
                 "pop": (r.get("avg_rating") or 0) + min(3, (r.get("num_downloads") or 0) / 2000)} for r in res]
    else:
        q = urllib.parse.urlencode({"q": query, "license": ",".join(licenses), "page_size": max(20, n * 5),
                                    "mature": "false"})
        res = http(f"https://api.openverse.org/v1/audio/?{q}").get("results", [])
        rows = [{"url": r["url"], "title": r["title"], "author": r.get("creator") or "",
                 "license": f"{r['license']} {r.get('license_version') or ''}".strip(),
                 "page": r.get("foreign_landing_url") or r["url"],
                 "duration": (r.get("duration") or 0) / 1000 or None, "pop": 0} for r in res if r.get("url")]
    if dur:  # closest length first (a 0.4 s click shouldn't come from a 30 s field recording), popularity breaks ties
        rows = [r for r in rows if not r["duration"] or r["duration"] <= max(dur * 6, dur + 6)]
        rows.sort(key=lambda r: (abs(__import__("math").log((r["duration"] or dur) / dur)) - 0.15 * r["pop"]))
    return rows[:n]


def credit(root, row: dict, file: str):
    f = C.proj(root) / "CREDITS.md"
    if not f.exists():
        f.write_text("# Sound credits\n\nRecordings used under their Creative Commons licenses.\n\n")
    with f.open("a") as fh:
        fh.write(f"- `{file}`: \"{row['title']}\" by {row['author'] or 'unknown'} ({row['license']}), {row['page']}\n")


def query_from_prompt(prompt: str) -> str:
    """Generation prompts are long; library search wants the noun + verb. Keep the first clause, drop studio words."""
    first = prompt.split(",")[0]
    first = re.sub(r"\b(single|one|tiny|small|quick|short|very|soft|crisp|deep|cute|close-?mic|dry|no \w+)\b", " ",
                   first, flags=re.I)
    return " ".join(first.split()[:6]) or prompt[:40]

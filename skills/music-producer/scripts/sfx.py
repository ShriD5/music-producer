# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "soundfile", "soxr", "pedalboard"]
# ///
"""Bespoke sound effects: one designed sound per cue, several takes each, trimmed and indexed by transient.

  gen       uv run sfx.py gen --cues audio/sfx/cues.json [--only logo-hit swipe] [--root .]
  video     uv run sfx.py video renders/video.mp4 [--segments audio/sfx/foley.json] [--prompt "..."]
  variants  uv run sfx.py variants audio/sfx/tick-1.wav --n 6      # round-robin copies for repeated hits
  tune      uv run sfx.py tune audio/sfx/tine-*.wav --key "C minor"  # clip pitch that lands each take in key
  sub       uv run sfx.py sub --note A1 [--drop 12 --dur 1.4]      # designed sub drop under an impact, in key
  index     uv run sfx.py index                                    # re-scan audio/sfx/*.wav

cues.json: [{"id": "logo-hit", "prompt": "...", "query": "wood latch", "dur": 2.5, "n": 3, "provider": "auto",
             "influence": 0.45, "loop": false, "keep_head": false, "licenses": ["cc0"]}]
  provider (per cue or --provider): auto | openverse (free, no key, CC0 recordings) | freesound (free key, better
  search) | eleven ($0.002/s via fal or your ElevenLabs key; best for designed/UI/impacts) | stable (Stable Audio 3,
  $0.02, textures/beds) | sonilo ($0.0018/s, natural foley).
  query: short search words for the recorded libraries (noun + verb: "wood knock", "paper flutter"); derived from
  the prompt when missing. Recorded takes longer than 1.5x dur are cropped to their strongest hit.
  Credits for recordings go to audio/CREDITS.md. keep_head: true for swells/reverse sounds (aligned by their END).
audio/sfx/index.json records per take: duration, peak (transient offset from file start), loudness.
"""
import argparse
import json
import pathlib
import sys

import numpy as np

import _common as C
import providers as P

VIDEO_SFX = ("sonilo/v1.1/video-to-sound-effects", lambda s: 0.009 * s)


def normalize(x, target_db=-12.0, ceiling_db=-1.0):
    """Loudest 50 ms window to target_db, peak capped at ceiling_db, so session gains mean the same thing
    for every take. Returns (x, dud) where dud = the take is basically silent."""
    env, _ = C.rms_env(x, win=0.05, hop=0.01)
    pk = float(C.db(np.abs(x).max()))
    if pk < -45:
        return x, True
    g = min(target_db - float(env.max()), ceiling_db - pk)
    return (x * C.undb(g)).astype(np.float32), False


def describe(path):
    x = C.load(path)
    env, _ = C.rms_env(x, win=0.4, hop=0.1)
    return {"duration": round(x.shape[-1] / C.SR, 3), "peak": round(C.peak_time(x), 4),
            "peak_dbfs": round(float(C.db(np.abs(x).max())), 1), "loud_db": round(float(env.max()), 1)}


def write_index(root):
    d = C.proj(root) / "sfx"
    idx_path = d / "index.json"
    old = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    idx = {}
    for w in sorted(d.glob("*.wav")):
        idx[w.name] = {**old.get(w.name, {}), **describe(w)}
    idx_path.write_text(json.dumps(idx, indent=1))
    return idx


def crop_to_hit(x, dur, pre=0.03):
    """Recordings often hold several events (three knocks, a long tail). Keep the strongest one, `dur` long."""
    if x.shape[-1] <= int(dur * 1.5 * C.SR):
        return x
    pk = C.peak_time(x)
    a = max(0, int((pk - pre) * C.SR))
    y = x[..., a:a + int(dur * C.SR)]
    return C.fade(y, 0.002, min(dur * 0.3, 0.25))


def take(x, cue):
    """Common post-processing for every take, generated or recorded."""
    if not cue.get("keep_head"):
        x = C.trim_silence(x, thresh_db=-55, keep_head=0.003, keep_tail=0.08)
    else:
        x = C.trim_silence(x, thresh_db=-70, keep_head=0.0, keep_tail=0.08)
    if cue.get("_library") and cue.get("dur") and not cue.get("loop"):
        if cue.get("keep_head"):  # swells: keep the `dur` seconds that END on the loudest moment
            if x.shape[-1] > int(cue["dur"] * 1.5 * C.SR):
                e = min(x.shape[-1], int((C.peak_time(x) + 0.03) * C.SR))
                if e < int(cue["dur"] * 0.5 * C.SR):  # loudest moment is at the very start: take the opening
                    e = int(cue["dur"] * C.SR)
                x = C.fade(x[..., max(0, e - int(cue["dur"] * C.SR)):e], min(0.3, cue["dur"] / 3), 0.005)
        else:
            x = crop_to_hit(x, cue["dur"])
    x = C.fade(x, fin=0.0015, fout=min(0.05, x.shape[-1] / C.SR / 4))
    return normalize(x)


def gen(a):
    d = C.proj(a.root) / "sfx"
    d.mkdir(exist_ok=True)
    cues = json.loads(pathlib.Path(a.cues).read_text())
    meta = {}
    for cue in cues:
        if a.only and cue["id"] not in a.only:
            continue
        prov = P.pick_sfx(cue.get("provider") or a.provider)
        info = P.SFX[prov]
        dur, n = cue.get("dur"), cue.get("n", 3)
        raws = []  # (raw path, extra meta)
        if info["kind"] == "library":
            q0 = cue.get("query") or P.query_from_prompt(cue["prompt"])
            words = q0.split()
            # widen until something comes back: length filter off, then drop leading adjectives
            tries = [(q0, dur), (q0, None)] + [(" ".join(words[i:]), None) for i in range(1, len(words))]
            rows, q = [], q0
            for q, dd in tries:
                rows = P.library_search(prov, q, dd, n, tuple(cue.get("licenses", ["cc0"])))
                if rows:
                    break
            if rows and q != q0:
                print(f"{cue['id']:28s} '{q0}' found nothing; used '{q}'")
            if not rows:
                print(f"{cue['id']:28s} no {prov} results for '{q}' (add a shorter \"query\" to the cue)")
                continue
            for k, row in enumerate(rows):
                raw = d / f".{cue['id']}-{k + 1}.raw"
                C.download(row["url"], raw)
                raws.append((raw, {"query": q, "source": row}))
        else:
            for k in range(n):
                raw = d / f".{cue['id']}-{k + 1}.raw"
                if prov == "eleven":
                    route = P.eleven_sfx(cue["prompt"], dur, cue.get("influence", 0.45), cue.get("loop", False), raw)
                    C.log_cost(a.root, f"{route}/elevenlabs-sfx-v2", info["cost"](dur or 4),
                               raw.stem.lstrip(".") + ("" if route == "fal" else " (ElevenLabs credits, fal-equivalent)"))
                else:
                    if prov == "stable":
                        payload = {"prompt": cue["prompt"], "duration": dur or 4, "output_format": "wav",
                                   "seed": 31 + k * 101,
                                   "negative_prompt": cue.get("negative", "music, melody, speech, voice, low quality")}
                    else:
                        payload = {"prompt": cue["prompt"], "duration": dur or 4, "audio_format": "wav"}
                    res = C.fal_run(info["endpoint"], payload, quiet=True)
                    C.download(C.fal_audio_url(res), raw)
                    C.log_cost(a.root, info["endpoint"], info["cost"](dur or 4), raw.stem.lstrip("."))
                raws.append((raw, {}))
        for k, (raw, extra) in enumerate(raws):
            x = C.load(raw)
            raw.unlink()
            x, dud = take(x, {**cue, "_library": info["kind"] == "library"})
            out = d / f"{cue['id']}-{k + 1}.wav"
            if dud:
                print(f"{out.name:28s} DUD (near-silent take, skipped)")
                continue
            C.save(out, x)
            if extra.get("source"):
                P.credit(a.root, extra["source"], out.name)
            meta[out.name] = {"prompt": cue["prompt"], "provider": prov, "cue": cue["id"], **extra, **describe(out)}
            m = meta[out.name]
            src = f"  <- {extra['source']['title'][:38]} ({extra['source']['license']})" if extra.get("source") else ""
            print(f"{out.name:28s} {m['duration']:5.2f}s  peak@{m['peak']:.3f}s  {m['peak_dbfs']:5.1f} dBFS{src}")
    idx_path = d / "index.json"
    idx = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    idx.update(meta)
    idx_path.write_text(json.dumps(idx, indent=1))
    print(f"spent so far: ${C.total_cost(a.root):.2f}")


def video(a):
    d = C.proj(a.root) / "sfx"
    d.mkdir(exist_ok=True)
    endpoint, price = VIDEO_SFX
    dur = C.duration(a.video)
    payload = {"video_url": C.fal_upload(a.video), "audio_format": "wav"}
    if a.prompt:
        payload["prompt"] = a.prompt
    if a.segments:
        payload["segments"] = json.loads(pathlib.Path(a.segments).read_text())
    res = C.fal_run(endpoint, payload)
    raw = d / ".foley.raw"
    C.download(C.fal_audio_url(res), raw)
    out = C.to_wav48(raw, d / (a.name + ".wav"))
    raw.unlink()
    C.log_cost(a.root, endpoint, price(dur), out.name)
    segs = res.get("segments") or []
    for s in segs:
        tags = (s.get("meta") or {}).get("tags") or []
        print(f"  {s.get('start', 0):6.2f}-{s.get('end', 0):6.2f}s  {', '.join(tags)}")
    print(f"-> {out} (full-length bed; place at 0 on the amb bus and cut what fights the score)")


NOTE_RE = __import__("re").compile(r"^([A-Ga-g])([#b]?)(-?\d)$")


def note_hz(note: str) -> float:
    m = NOTE_RE.match(note.strip())
    if not m:
        raise SystemExit(f"bad note '{note}' (use e.g. A1, F#1, Bb0)")
    idx = "C D EF G A B".index(m.group(1).upper()) + {"#": 1, "b": -1, "": 0}[m.group(2)]
    midi = 12 * (int(m.group(3)) + 1) + idx
    return 440.0 * 2 ** ((midi - 69) / 12)


def sub(a):
    """Designed sub drop (the low layer under an impact), tuned to the score's key. Pitch falls `drop` semitones
    onto the note in `glide` s, decays over `dur`; soft saturation adds harmonics so phones still hear it."""
    f1 = note_hz(a.note)
    f0 = f1 * 2 ** (a.drop / 12)
    n = int(a.dur * C.SR)
    t = np.arange(n) / C.SR
    f = f1 + (f0 - f1) * np.exp(-t / max(a.glide / 4, 1e-3))
    ph = 2 * np.pi * np.cumsum(f) / C.SR
    env = np.minimum(1, t / 0.004) * np.exp(-t / (a.dur / 3.5))
    y = np.tanh(a.drive * np.sin(ph)) / np.tanh(a.drive) * env
    if a.click:
        y[:int(0.006 * C.SR)] += np.random.default_rng(1).standard_normal(int(0.006 * C.SR)) * 0.25 * np.linspace(1, 0, int(0.006 * C.SR))
    x, _ = normalize(np.vstack([y, y]).astype(np.float32))
    out = C.free_name(C.proj(a.root) / "sfx", a.name or "sub-" + a.note.replace("#", "s"))
    C.save(out, C.fade(x, 0, 0.05))
    write_index(a.root)
    print(f"{out.name}: {f0:.0f}->{f1:.0f} Hz over {a.glide}s, {a.dur}s decay (layer it under the impact with align: attack)")


NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def tune(a):
    """Detect each take's pitch and print the clip `pitch` that puts it on the nearest tonic-chord note."""
    m = __import__("re").match(r"([A-Ga-g][#b]?)\s*(major|minor)", a.key.strip(), __import__("re").I)
    if not m:
        sys.exit('--key like "C minor" or "F# major"')
    root = NAMES.index({"Db": "C#", "D#": "Eb", "Gb": "F#", "G#": "Ab", "A#": "Bb"}.get(m.group(1).capitalize(), m.group(1).capitalize()))
    chord = [(root + i) % 12 for i in ((0, 3, 7) if m.group(2).lower() == "minor" else (0, 4, 7))]
    for f in a.files:
        x = C.mono(C.load(f))
        pk = int(C.peak_time(x) * C.SR)
        seg = x[pk + int(0.01 * C.SR): pk + int(0.25 * C.SR)]
        if len(seg) < 2048:
            print(f"{pathlib.Path(f).name:24s} too short to pitch")
            continue
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n=1 << 16))
        fr = np.fft.rfftfreq(1 << 16, 1 / C.SR)
        band = (fr > 80) & (fr < 5000)
        f0 = float(fr[band][np.argmax(sp[band])])
        clarity = float(sp[band].max() / (np.median(sp[band]) + 1e-9))
        midi = 69 + 12 * np.log2(f0 / 440)
        pc = round(midi) % 12
        cents = (midi - round(midi)) * 100
        best = min(((c - pc + 6) % 12 - 6 for c in chord), key=abs)
        shift = best - cents / 100
        tonal = "tonal" if clarity > 40 else "noisy (pitch matters less)"
        to_root = ((root - pc + 6) % 12 - 6) - cents / 100
        print(f"{pathlib.Path(f).name:24s} {NAMES[pc]:>2}{cents:+4.0f}c  ->  pitch {shift:+.2f} st to land on "
              f"{NAMES[(pc + best) % 12]}, or {to_root:+.2f} st for the tonic {NAMES[root]} (use the tonic on the "
              f"final button/logo)  [{tonal}]")


def variants(a):
    import pedalboard as pb
    x = C.load(a.file)
    src = pathlib.Path(a.file)
    rng = np.random.default_rng(len(src.name))
    for k in range(a.n):
        semis = float(rng.uniform(-a.spread, a.spread))
        tilt = float(rng.uniform(-2, 2))
        board = pb.Pedalboard([pb.PitchShift(semitones=semis), pb.HighShelfFilter(cutoff_frequency_hz=4000, gain_db=tilt)])
        y = board(x, C.SR) * C.undb(rng.uniform(-1.5, 0))
        out = src.with_name(f"{src.stem}-rr{k + 1}.wav")
        C.save(out, y.astype(np.float32))
        print(f"{out.name}  {semis:+.2f} st  {tilt:+.1f} dB air")
    write_index(a.root)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("gen")
    g.add_argument("--cues", required=True)
    g.add_argument("--only", nargs="*")
    g.add_argument("--provider", default="auto", choices=["auto"] + list(P.SFX),
                   help="default for cues without their own provider; auto = free library unless tier=paid")
    g.add_argument("--root", default=".")
    v = sp.add_parser("video")
    v.add_argument("video")
    v.add_argument("--prompt")
    v.add_argument("--segments", help='[{"start":0,"end":4.2,"prompt":"..."}] contiguous from 0')
    v.add_argument("--name", default="foley")
    v.add_argument("--root", default=".")
    r = sp.add_parser("variants")
    r.add_argument("file")
    r.add_argument("--n", type=int, default=4)
    r.add_argument("--spread", type=float, default=0.6, help="max pitch offset in semitones")
    r.add_argument("--root", default=".")
    tn = sp.add_parser("tune")
    tn.add_argument("files", nargs="+")
    tn.add_argument("--key", required=True, help='score key from music.py analyze, e.g. "C minor"')
    b = sp.add_parser("sub")
    b.add_argument("--note", required=True, help="landing note, e.g. A1 (55 Hz) or D1; use the score's tonic")
    b.add_argument("--drop", type=float, default=12, help="semitones it falls from")
    b.add_argument("--glide", type=float, default=0.15)
    b.add_argument("--dur", type=float, default=1.4)
    b.add_argument("--drive", type=float, default=1.8, help="saturation: harmonics for small speakers")
    b.add_argument("--click", action="store_true", help="add a tiny transient")
    b.add_argument("--name")
    b.add_argument("--root", default=".")
    i = sp.add_parser("index")
    i.add_argument("--root", default=".")
    i.add_argument("--normalize", action="store_true", help="re-level every take in audio/sfx (drops duds)")
    a = ap.parse_args()
    if a.cmd == "gen":
        gen(a)
    elif a.cmd == "video":
        video(a)
    elif a.cmd == "variants":
        variants(a)
    elif a.cmd == "sub":
        sub(a)
    elif a.cmd == "tune":
        tune(a)
    else:
        if a.normalize:
            for w in sorted((C.proj(a.root) / "sfx").glob("*.wav")):
                x, dud = normalize(C.load(w))
                if dud:
                    w.unlink()
                    print(f"{w.name}: dud, removed")
                else:
                    C.save(w, x)
        for k, m in write_index(a.root).items():
            print(f"{k:28s} {m['duration']:5.2f}s  peak@{m['peak']:.3f}s")


if __name__ == "__main__":
    main()

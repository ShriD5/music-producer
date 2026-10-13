# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "soundfile", "soxr", "pyloudnorm"]
# ///
"""Blind listening pack for the human: the only reliable judge of "does this sound premium".

  uv run pack.py audio/music/*.wav [--refs ref1.wav ref2.wav] [--secs 43] [--out audio/pack]

Writes loudness-matched (-16 LUFS) mp3s labelled A, B, C... in shuffled order, an index.html with players and
pick buttons, and key.json (which letter is which file). Loudness matching matters: louder always sounds better.
Mix references (real films you admire) in with --refs so the listener calibrates against the real thing.
AI ears (listen.py) can't do this job: in testing, Gemini ranked a real Arc launch film last of 9 and called it
"AI warbling", and two orderings of the same files produced opposite rankings.
"""
import argparse
import json
import pathlib
import random
import subprocess

import pyloudnorm as pyln

import _common as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--refs", nargs="*", default=[])
    ap.add_argument("--secs", type=float, default=45)
    ap.add_argument("--out", default="audio/pack")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    items = [(f, "candidate") for f in a.files] + [(f, "reference") for f in a.refs]
    random.Random(a.seed).shuffle(items)
    meter = pyln.Meter(C.SR)
    key = {}
    for i, (f, kind) in enumerate(items):
        letter = chr(ord("A") + i)
        x = C.load(f)[:, :int(a.secs * C.SR)]
        x = C.fade(x * C.undb(-16 - meter.integrated_loudness(x.T)), 0.01, 0.5)
        wav = out / f".{letter}.wav"
        C.save(wav, x)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "192k",
                        str(out / f"{letter}.mp3")], check=True)
        wav.unlink()
        key[letter] = {"file": str(f), "kind": kind}
    (out / "key.json").write_text(json.dumps(key, indent=1))
    rows = "\n".join(
        f'<div class=r><b>{l}</b><audio controls preload=none src="{l}.mp3"></audio>'
        f'<button onclick="pick(\'{l}\')">best</button></div>' for l in key)
    (out / "index.html").write_text(f"""<!doctype html><meta charset=utf-8><title>Blind listening pack</title>
<style>body{{font:15px system-ui;max-width:640px;margin:40px auto;background:#111;color:#eee}}
.r{{display:flex;gap:12px;align-items:center;margin:10px 0}}b{{width:20px}}audio{{flex:1}}
button{{background:#333;color:#eee;border:0;padding:6px 12px;border-radius:6px}}#o{{margin-top:20px;color:#8f8}}</style>
<h2>Which sounds most like a premium launch film?</h2>
<p>All clips are loudness-matched. Some are real launch films, some are candidates. Use headphones, then a phone speaker.</p>
{rows}<p id=o></p>
<script>function pick(l){{document.getElementById('o').textContent='Picked '+l+'. Tell the agent the letter (and what bugs you about the others).'}}</script>
""")
    print(f"-> {out / 'index.html'}  ({len(key)} clips; answers in {out / 'key.json'}, don't peek)")


if __name__ == "__main__":
    main()

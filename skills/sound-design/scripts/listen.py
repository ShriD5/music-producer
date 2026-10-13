# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "soundfile"]
# ///
"""Borrowed ears: send the final cut (or a mix, or several candidates) to Gemini, which actually hears audio.

  uv run listen.py renders/video.sound.mp4 --brief audio/SOUND.md          # critique the film
  uv run listen.py audio/music/score-1.wav audio/music/score-2.wav --compare --brief audio/SOUND.md
  uv run listen.py audio/sfx/logo-hit-*.wav --compare --ask "which hit is the tightest, least generic?"

Second opinion, not ground truth. Measured behaviour: scores are inflated (9-10/10 on almost anything), and it
"hears" events the brief asks for even when they are absent, so --compare strips timestamps from the brief. Use it
to find problems (genericness, artifacts, harshness); confirm with analyze.py before acting. ~$0.03-0.08 per call.
"""
import argparse
import base64
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import key  # noqa: E402

DEFAULT_MODEL = "google/gemini-3.8-flash"


FILM_RUBRIC = """You are a senior re-recording mixer and sound designer reviewing a product launch film before release.
Watch AND listen. Be blunt and specific, timestamped to the tenth of a second. Judge:
1. Identity: does the music feel made for THIS product and picture, or like generic stock / AI library music? Name the genre you hear.
2. Sync: do hits land exactly on cuts and on-screen actions? List any that are early/late or missing on a moment that needs one.
3. Over-scoring: are there sounds on things that did not need them? Does it feel like a toy?
4. Dynamics + arc: is there build, release, a moment of space before the biggest reveal, and a resolved ending (button / ring-out)?
5. Clarity: is any voice-over intelligible over the music on a phone speaker? Anything harsh, boomy, muddy, phasey?
6. Artifacts: warbly/metallic AI artifacts, clicks, bad loop points, abrupt cuts in the music.
7. The three changes that would most improve it, in priority order.
Return JSON: {"genre_heard": str, "identity_score": 1-10, "sync_score": 1-10, "mix_score": 1-10,
 "issues": [{"t": seconds or null, "severity": "high|med|low", "what": str, "fix": str}], "top3": [str]}"""

COMPARE_RUBRIC = """You are a senior music supervisor / sound designer. You get several numbered candidates for the same slot.
FIRST describe each candidate blind, only from what you hear: genre, instruments actually audible, and the energy
every 5 seconds (quiet / medium / full). Only then judge each against the brief: fit, distinctiveness (penalize
generic stock / AI-library sound), production quality, artifacts (warble, smeared transients, metallic tails, bad
loops). Never report an event because the brief asks for it; if you are unsure whether something happens, say so.
Return JSON: {"heard": {"1": {"genre": str, "instruments": [str], "energy_by_5s": [str]}, ...},
 "ranking": [candidate numbers best first], "notes": {"1": str, ...}, "pick_reason": str}"""

HONESTY = """
Report only what you actually hear and see. The brief states intentions, not facts: do not assume an intended event
happened. Timestamps must come from the media; if unsure, give null."""


def encode(path):
    p = pathlib.Path(path)
    td = tempfile.mkdtemp()
    if p.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv"):
        out = pathlib.Path(td) / "v.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(p), "-vf", "scale=-2:540", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "30", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
        return {"type": "video_url",
                "video_url": {"url": "data:video/mp4;base64," + base64.b64encode(out.read_bytes()).decode()}}
    out = pathlib.Path(td) / "a.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(p), "-c:a", "libmp3lame", "-b:a", "160k", str(out)],
                   check=True)
    return {"type": "input_audio", "input_audio": {"data": base64.b64encode(out.read_bytes()).decode(), "format": "mp3"}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--brief", help="SOUND.md or any text file with the sonic brief")
    ap.add_argument("--ask", help="extra question")
    ap.add_argument("--model", help="any OpenRouter audio-capable model; default SOUND_DESIGN_EARS_MODEL or "
                    "google/gemini-3.8-flash (cheap, accurate). ~google/gemini-pro-latest for a deeper read")
    a = ap.parse_args()
    brief = pathlib.Path(a.brief).read_text()[:6000] if a.brief else ""
    if a.compare and "\n## " in brief:  # candidates: concept only, the timed maps just get parroted back
        brief = brief.split("\n## ")[0]
        brief = re.sub(r"\b\d+(\.\d+)?\s*(-\s*\d+(\.\d+)?\s*)?s\b", "", brief)
    content = [{"type": "text", "text": (COMPARE_RUBRIC if a.compare else FILM_RUBRIC) + HONESTY
                + (f"\n\nBRIEF:\n{brief}" if brief else "") + (f"\n\nALSO: {a.ask}" if a.ask else "")}]
    for k, f in enumerate(a.files, 1):
        if a.compare:
            content.append({"type": "text", "text": f"Candidate {k}: {pathlib.Path(f).name}"})
        content.append(encode(f))
    model = a.model or key("SOUND_DESIGN_EARS_MODEL", required=False) or DEFAULT_MODEL
    body = {"model": model, "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"}, "temperature": 0.2}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key('OPENROUTER_API_KEY')}",
                                          "Content-Type": "application/json"})
    try:
        res = json.loads(urllib.request.urlopen(req, timeout=600).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"openrouter {e.code}: {e.read().decode()[:600]}")
    txt = res["choices"][0]["message"]["content"]
    try:
        print(json.dumps(json.loads(txt.strip().removeprefix("```json").removesuffix("```")), indent=2))
    except json.JSONDecodeError:
        print(txt)
    u = res.get("usage", {})
    print(f"\n[{res.get('model')}] tokens in {u.get('prompt_tokens')} out {u.get('completion_tokens')}"
          + (f" cost ${u['cost']:.3f}" if u.get("cost") else ""), file=sys.stderr)


if __name__ == "__main__":
    main()

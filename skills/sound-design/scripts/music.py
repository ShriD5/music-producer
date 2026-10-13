# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "scipy", "soundfile", "soxr", "librosa", "pyloudnorm", "pedalboard", "matplotlib"]
# ///
"""Score generation, analysis and conforming to picture.

  gen      uv run music.py gen --plan audio/music/plan.json [--n 2]          # auto: free local ACE-Step
           uv run music.py gen --provider eleven --plan audio/music/plan.json # paid: sections locked to the cut
           uv run music.py gen --provider lyria|lyria3pro|minimax|stable --prompt "..." [--duration 40]
           uv run music.py gen --provider sonilo --video renders/video.mp4 [--prompt "..."]
  repaint  uv run music.py repaint audio/music/score-1.wav --start 24 --end 29 --prompt "drums stop, sleepy celesta"
  extend   uv run music.py extend audio/music/x.wav --after 12 [--before 0] --prompt "same track, continues"
  analyze  uv run music.py analyze audio/music/score-1.wav
  fit      uv run music.py fit audio/music/score-1.wav --duration 42 [--hit 5.0 --src 12.4] [--bpm 120]
                [--end-hit 38.0 [--end-src auto|S]] [--fin 0] [--fout 1.5] --out audio/music/fit.wav

Plan file (eleven): section ends are absolute output times so sections lock to the cut.
  {"styles": ["..."], "negative": ["..."], "chunks": [
     {"name": "Intro", "until": 5.0, "styles": ["..."], "text": "{sparse, felt piano, room tone}"},
     {"name": "Drop",  "until": 21.0, "styles": ["..."], "text": "{full band enters on beat 1}", "adherence": "high"}]}
"""
import argparse
import json
import pathlib
import re
import sys

import numpy as np

import _common as C
import providers as P

EXTEND = ("fal-ai/stable-audio-3/medium/audio-outpainting", lambda s: 0.0446)
NOTE_NAMES = r"[A-G](?:#|b|-flat|-sharp| flat| sharp)?"


def eleven_plan(plan):
    chunks, prev = [], 0.0
    for c in plan["chunks"]:
        end = c.get("until", prev + c.get("seconds", 0))
        ms = int(round((end - prev) * 1000))
        if ms < 3000:
            sys.exit(f"chunk '{c['name']}' is {ms} ms; ElevenLabs needs >= 3000 ms per chunk. Merge it with a neighbour "
                     "and put the change inside the text as a {direction} instead.")
        chunks.append({
            "text": f"[{c['name']}]\n{c.get('text', '').strip()}".strip(),
            "duration_ms": min(ms, 120000),
            "positive_styles": list(dict.fromkeys(plan.get("styles", []) + c.get("styles", []))),
            "negative_styles": list(dict.fromkeys(plan.get("negative", []) + c.get("negative", []))) or None,
            "context_adherence": c.get("adherence"),
        })
        prev = end
    return {"chunks": [{k: v for k, v in ch.items() if v is not None} for ch in chunks]}, prev


def plan_meta(plan):
    """bpm / key / duration from explicit plan fields, else parsed out of the style tags."""
    styles = " ".join(plan.get("styles", []))
    bpm = plan.get("bpm")
    if not bpm and (m := re.search(r"(\d{2,3})\s*bpm", styles, re.I)):
        bpm = float(m.group(1))
    key = plan.get("key")
    if not key and (m := re.search(rf"({NOTE_NAMES})\s+(major|minor)", styles, re.I)):
        note = m.group(1).replace("-flat", "b").replace(" flat", "b").replace("-sharp", "#").replace(" sharp", "#")
        key = f"{note[0].upper()}{note[1:]} {m.group(2).lower()}"
    dur = plan["chunks"][-1].get("until") if plan.get("chunks") else plan.get("duration")
    return bpm, key, dur


def plan_caption(plan, compact=False):
    """A section plan folded into one caption for prompt-only models (ACE-Step, Lyria, MiniMax, Stable Audio)."""
    skip = re.compile(r"\d+\s*bpm|\b(major|minor)\b|great production quality|instrumental", re.I)
    styles = [t for t in plan.get("styles", []) if not skip.search(t)]
    arc, prev = [], 0.0
    for c in plan.get("chunks", []):
        end = c.get("until", prev + c.get("seconds", 0))
        txt = re.sub(r"[{}]", "", c.get("text", "")).strip()
        bits = ", ".join(c.get("styles", []) + ([txt] if txt and not compact else []))
        arc.append(f"{c['name'].lower()} at {prev:g}s: {bits}")
        prev = end
    neg = plan.get("negative", [])
    cap = ", ".join(styles) + ". Arrangement: " + "; ".join(arc) + "."
    if neg:
        cap += " Avoid: " + ", ".join(neg) + "."
    return cap + " Instrumental, no vocals, crisp modern mix."


def gen(a):
    out = C.proj(a.root) / "music"
    out.mkdir(exist_ok=True)
    prov = P.pick_music(a.provider)
    plan = json.loads(pathlib.Path(a.plan).read_text()) if a.plan else None
    if prov == "eleven" and not plan:
        sys.exit("--plan required for eleven")
    if not plan and not a.prompt and prov != "sonilo":
        sys.exit("--plan or --prompt required")
    bpm, key, pdur = plan_meta(plan) if plan else (a.bpm, a.key, None)
    bpm, key = a.bpm or bpm, a.key or key
    secs = pdur or a.duration
    info = P.MUSIC[prov]
    prompt = a.prompt or (plan_caption(plan) if plan else None)
    if prompt and info.get("max_prompt") and len(prompt) > info["max_prompt"]:
        prompt = (plan_caption(plan, compact=True) if plan else prompt)[:info["max_prompt"]]
    if prompt and prov != "eleven" and (bpm or key) and plan:
        prompt += "".join([f" {bpm:g} BPM." if bpm else "", f" Key {key}." if key else ""])
    print(f"music: {prov} ({info.get('note') or info.get('endpoint')}), {a.n} take(s), ~${info['cost'](secs) * a.n:.2f}",
          file=sys.stderr)
    made, seed0 = [], a.seed or 1000
    if prov == "ace":
        outs = P.ace_generate({"out_dir": str(out / ".ace"), "n": a.n, "seed": seed0, "caption": prompt,
                               "duration": secs, "bpm": bpm, "keyscale": key or "", "timesignature": "4",
                               "lm": a.lm, "steps": a.steps})
        for k, o in enumerate(outs):
            wav = C.to_wav48(o["path"], out / f"{a.name}-{k + 1}.wav")
            wav.with_suffix(".json").write_text(json.dumps({"provider": "ace", "seed": o["seed"], "caption": prompt,
                                                            "bpm": bpm, "key": key, "lm": a.lm}, indent=2))
            C.log_cost(a.root, "local/ace-step-1.5", 0.0, wav.name)
            made.append(wav)
    for k in range(a.n if prov != "ace" else 0):
        seed = seed0 + k * 7919
        wav = out / f"{a.name}-{k + 1}.wav"
        if prov == "eleven":
            cp, _ = eleven_plan(plan)
            route = P.eleven_music(cp, seed, wav)
            meta = {"provider": "eleven", "route": route, "seed": seed, "plan": cp}
            C.log_cost(a.root, f"{route}/elevenlabs-music-v2.5", info["cost"](secs) if route == "fal" else 0.0,
                       wav.name + ("" if route == "fal" else " (ElevenLabs credits)"))
        else:
            if prov == "sonilo":
                payload = {"video_url": a._video_url, "num_samples": 1, "prompt_influence": a.influence}
                if prompt:
                    payload["prompt"] = prompt
            else:
                payload = {"prompt": prompt}
                if prov in ("minimax", "stable"):
                    payload |= {"duration": secs, "seed": seed}
                if prov == "minimax":  # lyrics is required; section tags + [instrumental] keep it wordless
                    tags = [f"[{c['name'].lower()}]" for c in plan["chunks"]] if plan else ["[intro]", "[outro]"]
                    payload["lyrics"] = "\n".join(f"{t}\n[instrumental]" for t in tags)
                if prov == "stable":
                    payload |= {"output_format": "wav",
                                "negative_prompt": a.negative or "vocals, singing, low quality, muffled, distorted"}
            res = C.fal_run(info["endpoint"], payload)
            C.download(C.fal_audio_url(res), wav.with_suffix(".raw"))
            C.to_wav48(wav.with_suffix(".raw"), wav)
            wav.with_suffix(".raw").unlink()
            meta = {"provider": prov, "endpoint": info["endpoint"], "seed": seed, "payload": payload}
            C.log_cost(a.root, info["endpoint"], info["cost"](secs), wav.name)
        wav.with_suffix(".json").write_text(json.dumps(meta, indent=2))
        made.append(wav)
    for w in made:
        analyze_file(w, quiet=False, plan=a.plan)
    print(f"spent so far: ${C.total_cost(a.root):.2f}")


def repaint(a):
    """Regenerate one stretch of a take in place (free, local ACE-Step). Use it to force a planned section
    (a quiet breakdown, a stop, a bigger entrance) that the first pass ignored."""
    src = pathlib.Path(a.file).resolve()
    info = analyze_file(src, quiet=True)
    outs = P.ace_generate({"task": "repaint", "src_audio": str(src), "repaint_start": a.start, "repaint_end": a.end,
                           "caption": a.prompt, "out_dir": str(src.parent / ".ace"), "n": a.n,
                           "seed": a.seed or 2000, "bpm": info["bpm"], "keyscale": "", "lm": "none", "steps": a.steps,
                           "strength": a.strength})
    for k, o in enumerate(outs):
        dst = src.with_name(f"{src.stem}-rp{k + 1}.wav")
        C.to_wav48(o["path"], dst)
        C.log_cost(a.root, "local/ace-step-1.5 repaint", 0.0, dst.name)
        analyze_file(dst)


def extend(a):
    endpoint, price = EXTEND
    url = C.fal_upload(a.file)
    payload = {"audio_url": url, "extend_seconds_after": a.after, "extend_seconds_before": a.before,
               "prompt": a.prompt, "output_format": "wav"}
    res = C.fal_run(endpoint, payload)
    src = pathlib.Path(a.file)
    raw = src.with_name(f".{src.stem}-ext.raw")
    C.download(C.fal_audio_url(res), raw)
    ext = C.load(raw)
    raw.unlink()
    C.log_cost(a.root, endpoint, price(0), src.stem + "-ext")
    orig = C.load(a.file)
    L = orig.shape[-1]
    if a.after and not a.before:
        # Stable Audio re-encodes the source and tends to leave ~1 s of near-silence before the continuation, which
        # then resumes on the beat grid. Keep the untouched original, skip the gap in whole beats, crossfade.
        env, et = C.rms_env(ext[..., L:], win=0.05, hop=0.01)
        live = float(np.median(C.rms_env(orig, win=0.05, hop=0.01)[0]))
        idx = np.argmax(env > live - 15) if np.any(env > live - 15) else 0
        gap = float(et[idx]) - 0.025 if idx else 0.0
        skip = 0.0
        if gap > 0.12:
            beat = 60.0 / max(40.0, analyze_file(a.file, quiet=True)["bpm"])
            k = max(1, round(gap / beat))
            skip = k * beat if k * beat >= gap - 0.05 else (k + 1) * beat
            print(f"continuation resumes {gap:.2f}s after the source end: skipping {skip:.2f}s ({round(skip / beat)} beats)")
        tail = ext[..., L + int(skip * C.SR):]
        out = xfade_join(orig, tail, ms=15)
    else:
        out = ext
        print("note: --before output is used as returned (source re-encoded); check the seam by ear / energy")
    dst = C.save(a.out or src.with_name(f"{src.stem}-ext.wav"), out)
    analyze_file(dst)


# ---------- analysis ----------
KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def analyze_file(path, quiet=False, plan=None):
    import librosa
    import pyloudnorm as pyln
    x = C.load(path)
    m = C.mono(x)
    sr = C.SR
    y = librosa.resample(m, orig_sr=sr, target_sr=22050)
    hop = 512
    onset = librosa.onset.onset_strength(y=y, sr=22050, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=22050, hop_length=hop)
    tempo = float(np.atleast_1d(tempo)[0])
    bt = librosa.frames_to_time(beats, sr=22050, hop_length=hop)
    if len(bt) >= 8:  # librosa's tempo bins are coarse (120 reads as 117.5): refine from the beat-time slope
        d = np.diff(bt)
        good = np.abs(d - np.median(d)) < 0.1 * np.median(d)
        if good.sum() >= 6:
            tempo = 60.0 / float(np.mean(d[good]))
    # downbeat phase: which of every-4th-beat carries the most low-end onset energy
    S = np.abs(librosa.stft(y, hop_length=hop))
    low = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S[:40]), sr=22050, hop_length=hop)
    phase = int(np.argmax([low[beats[k::4]].sum() if len(beats[k::4]) else 0 for k in range(4)])) if len(beats) >= 8 else 0
    downbeats = bt[phase::4]
    chroma = librosa.feature.chroma_cqt(y=y, sr=22050).mean(axis=1)
    scores = [(np.corrcoef(np.roll(KS_MAJ, i), chroma)[0, 1], f"{NOTES[i]} major") for i in range(12)]
    scores += [(np.corrcoef(np.roll(KS_MIN, i), chroma)[0, 1], f"{NOTES[i]} minor") for i in range(12)]
    key = max(scores)[1]
    env, et = C.rms_env(x, win=0.5, hop=0.25)
    env = np.maximum(env, -120)
    med0 = float(np.median(env))
    starts_at = float(et[np.argmax(env > med0 - 20)]) - 0.25
    # entrances: biggest 1.5 s energy rises (where a drop / full band arrives)
    lag = 6
    rise = np.r_[np.zeros(lag), env[lag:] - env[:-lag]]
    ent = []
    for i in np.argsort(-rise):
        if rise[i] < 4:
            break
        t = float(et[i])
        if t < starts_at + 1.0 or env[max(0, i - lag)] < med0 - 30:  # the file starting is not an entrance
            continue
        if all(abs(t - e["t"]) > 3 for e in ent):
            snap = float(downbeats[np.argmin(np.abs(downbeats - t))]) if len(downbeats) else t
            ent.append({"t": round(t, 2), "downbeat": round(snap, 3), "rise_db": round(float(rise[i]), 1)})
        if len(ent) == 4:
            break
    dur = x.shape[-1] / sr
    med = float(np.median(env))
    tail_db = float(env[-4:].mean()) if len(env) > 4 else med
    ending = "natural" if tail_db < med - 20 else "abrupt/looping"
    final_hit = None
    loud = np.where(env > med - 20)[0]
    end_t = float(et[loud[-1]]) if len(loud) else dur
    if len(downbeats):
        tail_beats = [b for b in bt if end_t - 10 <= b <= end_t]
        if tail_beats:
            fr = librosa.time_to_frames(tail_beats, sr=22050, hop_length=hop)
            fr = fr[fr < len(onset)]
            if len(fr):
                final_hit = round(float(librosa.frames_to_time(fr[np.argmax(onset[fr])], sr=22050, hop_length=hop)), 3)
    lufs = float(pyln.Meter(sr).integrated_loudness(x.T))
    res = {"file": str(path), "duration": round(dur, 2), "bpm": round(tempo, 1), "key": key,
           "starts_at": round(max(0.0, starts_at), 2), "beat_phase_s": round(float(bt[0]), 3) if len(bt) else None, "downbeats": [round(float(d), 3) for d in downbeats],
           "entrances": ent, "ending": ending, "final_hit": final_hit, "lufs": round(lufs, 1),
           "energy_db_per_s": [round(float(v), 1) for v in env[::4]]}
    if plan:  # did the take follow the plan? level step at each boundary + mean level per section
        fine, ft = C.rms_env(x, win=0.1, hop=0.05)
        fine = np.maximum(fine, -120)
        rows, prev = [], 0.0
        for c in json.loads(pathlib.Path(plan).read_text())["chunks"]:
            end = c.get("until", prev + c.get("seconds", 0))
            sel = env[(et >= prev) & (et < end)]
            pre = fine[(ft >= prev - 0.4) & (ft < prev)]
            post = fine[(ft >= prev) & (ft < prev + 0.4)]
            jump = round(float(post.mean() - pre.mean()), 1) if len(pre) and len(post) else None
            rows.append({"section": c["name"], "from": prev, "to": end, "enter_jump_db": jump,
                         "mean_db": round(float(sel.mean()), 1) if len(sel) else None})
            prev = end
        res["sections"] = rows
    pathlib.Path(path).with_suffix(".analysis.json").write_text(json.dumps(res, indent=1))
    if not quiet:
        print(f"{pathlib.Path(path).name}: {dur:.1f}s  {tempo:.1f} bpm  {key}  {lufs:.1f} LUFS  starts@{max(0.0, starts_at):.2f}s  ending={ending}"
              f"  final_hit={final_hit}\n  entrances: " + ", ".join(f"{e['downbeat']}s (+{e['rise_db']} dB)" for e in ent)
              + "\n  energy/s: " + " ".join(f"{v:.0f}" for v in res["energy_db_per_s"]))
        for r in res.get("sections", []):
            print(f"  {r['from']:5.1f}-{r['to']:5.1f}s  {r['section']:<12} mean {r['mean_db']} dB  "
                  f"step at start {r['enter_jump_db']:+} dB" if r["enter_jump_db"] is not None else
                  f"  {r['from']:5.1f}-{r['to']:5.1f}s  {r['section']:<12} mean {r['mean_db']} dB")
    return res


# ---------- conform ----------
def xfade_join(a, b, ms=30):
    n = int(ms / 1000 * C.SR)
    n = min(n, a.shape[-1], b.shape[-1])
    if n < 2:
        return np.concatenate([a, b], axis=-1)
    r = np.linspace(0, np.pi / 2, n)
    mid = a[..., -n:] * np.cos(r) + b[..., :n] * np.sin(r)
    return np.concatenate([a[..., :-n], mid, b[..., n:]], axis=-1)


def fit(a):
    import pedalboard
    x = C.load(a.file)
    sr = C.SR
    info = analyze_file(a.file, quiet=True)
    src_bpm = info["bpm"]
    ratio = 1.0
    if a.bpm:
        ratio = a.bpm / src_bpm
        if abs(ratio - 1) > 0.08:
            print(f"warning: {src_bpm}->{a.bpm} bpm is a {abs(ratio - 1) * 100:.0f}% stretch; artifacts likely above 8%",
                  file=sys.stderr)
        x = pedalboard.time_stretch(x, sr, stretch_factor=ratio, high_quality=True, transient_mode="crisp")
        x = np.ascontiguousarray(x, dtype=np.float32)
    s2o = lambda s: s / ratio  # source time -> stretched time
    D = a.duration
    start = 0.0
    if a.hit is not None and a.src is not None:
        start = s2o(a.src) - a.hit
    elif a.start:
        start = s2o(a.start)
    pre = np.zeros((2, 0), np.float32)
    if start < 0:  # source event is earlier than the hit: pad with silence (or let pre-roll SFX carry it)
        pre = np.zeros((2, int(-start * sr)), np.float32)
        start = 0.0
    body = np.concatenate([pre, x[..., int(start * sr):]], axis=-1)
    log = [f"source {start * ratio:.3f}s -> output {pre.shape[-1] / sr:.3f}s" + (f" (stretched x{ratio:.4f})" if ratio != 1 else "")]

    if a.end_hit is not None:
        es = info["final_hit"] if a.end_src in (None, "auto") else float(a.end_src)
        if es is None:
            sys.exit("no final hit detected; pass --end-src seconds")
        tail = x[..., int(s2o(es) * sr):]
        cut = int(a.end_hit * sr)
        body = xfade_join(body[..., :cut], tail, ms=12)
        log.append(f"button: source {es:.3f}s spliced at output {a.end_hit:.3f}s (hard splice - put the A-hit SFX here to mask it)")

    need = int(D * sr)
    if body.shape[-1] < need:
        if a.end_hit is None:
            short = D - body.shape[-1] / sr
            sys.exit(f"music runs out {short:.1f}s early. Use `music.py extend --after {np.ceil(short + 2):.0f}` "
                     "(musical continuation) or regenerate longer; looping bars is a last resort.")
        log.append(f"ending rings out at {body.shape[-1] / sr:.2f}s, silence after")
        body = C.fade(body, fin=a.fin)
        body = np.pad(body, ((0, 0), (0, need - body.shape[-1])))
    else:
        rest = C.rms_env(body[..., need:])[0].max() if body.shape[-1] - need > C.SR * 0.06 else -120
        body = C.fade(body[..., :need], fin=a.fin, fout=a.fout if rest > -50 else 0.05)
        if rest > -50:
            log.append(f"music still playing at {D:.2f}s: faded over {a.fout}s (a button ending with --end-hit sounds better)")
    out = pathlib.Path(a.out)
    C.save(out, body)
    print("\n".join(log))
    print(f"-> {out}  {body.shape[-1] / sr:.2f}s")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("gen")
    g.add_argument("--provider", default="auto", choices=["auto"] + list(P.MUSIC),
                   help="auto = free local ACE-Step unless SOUND_DESIGN_TIER=paid")
    g.add_argument("--plan", help="section plan json (exact sections on eleven; folded into a caption elsewhere)")
    g.add_argument("--prompt")
    g.add_argument("--negative")
    g.add_argument("--video")
    g.add_argument("--bpm", type=float)
    g.add_argument("--key", help='e.g. "D major"')
    g.add_argument("--influence", type=float, default=0.6)
    g.add_argument("--duration", type=float, default=45)
    g.add_argument("--n", type=int, default=2)
    g.add_argument("--seed", type=int)
    g.add_argument("--lm", default="auto",
                   help="ace only: planner LM. auto = 0.6B planner with >= 24 GB RAM, none below "
                        "(acestep-5Hz-lm-0.6B | acestep-5Hz-lm-1.7B | none)")
    g.add_argument("--steps", type=int, default=8, help="ace only: diffusion steps (turbo: 8)")
    g.add_argument("--name", default="score")
    g.add_argument("--root", default=".")
    r = sp.add_parser("repaint")
    r.add_argument("file")
    r.add_argument("--start", type=float, required=True)
    r.add_argument("--end", type=float, required=True)
    r.add_argument("--prompt", required=True, help="what this stretch should become")
    r.add_argument("--n", type=int, default=2)
    r.add_argument("--seed", type=int)
    r.add_argument("--steps", type=int, default=8)
    r.add_argument("--strength", type=float, default=0.5,
                   help="0-1, how far the stretch may move from the original (0.5 measured: -3.6 dB on a 'quiet' ask)")
    r.add_argument("--root", default=".")
    e = sp.add_parser("extend")
    e.add_argument("file")
    e.add_argument("--after", type=float, default=0)
    e.add_argument("--before", type=float, default=0)
    e.add_argument("--prompt", default="seamless continuation of the same track, same instruments and groove")
    e.add_argument("--out")
    e.add_argument("--root", default=".")
    n = sp.add_parser("analyze")
    n.add_argument("files", nargs="+")
    n.add_argument("--plan", help="plan.json: print mean level per planned section to check adherence")
    f = sp.add_parser("fit")
    f.add_argument("file")
    f.add_argument("--duration", type=float, required=True)
    f.add_argument("--hit", type=float, help="output time where the source event must land")
    f.add_argument("--src", type=float, help="source time of that event (e.g. an entrance from analyze)")
    f.add_argument("--start", type=float, help="plain source offset when there is no hit to align")
    f.add_argument("--bpm", type=float, help="stretch to this tempo (Rubber Band), e.g. a spot.py tempo candidate")
    f.add_argument("--end-hit", type=float, help="output time of the final button (logo / CTA)")
    f.add_argument("--end-src", help="source time of the ending hit, or auto")
    f.add_argument("--fin", type=float, default=0.0)
    f.add_argument("--fout", type=float, default=1.5)
    f.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "gen":
        if a.provider == "sonilo":
            a._video_url = C.fal_upload(a.video)
        gen(a)
    elif a.cmd == "repaint":
        repaint(a)
    elif a.cmd == "extend":
        extend(a)
    elif a.cmd == "analyze":
        for p in a.files:
            analyze_file(p, plan=a.plan)
    else:
        fit(a)


if __name__ == "__main__":
    main()

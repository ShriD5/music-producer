# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "scipy", "soundfile", "soxr", "matplotlib"]
# ///
"""Spotting pass: read a picture-locked video, find cuts + big motion, suggest tempos that land on the cuts,
and draw a contact sheet so you can SEE what happens at each sync point before writing cues.

  uv run spot.py renders/video.mp4 [--root .] [--cut 0.28] [--marks marks.json] [--bpm 110 130]
  uv run spot.py renders/video.mp4 --zoom 8.5 10.5        # 10 fps strip to place a hit on its exact frame

Writes audio/spot.json and audio/spot.png. `--marks` takes [{"t": 5.0, "label": "logo"}] from the edit /
storyboard; those are exact and beat the detector, so pass them whenever the timeline is known.
"""
import argparse
import json
import pathlib
import re
import subprocess
import tempfile

import numpy as np
from scipy.signal import find_peaks

import _common as C


def scene_scores(video):
    cmd = ["ffmpeg", "-v", "error", "-i", str(video), "-an", "-vf",
           "scale=320:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file=-", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    ts, ss = [], []
    t = None
    for line in out.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m.group(1))
        m = re.search(r"lavfi\.scene_score=([\d.]+)", line)
        if m and t is not None:
            ts.append(t)
            ss.append(float(m.group(1)))
    return np.array(ts), np.array(ss)


def fps_of(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout.strip()
    a, b = r.split("/")
    return float(a) / float(b)


def tempo_fit(times, lo=70, hi=180, tol=0.04):
    """BPMs whose beat grid lands on the most cuts. Returns [(bpm, phase, score, hits)]."""
    times = np.asarray(times)
    if len(times) < 2:
        return []
    res = []
    for bpm in np.arange(lo, hi + 0.01, 0.5):
        p = 60 / bpm
        best = (0, 0, 0)
        for ph in np.arange(0, p, 0.005):
            d = np.mod(times - ph, p)
            err = np.minimum(d, p - d)
            score = float(np.mean(np.exp(-(err / tol) ** 2)))
            if score > best[0]:
                best = (score, ph, int((err < 1.5 * tol).sum()))
        res.append((float(bpm), round(best[1], 3), round(best[0], 3), best[2]))
    res.sort(key=lambda r: -r[2])
    picked = []
    for r in res:  # drop near-duplicates and octave twins
        if all(abs(r[0] - q[0]) > 3 and abs(r[0] - 2 * q[0]) > 3 and abs(2 * r[0] - q[0]) > 3 for q in picked):
            picked.append(r)
        if len(picked) == 6:
            break
    return [{"bpm": b, "phase_s": ph, "score": s, "cuts_on_beat": h} for b, ph, s, h in picked]


def zoom(a):
    """10 fps strip between two times, labelled, so hits can be placed on the exact frame."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t0, t1 = a.zoom
    ts = np.arange(t0, t1 + 1e-6, 0.1)[:40]
    cols = 8
    rows = int(np.ceil(len(ts) / cols))
    fig = plt.figure(figsize=(cols * 2.4, rows * 1.6), facecolor="#111")
    with tempfile.TemporaryDirectory() as td:
        for k, t in enumerate(ts):
            f = pathlib.Path(td) / f"{k}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", a.video, "-frames:v", "1",
                            "-vf", "scale=360:-2", str(f)], check=False)
            ax = fig.add_subplot(rows, cols, k + 1)
            if f.exists():
                ax.imshow(plt.imread(str(f)))
            ax.set_title(f"{t:.2f}s", color="w", fontsize=8)
            ax.axis("off")
    fig.tight_layout()
    out = C.proj(a.root) / f"zoom-{t0:g}-{t1:g}.png"
    fig.savefig(out, dpi=80, facecolor=fig.get_facecolor())
    print(f"-> {out} (Read it)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--root", default=".")
    ap.add_argument("--cut", type=float, default=0.28, help="scene score that counts as a hard cut")
    ap.add_argument("--marks", help="json list of {t,label} from the timeline")
    ap.add_argument("--bpm", nargs=2, type=float, default=[70, 180], metavar=("LO", "HI"),
                    help="tempo range for candidates (your genre's band)")
    ap.add_argument("--zoom", nargs=2, type=float, metavar=("T0", "T1"),
                    help="instead: a 10 fps frame strip of T0..T1 (audio/zoom-T0-T1.png) to place hits exactly")
    a = ap.parse_args()
    if a.zoom:
        return zoom(a)

    dur = C.duration(a.video)
    fps = fps_of(a.video)
    ts, ss = scene_scores(a.video)
    # a cut is a one-frame spike; dark / low-contrast films never reach the absolute threshold, so also accept
    # frames that tower over their +-3 frame neighbourhood
    pad = np.pad(ss, 3, mode="edge")
    neigh = np.max(np.stack([pad[3 + k: 3 + k + len(ss)] for k in (-3, -2, -1, 1, 2, 3)]), axis=0)
    spike = ss / (neigh + 1e-3)
    cand = (ss >= a.cut) | ((ss >= 0.03) & (spike >= 4))
    cuts_i, _ = find_peaks(np.where(cand, ss, 0), height=1e-6, distance=max(1, int(0.2 * fps)))
    cuts = [round(float(ts[i]), 3) for i in cuts_i]
    sm = np.convolve(np.where(cand, 0, ss), np.ones(5) / 5, mode="same")
    mh = max(0.008, float(np.percentile(sm, 97))) if len(sm) else 1
    mot_i, _ = find_peaks(sm, height=mh, prominence=mh / 2, distance=max(1, int(0.4 * fps)))
    motion = [round(float(ts[i]), 3) for i in mot_i if all(abs(ts[i] - c) > 0.25 for c in cuts)]
    marks = json.loads(pathlib.Path(a.marks).read_text()) if a.marks else []
    sync = sorted(set([m["t"] for m in marks] + cuts))
    # a grid always "fits" 3-5 points; below 6 sync points the candidates mean nothing
    tempos = tempo_fit(sync, lo=a.bpm[0], hi=a.bpm[1]) if len(sync) >= 6 else []

    out = C.proj(a.root)
    data = {"video": str(pathlib.Path(a.video).resolve()), "duration": round(dur, 3), "fps": round(fps, 3),
            "frame_s": round(1 / fps, 4), "cuts": cuts, "motion": motion, "marks": marks, "tempo_candidates": tempos,
            "activity": {"mean_scene_score": round(float(ss.mean()), 4) if len(ss) else 0,
                         "cuts_per_10s": round(10 * len(cuts) / dur, 2)}}
    (out / "spot.json").write_text(json.dumps(data, indent=2))

    # contact sheet: one frame just after every sync point (+ opening and closing frame)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    points = sorted(set([0.05] + sync + [max(0, dur - 0.1)]))
    filled = []  # no blind stretch longer than 2.5 s between looks
    for p0, p1 in zip(points, points[1:]):
        filled.append(p0)
        k = int((p1 - p0) // 2.5)
        filled += [p0 + (p1 - p0) * (j + 1) / (k + 1) for j in range(k)]
    points = (filled + [points[-1]])[:40]
    cols = 5
    rows = int(np.ceil(len(points) / cols))
    fig = plt.figure(figsize=(cols * 3.2, rows * 2.1 + 2.2), facecolor="#111")
    with tempfile.TemporaryDirectory() as td:
        for k, t in enumerate(points):
            f = pathlib.Path(td) / f"{k}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{min(t + 0.08, dur - 0.04):.3f}", "-i", a.video,
                            "-frames:v", "1", "-vf", "scale=480:-2", str(f)], check=False)
            ax = fig.add_subplot(rows + 1, cols, k + 1)
            if f.exists():
                ax.imshow(plt.imread(str(f)))
            label = next((m["label"] for m in marks if abs(m["t"] - t) < 0.01), "cut" if t in cuts else "")
            ax.set_title(f"{t:.2f}s {label}", color="w", fontsize=9)
            ax.axis("off")
    ax = fig.add_subplot(rows + 1, 1, rows + 1)
    ax.plot(ts, ss, color="#7af", lw=0.8)
    for c in cuts:
        ax.axvline(c, color="#f55", lw=0.8)
    for m in motion:
        ax.axvline(m, color="#fc3", lw=0.6, ls="--")
    for m in marks:
        ax.axvline(m["t"], color="#5f5", lw=1.2)
    ax.set_xlim(0, dur)
    ax.set_facecolor("#181818")
    ax.tick_params(colors="w", labelsize=8)
    ax.set_title("scene change (red = cut, yellow = big motion, green = marks)", color="w", fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "spot.png", dpi=90, facecolor=fig.get_facecolor())

    print(f"{dur:.2f}s @ {fps:.2f}fps  cuts={len(cuts)}  motion={len(motion)}  marks={len(marks)}")
    print("cuts:", cuts)
    print("motion:", motion)
    if not tempos:
        print("tempo: fewer than 6 cuts/marks, no tempo-to-picture suggestion (pick a tempo from the genre)")
    for t in tempos[:4]:
        print(f"tempo {t['bpm']:>6} bpm  phase {t['phase_s']:.3f}s  fit {t['score']:.2f}  ({t['cuts_on_beat']}/{len(sync)} on beat)")
    print(f"-> {out / 'spot.json'}\n-> {out / 'spot.png'}  (Read it: you need to see what is on screen at each point)")


if __name__ == "__main__":
    main()

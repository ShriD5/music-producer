# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "scipy", "soundfile", "soxr", "pyloudnorm", "librosa", "matplotlib"]
# ///
"""Measure a mix the way a mix engineer would listen to it, then draw it. You cannot hear: read the PNG.

  uv run analyze.py [audio/mix/mix.wav] [--root .] [--target -14] [--tp -1]

Uses audio/mix/stems/*.wav, audio/mix/render.json and audio/spot.json when present.
Writes audio/mix/report.md, analysis.json, analysis.png. Exit code 1 if a hard check fails.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

import numpy as np
import pyloudnorm as pyln
import soxr
from scipy.signal import butter, sosfiltfilt

import _common as C
import tonal

SR = C.SR


def ebur128(path):
    p = subprocess.run(["ffmpeg", "-nostats", "-v", "verbose", "-i", str(path), "-af", "ebur128=peak=true:framelog=verbose",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    t, M, S = [], [], []
    for m in re.finditer(r"t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+|-inf)\s+S:\s*(-?[\d.]+|-inf)", p):
        t.append(float(m.group(1)))
        M.append(float(m.group(2)) if m.group(2) != "-inf" else -120)
        S.append(float(m.group(3)) if m.group(3) != "-inf" else -120)
    summ = p[p.rfind("Summary:"):]
    get = lambda k: float(re.search(k + r":\s*(-?[\d.]+|-inf)", summ).group(1).replace("-inf", "-120"))
    return {"I": get("I"), "LRA": get("LRA"), "TP": get("Peak")}, np.array(t), np.array(M), np.array(S)


def band(x, lo=None, hi=None, order=4):
    if lo and hi:
        sos = butter(order, [lo, hi], "band", fs=SR, output="sos")
    elif lo:
        sos = butter(order, lo, "high", fs=SR, output="sos")
    else:
        sos = butter(order, hi, "low", fs=SR, output="sos")
    return sosfiltfilt(sos, x, axis=-1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mix", nargs="?")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", type=float)
    ap.add_argument("--tp", type=float)
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()
    adir = C.proj(root)
    mdir = adir / "mix"
    mix_path = pathlib.Path(a.mix) if a.mix else mdir / "mix.wav"
    x = C.load(mix_path)
    D = x.shape[-1] / SR
    render = json.loads((mdir / "render.json").read_text()) if (mdir / "render.json").exists() else {}
    spot = json.loads((adir / "spot.json").read_text()) if (adir / "spot.json").exists() else {}
    sess_path = adir / "session.json"
    sess = json.loads(sess_path.read_text()) if sess_path.exists() else {}
    target = a.target if a.target is not None else sess.get("master", {}).get("lufs", -14)
    tp_ceiling = a.tp if a.tp is not None else sess.get("master", {}).get("tp", -1.0)
    stems = {p.stem: C.load(p) for p in sorted((mdir / "stems").glob("*.wav"))} if (mdir / "stems").exists() else {}
    frame = spot.get("frame_s", 1 / 30)
    checks, notes = [], []

    def check(name, ok, detail, hard=False):
        checks.append({"check": name, "ok": bool(ok), "hard": hard, "detail": detail})

    # loudness (independent meter: ffmpeg)
    summ, t, M, S = ebur128(mix_path)
    check("integrated loudness", abs(summ["I"] - target) <= 0.5, f"{summ['I']:.1f} LUFS (target {target})", hard=True)
    check("true peak", summ["TP"] <= tp_ceiling + 0.1, f"{summ['TP']:.2f} dBTP (ceiling {tp_ceiling})", hard=True)
    check("loudness range", 3 <= summ["LRA"] <= 12,
          f"{summ['LRA']:.1f} LU (launch films live around 4-9; <3 = wall of sound, >12 = quiet bits get lost on phones)")
    clip = int((np.abs(x) >= 0.999).sum())
    check("no clipping", clip == 0, f"{clip} samples at full scale", hard=True)

    # VO intelligibility: speech-band level of VO vs everything else while someone talks
    vo = stems.get("vo")
    if vo is not None and np.any(vo):
        rest = sum(v for k, v in stems.items() if k not in ("vo",))
        ve, et = C.rms_env(band(vo, 300, 4000), win=0.4, hop=0.1)
        re_, _ = C.rms_env(band(rest, 300, 4000), win=0.4, hop=0.1) if np.any(rest) else (np.full_like(ve, -120), None)
        talk = ve > (ve.max() - 25)
        diff = (ve - re_)[talk]
        if len(diff):
            p10 = float(np.percentile(diff, 10))
            check("VO sits on top", p10 >= 8, f"speech band VO over bed: median {np.median(diff):.1f} dB, worst 10% "
                                              f"{p10:.1f} dB (want >= 8; >= 12 for dense music)")
            bad = et[talk][diff < 6]
            if len(bad):
                notes.append(f"VO masked (< 6 dB over bed) around: {', '.join(f'{v:.1f}s' for v in bad[::10][:8])}")

    # sync: did every peak-aligned hit actually land on its anchor, and is it on a picture event?
    placed = render.get("placed", [])
    sfx_stem = stems.get("sfx")
    events = sorted(set(spot.get("cuts", []) + spot.get("motion", []) + [m["t"] for m in spot.get("marks", [])]))
    sync_rows = []
    if sfx_stem is not None and placed:
        seen_a = set()
        for p in placed:  # one row per moment: layered hits are judged by their combined attack
            if p["bus"] != "sfx" or p["align"] not in ("peak", "attack") or round(p["anchor"], 3) in seen_a:
                continue
            seen_a.add(round(p["anchor"], 3))
            a0 = p["anchor"]
            w0 = max(0, a0 - 0.12)
            seg = sfx_stem[..., int(w0 * SR): int((a0 + 0.12) * SR)]
            if not seg.shape[-1]:
                continue
            env, et = C.rms_env(seg, win=0.003, hop=0.0005)
            # attack = the biggest energy rise near the anchor (robust to tails of earlier sounds still ringing)
            k = 30  # 15 ms look-back
            rise = np.array([env[i] - env[max(0, i - k):i + 1].min() for i in range(len(env))])
            near_a = np.abs(w0 + et - a0) <= 0.08
            layers = [q for q in placed if q["bus"] == "sfx" and abs(q["anchor"] - a0) < 1e-3]
            if any(q["align"] == "attack" for q in layers):
                got = w0 + float(et[np.argmax(np.where(near_a, rise, -1e9))])
            else:  # peak-aligned (whooshes): the loudest point near the anchor
                got = w0 + float(et[np.argmax(np.where(near_a, env, -1e9))])
            err = (got - a0) * 1000
            near = min(events, key=lambda e: abs(e - a0)) if events else None
            dist = (a0 - near) * 1000 if near is not None else None
            label = " + ".join(q["label"] for q in layers)
            sync_rows.append((label, a0, err, dist))
        moments = {round(m["anchor"], 3): m["err_ms"] for m in render.get("moments", [])}
        if moments:  # placement-verified timing beats stem detection (overlapping sounds fool the detector)
            sync_rows = [(l, a, moments.get(round(a, 3), e), d) for l, a, e, d in sync_rows]
        off = [r for r in sync_rows if abs(r[2]) > frame * 1000]
        check("hits land on their frame", not off,
              f"{len(sync_rows) - len(off)}/{len(sync_rows)} hit moments attack within 1 frame ({frame * 1000:.0f} ms)"
              + ("; off: " + ", ".join(f"{l}@{a:.2f}s {e:+.0f}ms" for l, a, e, _ in off) if off else ""))
        if events:
            stray = [r for r in sync_rows if r[3] is not None and abs(r[3]) > 1.5 * frame * 1000]
            if stray:
                notes.append("hits not on a cut/mark/motion peak (fine if they sit on an action the detector missed; check the contact sheet): "
                             + ", ".join(f"{l}@{a:.2f}s ({d:+.0f}ms from nearest event)" for l, a, _, d in stray[:10]))
        n_sfx = len([p for p in placed if p["bus"] == "sfx"])
        dens = 10 * n_sfx / D
        check("not over-scored", dens <= 7, f"{dens:.1f} SFX events per 10 s (more than ~7 reads as a toy; "
                                           "pick the moments that matter)")

    # phone speaker: does each big hit survive a 300 Hz high-pass?
    if sfx_stem is not None:
        hp = band(sfx_stem, 300, None)
        weak, seen = [], set()
        for p in placed:  # one verdict per moment: all layers on an anchor count together
            if p["bus"] != "sfx" or round(p["anchor"], 2) in seen:
                continue
            seen.add(round(p["anchor"], 2))
            s0 = int(p["anchor"] * SR) if p["align"] != "end" else int((p["anchor"] - 0.3) * SR)
            s0 = max(0, s0)
            seg, seghp = sfx_stem[..., s0:s0 + int(0.25 * SR)], hp[..., s0:s0 + int(0.25 * SR)]
            if seg.shape[-1] and np.sqrt(np.mean(seg ** 2)) > 1e-4:
                ratio = float(C.db(np.sqrt(np.mean(seghp ** 2)) / np.sqrt(np.mean(seg ** 2))))
                if ratio < -9:
                    weak.append(f"{p['label']}@{p['anchor']:.2f}s ({ratio:.0f} dB)")
        check("hits survive phone speakers", not weak,
              "all hits keep energy above 300 Hz" if not weak else
              "mostly sub, vanish on phones: " + ", ".join(weak[:8]) + " -> layer a mid transient (click/crack/thud 300 Hz-3 kHz)")

    # mono fold-down
    meter = pyln.Meter(SR)
    corr = float(np.corrcoef(x[0], x[1])[0, 1]) if np.std(x[0]) > 0 and np.std(x[1]) > 0 else 1.0
    mono_loss = meter.integrated_loudness(x.T) - meter.integrated_loudness(np.vstack([C.mono(x)] * 2).T)
    check("mono compatible", corr > 0.2 and mono_loss < 3, f"L/R correlation {corr:.2f}, mono fold loses {mono_loss:.1f} LU")

    # dead air + ending
    mid = (t > 0.6) & (t < D - 0.6)
    quiet = t[mid][M[mid] < -45]
    if len(quiet):
        runs, start, prev = [], quiet[0], quiet[0]
        for v in quiet[1:]:
            if v - prev > 0.15:
                runs.append((start, prev))
                start = v
            prev = v
        runs.append((start, prev))
        runs = [r for r in runs if r[1] - r[0] >= 0.35]
        if runs:
            notes.append("near-silence (intentional? a pre-reveal drop-out should be 0.2-1.0 s): "
                         + ", ".join(f"{s:.1f}-{e:.1f}s" for s, e in runs))
    tail = x[..., -int(0.05 * SR):]
    tail_db = float(C.db(np.sqrt(np.mean(tail ** 2)) + 1e-12))
    check("ending resolves", tail_db < -35, f"last 50 ms at {tail_db:.0f} dBFS (want a ring-out / button, not a chop)")
    head_db = float(C.db(np.sqrt(np.mean(x[..., :int(0.3 * SR)] ** 2)) + 1e-12))
    if head_db < -60:
        notes.append(f"first 300 ms is silent ({head_db:.0f} dBFS): on autoplay feeds sound should start on frame 1")

    # spectral balance
    spec_bands = [("sub <60", None, 60), ("low 60-250", 60, 250), ("lowmid 250-2k", 250, 2000),
                  ("presence 2-6k", 2000, 6000), ("air >6k", 6000, None)]
    mm = C.mono(x)
    energy = {n: float(np.mean(band(mm, lo, hi) ** 2)) for n, lo, hi in spec_bands}
    tot = sum(energy.values()) + 1e-12
    share = {k: round(100 * v / tot, 1) for k, v in energy.items()}
    ref_name = sess.get("master", {}).get("match") or "launch"
    ref = tonal.load_ref(ref_name)
    hz, dev = tonal.deviation(x, ref)
    groups = tonal.group_report(hz, dev)
    off = [(g, d) for g, d in groups if abs(d) > 3]
    check(f"tonal balance vs {ref_name} films", not off,
          " | ".join(f"{g} {d:+.1f}" for g, d in groups) + " dB outside the reference range"
          + ("; " + ", ".join(("missing " if d < 0 else "too much ") + g for g, d in off)
             + " (master.match fixes small gaps; missing sub needs a source: music bus `sub`, or sub layers on hits)"
             if off else ""))
    refl = ref.get("loudness", {}).get("integrated_lufs")
    if refl:
        notes.append(f"reference films master at {min(refl):.0f}..{max(refl):.0f} LUFS (median {np.median(refl):.1f}); "
                     f"this mix is {summ['I']:.1f}")

    # ---------- picture ----------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import librosa
    import librosa.display
    rows = 3 + (1 if stems else 0)
    fig, ax = plt.subplots(rows, 1, figsize=(16, 3.0 * rows), sharex=False, facecolor="#111")

    def deco(axx, title):
        axx.set_facecolor("#181818")
        axx.tick_params(colors="#ccc", labelsize=8)
        axx.set_title(title, color="w", fontsize=10, loc="left")
        axx.set_xlim(0, D)
        for c in spot.get("cuts", []):
            axx.axvline(c, color="#f55", lw=0.6, alpha=0.6)
        for m in spot.get("marks", []):
            axx.axvline(m["t"], color="#5f5", lw=1.0, alpha=0.8)
        for p in placed:
            if p["bus"] == "sfx":
                axx.axvline(p["anchor"], color="#fc3", lw=0.8, ls=":", alpha=0.9)

    i = 0
    ax[i].plot(t, M, color="#68f", lw=0.6, label="momentary")
    ax[i].plot(t, S, color="#fff", lw=1.2, label="short-term")
    ax[i].axhline(target, color="#5f5", lw=0.8, ls="--")
    ax[i].set_ylim(-50, max(-5, float(np.max(M)) + 2))
    deco(ax[i], f"loudness  I {summ['I']:.1f} LUFS  LRA {summ['LRA']:.1f}  TP {summ['TP']:.1f} dBTP"
                f"   (red cut / green mark / yellow sfx anchor)")
    ax[i].legend(loc="lower right", fontsize=7, facecolor="#222", labelcolor="w")
    i += 1
    if stems:
        colors = {"vo": "#fff", "music": "#6cf", "sfx": "#fc3", "amb": "#9c6", "room": "#c8f"}
        for k, v in stems.items():
            e, et = C.rms_env(v, win=0.2, hop=0.05)
            ax[i].plot(et, e, lw=1.0, label=k, color=colors.get(k))
        ax[i].set_ylim(-70, 0)
        deco(ax[i], "stems RMS dBFS (pre-master): VO should ride clearly above music where it speaks")
        ax[i].legend(loc="lower right", fontsize=7, facecolor="#222", labelcolor="w", ncol=5)
        i += 1
    y = librosa.resample(mm, orig_sr=SR, target_sr=22050)
    Sm = librosa.amplitude_to_db(librosa.feature.melspectrogram(y=y, sr=22050, n_mels=128, hop_length=256), ref=np.max)
    librosa.display.specshow(Sm, sr=22050, hop_length=256, x_axis="time", y_axis="mel", ax=ax[i], cmap="magma")
    deco(ax[i], "mel spectrogram (vertical stripes = hits, horizontal bands = sustained tones / ringing)")
    i += 1
    ax[i].bar(list(share), list(share.values()), color="#6cf")
    ax[i].set_facecolor("#181818")
    ax[i].tick_params(colors="#ccc", labelsize=8)
    ax[i].set_title("energy share by band (%)", color="w", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(mdir / "analysis.png", dpi=80, facecolor=fig.get_facecolor())

    hard_fail = [c for c in checks if not c["ok"] and c["hard"]]
    lines = [f"# Mix report: {mix_path.name} ({D:.2f}s)", ""]
    for c in checks:
        lines.append(f"- {'PASS' if c['ok'] else ('FAIL' if c['hard'] else 'WARN')}  {c['check']}: {c['detail']}")
    if sync_rows:
        lines += ["", "## Hits", "| label | anchor | transient err | from nearest cut/mark |", "|---|---|---|---|"]
        lines += [f"| {l} | {a:.3f}s | {e:+.0f} ms | {'' if d is None else f'{d:+.0f} ms'} |" for l, a, e, d in sync_rows]
    if notes:
        lines += ["", "## Notes"] + [f"- {n}" for n in notes]
    (mdir / "report.md").write_text("\n".join(lines) + "\n")
    (mdir / "analysis.json").write_text(json.dumps({"summary": summ, "checks": checks, "notes": notes,
                                                     "band_share": share}, indent=1))
    print("\n".join(lines))
    print(f"\n-> {mdir / 'analysis.png'} (Read it)")
    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    main()

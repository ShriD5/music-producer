# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["numpy", "scipy", "soundfile", "soxr", "pyloudnorm", "pedalboard"]
# ///
"""Render a mix session: buses -> stems -> shared room -> glue -> loudness + true-peak master -> (mux).

  uv run mix.py audio/session.json [--root .] [--mux] [--out audio/mix]

Session (all times in output seconds, gains in dB):
{
  "duration": 42.0,
  "video": "renders/video.mp4",
  "master": {"lufs": -13, "tp": -1.0, "glue": true, "match": "launch"},
  "room": {"size": 0.35, "damping": 0.55, "predelay_ms": 14, "hpf": 280, "lpf": 8500, "return_db": -4},
  "buses": {
    "vo":    {"preset": "vo"},
    "music": {"preset": "music", "gain_db": -3, "eq": [{"type": "peak", "hz": 3000, "db": -2, "q": 0.9}],
              "sub": {"octave_db": -8, "shelf_db": 2},
              "duck": {"by": "vo", "depth_db": 6, "mid_extra_db": 5, "attack": 0.06, "release": 0.5}},
    "sfx":   {"preset": "sfx", "send": 0.12},
    "amb":   {"preset": "amb", "gain_db": -12, "duck": {"by": "vo", "depth_db": 4}}
  },
  "clips": [
    {"bus": "music", "file": "audio/music/fit.wav", "at": 0},
    {"bus": "sfx", "file": "audio/sfx/logo-hit-2.wav", "at": 38.0, "align": "attack", "gain_db": -3,
     "pan": -0.6, "pan_to": 0.6, "width": 1.0, "pitch": -2, "hpf": 0, "lpf": 0, "reverse": false,
     "in": 0, "out": null, "fade_in": 0, "fade_out": 0.3, "send": 0.25, "label": "logo"}
  ],
  "automation": {"music": {"gain": [[0, -6], [4.7, -6], [4.95, -28], [5.0, 0]],
                           "lpf": [[0, 600], [4.9, 600], [5.0, 20000]]}}
}
align: start (default) | attack (the sound's arrival lands on `at`: clicks, impacts, sub drops, anything layered)
       | peak (its loudest moment lands on `at`: whooshes, swishes) | end (the file ends on `at`: risers, swells).
"""
import argparse
import json
import pathlib
import subprocess
import sys

import numpy as np
import pedalboard as pb
import pyloudnorm as pyln
import soxr
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, sosfilt, sosfiltfilt

import _common as C
import tonal

SR = C.SR


# ---------- dsp ----------
def eq_board(items):
    fx = []
    for e in items or []:
        t, hz = e["type"], e["hz"]
        if t == "hpf":
            fx += [pb.HighpassFilter(cutoff_frequency_hz=hz) for _ in range(e.get("order", 2))]
        elif t == "lpf":
            fx += [pb.LowpassFilter(cutoff_frequency_hz=hz) for _ in range(e.get("order", 2))]
        elif t == "peak":
            fx.append(pb.PeakFilter(cutoff_frequency_hz=hz, gain_db=e["db"], q=e.get("q", 1.0)))
        elif t == "lowshelf":
            fx.append(pb.LowShelfFilter(cutoff_frequency_hz=hz, gain_db=e["db"], q=e.get("q", 0.707)))
        elif t == "highshelf":
            fx.append(pb.HighShelfFilter(cutoff_frequency_hz=hz, gain_db=e["db"], q=e.get("q", 0.707)))
    return fx


def deess(x, lo=5200, hi=10000, thresh_db=-30, ratio=4.0):
    sos = butter(4, [lo, hi], "band", fs=SR, output="sos")
    s = sosfiltfilt(sos, x, axis=-1)
    env = np.sqrt(uniform_filter1d(C.mono(s) ** 2, int(0.004 * SR)))
    over = np.maximum(0, C.db(env) - thresh_db)
    g = C.undb(-over * (1 - 1 / ratio))
    return x - s + s * g


PRESETS = {
    # dialogue: rumble out, mud down, presence up, level it, tame esses
    "vo": lambda: [pb.HighpassFilter(80), pb.HighpassFilter(80), pb.PeakFilter(280, -2.5, 1.0),
                   pb.PeakFilter(3200, 2.0, 0.8), pb.HighShelfFilter(10000, 1.5),
                   pb.Compressor(threshold_db=-22, ratio=3.0, attack_ms=4, release_ms=90),
                   pb.Compressor(threshold_db=-10, ratio=6.0, attack_ms=1, release_ms=40)],
    # generated scores arrive mastered: only clean the sub and leave dynamics alone
    "music": lambda: [pb.HighpassFilter(28)],
    "sfx": lambda: [pb.HighpassFilter(30), pb.Compressor(threshold_db=-14, ratio=2.0, attack_ms=12, release_ms=120)],
    "amb": lambda: [pb.HighpassFilter(60), pb.HighpassFilter(60), pb.LowpassFilter(12000)],
    "none": lambda: [],
}


def varispeed(x, semis):
    if not semis:
        return x
    r = 2 ** (semis / 12)
    return soxr.resample(x.T, SR * r, SR, quality="VHQ").T.astype(np.float32)


def pan_stereo(x, pan, pan_to=None, width=1.0):
    if width != 1.0:
        m, s = (x[0] + x[1]) / 2, (x[0] - x[1]) / 2 * width
        x = np.vstack([m + s, m - s])
    n = x.shape[-1]
    p = np.full(n, float(pan)) if pan_to is None else np.linspace(pan, pan_to, n)
    th = (p + 1) * np.pi / 4
    return np.vstack([x[0] * np.cos(th) * np.sqrt(2), x[1] * np.sin(th) * np.sqrt(2)]).astype(np.float32)


def env_curve(points, n, default=0.0, log=False):
    if not points:
        return None
    pts = sorted(points)
    t = np.arange(n) / SR
    xs = [p[0] for p in pts]
    ys = [np.log(p[1]) if log else p[1] for p in pts]
    y = np.interp(t, xs, ys)
    return np.exp(y) if log else y


def lpf_automate(x, curve, block=256):
    f = pb.LowpassFilter(20000)
    out = np.zeros_like(x)
    for i in range(0, x.shape[-1], block):
        f.cutoff_frequency_hz = float(np.clip(curve[min(i + block // 2, len(curve) - 1)], 30, 20000))
        out[:, i:i + block] = f(x[:, i:i + block], SR, reset=False)
    return out


def hpf_automate(x, curve, block=256):
    f = pb.HighpassFilter(20)
    out = np.zeros_like(x)
    for i in range(0, x.shape[-1], block):
        f.cutoff_frequency_hz = float(np.clip(curve[min(i + block // 2, len(curve) - 1)], 20, 18000))
        out[:, i:i + block] = f(x[:, i:i + block], SR, reset=False)
    return out


def duck_gain(key, depth_db, thresh_db=-40, attack=0.06, release=0.5):
    """Smoothed 0..1 'someone is talking' mask from the key bus -> gain curve in dB."""
    env, t = C.rms_env(key, win=0.03, hop=0.005)
    active = (env > thresh_db).astype(float)
    a_up, a_dn = 1 - np.exp(-0.005 / attack), 1 - np.exp(-0.005 / release)
    s = np.zeros_like(active)
    v = 0.0
    for i, on in enumerate(active):
        v += (on - v) * (a_up if on > v else a_dn)
        s[i] = v
    n = key.shape[-1]
    return np.interp(np.arange(n) / SR, t, s) * -depth_db


def sub_enhance(x, octave_db=None, shelf_db=0.0):
    """Weight under a thin bed: an octave-down copy of the 40-110 Hz band (felt, not heard) plus a 50 Hz shelf."""
    y = x
    if octave_db is not None:
        band = sosfiltfilt(butter(4, [40, 110], "band", fs=SR, output="sos"), x, axis=-1).astype(np.float32)
        oct_ = pb.Pedalboard([pb.PitchShift(semitones=-12), pb.LowpassFilter(75), pb.LowpassFilter(75)])(band, SR)
        y = y + oct_[:, :x.shape[-1]] * C.undb(octave_db)
    if shelf_db:
        y = pb.Pedalboard([pb.LowShelfFilter(55, shelf_db, 0.7)])(y.astype(np.float32), SR)
    return y.astype(np.float32)


def split3(x, lo=250, hi=5000):
    low = sosfiltfilt(butter(4, lo, "low", fs=SR, output="sos"), x, axis=-1)
    high = sosfiltfilt(butter(4, hi, "high", fs=SR, output="sos"), x, axis=-1)
    return low, x - low - high, high


def true_peak_db(x):
    up = soxr.resample(x.T, SR, SR * 4).T
    return float(C.db(np.abs(up).max()))


def tp_limit(x, ceiling_db, look=0.004, release=0.06):
    up = np.abs(soxr.resample(x.T, SR, SR * 4).T).max(axis=0)
    n = x.shape[-1]
    up = np.pad(up, (0, max(0, 4 * n - len(up))))[:4 * n].reshape(n, 4).max(axis=1)
    ceil = C.undb(ceiling_db)
    g = np.minimum(1.0, ceil / np.maximum(up, 1e-9))
    L = max(2, int(look * SR)) // 2 * 2
    gmin = minimum_filter1d(g, size=L + 1, origin=-(L // 2), mode="nearest")
    a = 1 - np.exp(-1 / (release * SR))
    y = np.empty_like(gmin)
    v = 1.0
    for i in range(n):  # instant attack (already looked ahead), smooth release
        gi = gmin[i]
        v = gi if gi < v else v + (gi - v) * a
        y[i] = v
    y = uniform_filter1d(y, size=L + 1, origin=L // 2, mode="nearest")
    return (x * y).astype(np.float32), float(C.db(y.min())), y


# ---------- render ----------
def place_clip(c, n, root):
    x = C.load(root / c["file"])
    if c.get("in") or c.get("out"):
        x = x[..., int(c.get("in", 0) * SR): int(c["out"] * SR) if c.get("out") else None]
    if c.get("reverse"):
        x = x[..., ::-1].copy()
    x = varispeed(x, c.get("pitch", 0))
    fx = []
    if c.get("hpf"):
        fx += [pb.HighpassFilter(c["hpf"]) for _ in range(2)]
    if c.get("lpf"):
        fx += [pb.LowpassFilter(c["lpf"]) for _ in range(2)]
    fx += eq_board(c.get("eq"))
    if fx:
        x = pb.Pedalboard(fx)(x, SR)
    x = C.fade(x, c.get("fade_in", 0), c.get("fade_out", 0))
    x = x * C.undb(c.get("gain_db", 0))
    if "pan" in c or "pan_to" in c or "width" in c:
        x = pan_stereo(x, c.get("pan", 0), c.get("pan_to"), c.get("width", 1.0))
    align = c.get("align", "start")
    off = {"attack": lambda: C.attack_time(x), "peak": lambda: C.peak_time(x), "end": lambda: x.shape[-1] / SR}.get(
        align, lambda: 0.0)()
    start = c["at"] - off
    s = int(round(start * SR))
    if s < 0:
        x, s = x[..., -s:], 0
    return x, s, start, off


def moment_sync(layers):
    """Where each hit moment actually arrives, measured on the summed layers placed there (nothing else), with the
    same definition used to place them. Catches layers whose attacks smear apart."""
    out = []
    for (bus, anchor), items in layers.items():
        aligns = {a for _, _, a in items}
        if bus != "sfx" or not aligns & {"attack", "peak"}:
            continue
        s0 = min(s for s, _, _ in items)
        n = max(s + y.shape[-1] for s, y, _ in items) - s0
        buf = np.zeros((2, n), np.float32)
        for s, y, _ in items:
            buf[:, s - s0:s - s0 + y.shape[-1]] += y
        t = C.attack_time(buf) if "attack" in aligns else C.peak_time(buf)
        out.append({"anchor": anchor, "err_ms": round((s0 / SR + t - anchor) * 1000, 1), "layers": len(items)})
    return out


def render(sess, root, outdir, mux=False):
    D = float(sess["duration"])
    n = int(round(D * SR))
    buses_cfg = sess.get("buses", {})
    names = list(dict.fromkeys(list(buses_cfg) + [c["bus"] for c in sess["clips"]]))
    raw = {b: np.zeros((2, n), np.float32) for b in names}
    send = {b: np.zeros((2, n), np.float32) for b in names}
    placed, layers = [], {}
    for c in sess["clips"]:
        x, s, start, off = place_clip(c, n, root)
        e = min(n, s + x.shape[-1])
        if e <= s:
            continue
        raw[c["bus"]][:, s:e] += x[:, :e - s]
        snd = c.get("send", buses_cfg.get(c["bus"], {}).get("send", 0))
        if snd:
            send[c["bus"]][:, s:e] += x[:, :e - s] * snd
        placed.append({"bus": c["bus"], "file": c["file"], "label": c.get("label", pathlib.Path(c["file"]).stem),
                       "start": round(start, 4), "anchor": c["at"], "align": c.get("align", "start"),
                       "transient_offset": round(off, 4), "len": round(x.shape[-1] / SR, 3)})
        layers.setdefault((c["bus"], round(c["at"], 3)), []).append((s, x[:, :e - s], c.get("align", "start")))

    # bus processing (vo first: it keys the ducks)
    out = {}
    order = sorted(names, key=lambda b: 0 if b == "vo" else 1)
    for b in order:
        cfg = buses_cfg.get(b, {})
        x = raw[b]
        if not np.any(x):
            out[b] = x
            continue
        preset = cfg.get("preset", b if b in PRESETS else "none")
        x = pb.Pedalboard(PRESETS[preset]() + eq_board(cfg.get("eq")))(x, SR)
        if preset == "vo" or cfg.get("deess"):
            x = deess(x)
        if cfg.get("sub"):
            x = sub_enhance(x, cfg["sub"].get("octave_db"), cfg["sub"].get("shelf_db", 0.0))
        auto = sess.get("automation", {}).get(b, {})
        if isinstance(auto, list):
            auto = {"gain": auto}
        if auto.get("lpf"):
            x = lpf_automate(x, env_curve(auto["lpf"], n, log=True))
        if auto.get("hpf"):
            x = hpf_automate(x, env_curve(auto["hpf"], n, log=True))
        d = cfg.get("duck")
        if d and d.get("by") in out and np.any(out[d["by"]]):
            g = duck_gain(out[d["by"]], d.get("depth_db", 6), d.get("thresh_db", -40), d.get("attack", 0.06),
                          d.get("release", 0.5))
            if d.get("mid_extra_db"):  # carve the speech band harder than lows/highs
                lo, mid, hi = split3(x)
                gm = g * (1 + d["mid_extra_db"] / max(d.get("depth_db", 6), 0.1))
                x = (lo + hi) * C.undb(g) + mid * C.undb(gm)
            else:
                x = x * C.undb(g)
        if auto.get("gain"):
            x = x * C.undb(env_curve(auto["gain"], n))
        x = x * C.undb(cfg.get("gain_db", 0))
        out[b] = x.astype(np.float32)

    # shared room: everything that sends lives in the same space
    rc = {"size": 0.35, "damping": 0.55, "predelay_ms": 14, "hpf": 280, "lpf": 8500, "return_db": -4,
          **sess.get("room", {})}
    total_send = sum(send.values())
    room = np.zeros((2, n), np.float32)
    if np.any(total_send):
        board = pb.Pedalboard([pb.HighpassFilter(rc["hpf"]), pb.LowpassFilter(rc["lpf"]),
                               pb.Delay(delay_seconds=rc["predelay_ms"] / 1000, feedback=0, mix=1.0),
                               pb.Reverb(room_size=rc["size"], damping=rc["damping"], wet_level=1.0, dry_level=0.0,
                                         width=1.0)])
        room = board(total_send, SR)[:, :n] * C.undb(rc["return_db"])
        room = room.astype(np.float32)
        out["room"] = room

    stems_dir = outdir / "stems"
    for b, x in out.items():
        if np.any(x):
            C.save(stems_dir / f"{b}.wav", x, subtype="FLOAT")
    pre = sum(out.values())

    # master
    m = sess.get("master", {})
    target, tp = m.get("lufs", -14.0), m.get("tp", -1.0)
    meter = pyln.Meter(SR)
    x = pre * C.undb(-18 - meter.integrated_loudness(pre.T))  # stage to -18 LUFS before the glue
    if m.get("glue", True):
        x = pb.Pedalboard([pb.Compressor(threshold_db=-20, ratio=1.8, attack_ms=25, release_ms=180)])(x, SR)
    if m.get("tilt_db"):
        x = pb.Pedalboard([pb.HighShelfFilter(4500, m["tilt_db"]), pb.LowShelfFilter(120, -m["tilt_db"] / 2)])(x, SR)
    match_log = []
    if m.get("match"):  # pull bands that sit outside real launch films' range back into it
        x, match_log = tonal.match(x, tonal.load_ref(m["match"]), m.get("match_strength", 0.8), m.get("match_max_db", 6))
    gain = target - meter.integrated_loudness(x.T)
    for _ in range(4):
        y, gr, gcurve = tp_limit(x * C.undb(gain), tp - 0.15)
        got = meter.integrated_loudness(y.T)
        if abs(got - target) < 0.15:
            break
        gain += target - got
    y = C.fade(y, 0.0, 0.02)
    tpk = true_peak_db(y)
    C.save(outdir / "mix.wav", y)
    if match_log:
        print("  tonal match: " + ", ".join(f"{h:.0f}Hz {g:+.1f}" for h, g in match_log))
    rep = {"tonal_match": match_log, "lufs": round(got, 2), "true_peak_dbtp": round(tpk, 2), "limiter_max_gr_db": round(-gr, 2),
           "master_gain_db": round(gain, 2), "duration": D, "placed": placed}
    (outdir / "render.json").write_text(json.dumps(rep, indent=1))
    print(f"mix -> {outdir / 'mix.wav'}  {got:.2f} LUFS  {tpk:.2f} dBTP  limiter max GR {-gr:.1f} dB")
    grdb = -C.db(gcurve)
    hot = []  # where the limiter digs in, worst first, one entry per 0.5 s
    for i in np.argsort(-grdb[::480]) * 480:
        if grdb[i] < 2 or len(hot) == 6:
            break
        t = i / SR
        if all(abs(t - h[0]) > 0.5 for h in hot):
            near = [p["label"] for p in placed if p["start"] - 0.05 <= t <= p["start"] + p["len"]]
            hot.append((t, float(grdb[i]), near))
    rep["moments"] = moment_sync(layers)
    rep["limiter_hotspots"] = [{"t": round(t, 2), "gr_db": round(g, 1), "playing": n} for t, g, n in hot]
    (outdir / "render.json").write_text(json.dumps(rep, indent=1))
    if -gr > 4:
        print("  ! limiter is working > 4 dB: something is too loud before the master. Turn that clip down instead "
              "of squashing the whole mix. Hotspots:")
    if hot:
        for t, g, n in hot:
            print(f"    {t:6.2f}s  -{g:.1f} dB  playing: {', '.join(n)}")
    if mux:
        vid = root / sess["video"]
        dst = vid.with_name(vid.stem + ".sound.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(vid), "-i", str(outdir / "mix.wav"), "-map", "0:v:0",
                        "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                        "-t", f"{D:.3f}", "-movflags", "+faststart", str(dst)], check=True)
        print(f"muxed -> {dst}")
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    ap.add_argument("--mux", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()
    sess = json.loads(pathlib.Path(a.session).read_text())
    outdir = pathlib.Path(a.out) if a.out else C.proj(root) / "mix"
    outdir.mkdir(parents=True, exist_ok=True)
    missing = [c["file"] for c in sess["clips"] if not (root / c["file"]).exists()]
    if missing:
        sys.exit(f"missing files: {missing}")
    render(sess, root, outdir, a.mux)


if __name__ == "__main__":
    main()

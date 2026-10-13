"""Tonal balance vs. a reference curve (third octaves, loudness-matched), plus the matching EQ.

The reference (references/launch-reference.json) is the median and interquartile range of real launch films.
Matching only corrects bands that fall OUTSIDE the references' typical range, so a genre's own colour survives
while missing sub, boxy low-mids or harsh highs get pulled back into the window a launch film lives in.
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import pyloudnorm as pyln
from scipy.signal import fftconvolve, firwin2, welch

import _common as C

SR = C.SR
REF_DIR = pathlib.Path(__file__).resolve().parent.parent / "references"
GROUPS = [("sub", 25, 50), ("low", 63, 160), ("low-mid", 200, 500), ("mid", 630, 2000), ("presence", 2500, 5000),
          ("air", 6300, 16000)]


def load_ref(name: str = "launch") -> dict:
    p = pathlib.Path(name)
    if not p.exists():
        p = REF_DIR / f"{name}-reference.json"
    return json.loads(p.read_text())


def curve(x, centers) -> np.ndarray:
    """Band power (dB) per third octave after matching the signal to -14 LUFS."""
    m = C.mono(x)
    lufs = pyln.Meter(SR).integrated_loudness(np.atleast_2d(x).T if x.ndim == 2 else m)
    m = m * C.undb(-14 - lufs)
    f, p = welch(m, SR, nperseg=16384)
    out = []
    for c in centers:
        sel = (f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))
        out.append(10 * np.log10(p[sel].mean() * c * (2 ** (1 / 6) - 2 ** (-1 / 6)) + 1e-20))
    return np.array(out)


def deviation(x, ref: dict) -> tuple[np.ndarray, np.ndarray]:
    """dB outside the reference IQR per band (0 inside, + = too much, - = too little)."""
    hz = np.array(ref["hz"])
    ours = curve(x, hz)
    lo, hi = np.array(ref["p25_db"]), np.array(ref["p75_db"])
    dev = np.where(ours > hi, ours - hi, np.where(ours < lo, ours - lo, 0.0))
    return hz, dev


def group_report(hz, dev) -> list[tuple[str, float]]:
    out = []
    for name, a, b in GROUPS:
        sel = (hz >= a * 0.9) & (hz <= b * 1.1)
        if sel.any():
            out.append((name, float(np.mean(dev[sel]))))
    return out


def match(x, ref: dict, strength: float = 0.8, max_db: float = 6.0) -> tuple[np.ndarray, list]:
    """Linear-phase EQ that pulls out-of-range bands back toward the reference window."""
    hz, dev = deviation(x, ref)
    g = np.clip(-dev * strength, -max_db, max_db)
    g = np.convolve(np.pad(g, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")  # no single-band spikes
    freqs = np.concatenate([[0], hz, [SR / 2]])
    gains = np.concatenate([[g[0]], g, [g[-1]]])
    taps = firwin2(8191, freqs / (SR / 2), C.undb(gains))
    d = len(taps) // 2
    y = np.vstack([fftconvolve(ch, taps)[d:d + x.shape[-1]] for ch in x]).astype(np.float32)
    return y, [(float(h), float(v)) for h, v in zip(hz, g) if abs(v) >= 0.5]

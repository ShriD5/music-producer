"""Shared helpers for the sound-design scripts: audio IO, dB math, fal queue client, cost log."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

import numpy as np
import soundfile as sf

SR = 48000
SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent


# ---------- keys ----------
CONFIG_FILES = ["./.env", "~/.config/sound-design/keys.env"]


def key(name: str, required: bool = True) -> str | None:
    """Env var, then ./.env, then ~/.config/sound-design/keys.env. required=False returns None when unset."""
    if os.environ.get(name):
        return os.environ[name]
    for p in CONFIG_FILES:
        f = pathlib.Path(p).expanduser()
        if f.exists():
            for line in f.read_text().splitlines():
                line = line.strip().removeprefix("export ")
                if line.startswith(name + "="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    if not required:
        return None
    sys.exit(f"{name} not set (env var, ./.env or ~/.config/sound-design/keys.env). "
             "Run `uv run setup.py doctor` to see what each key unlocks.")


# ---------- audio ----------
def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-12))


def undb(d):
    return 10 ** (np.asarray(d, dtype=float) / 20)


def load(path, sr: int = SR, stereo: bool = True) -> np.ndarray:
    """Any file ffmpeg can read -> float32 (channels, samples) at `sr`."""
    path = str(path)
    try:
        x, fs = sf.read(path, always_2d=True, dtype="float32")
        x = x.T
    except Exception:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"],
            capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).T.copy()
        fs = sr
    if fs != sr:
        import soxr
        x = soxr.resample(x.T, fs, sr, quality="VHQ").T.astype(np.float32)
    if stereo and x.shape[0] == 1:
        x = np.vstack([x, x])
    if stereo and x.shape[0] > 2:
        x = x[:2]
    return np.ascontiguousarray(x, dtype=np.float32)


def save(path, x: np.ndarray, sr: int = SR, subtype: str = "PCM_24"):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.asarray(x).T, sr, subtype=subtype)
    return path


def mono(x):
    return x.mean(axis=0) if x.ndim == 2 else x


def rms_env(x, sr=SR, win=0.05, hop=0.01):
    """RMS envelope in dBFS, frame times."""
    m = mono(x)
    w, h = int(win * sr), int(hop * sr)
    if len(m) < w:
        return np.array([db(np.sqrt(np.mean(m ** 2)) + 1e-12)]), np.array([0.0])
    frames = np.lib.stride_tricks.sliding_window_view(m, w)[::h]
    r = np.sqrt((frames ** 2).mean(axis=1))
    return db(r), np.arange(len(r)) * hop + win / 2


def trim_silence(x, thresh_db=-60, keep_head=0.002, keep_tail=0.05, sr=SR):
    env, t = rms_env(x, sr, win=0.01, hop=0.002)
    on = np.where(env > thresh_db)[0]
    if not len(on):
        return x
    a = max(0, int((t[on[0]] - keep_head) * sr))
    b = min(x.shape[-1], int((t[on[-1]] + keep_tail) * sr))
    return x[..., a:b]


def peak_time(x, sr=SR) -> float:
    """Where the transient lands: first frame within 1 dB of the loudest 5 ms RMS."""
    env, t = rms_env(x, sr, win=0.005, hop=0.001)
    top = env.max()
    return float(t[np.argmax(env >= top - 1.0)])


def fade(x, fin=0.0, fout=0.0, sr=SR, shape="cos"):
    x = x.copy()
    n = x.shape[-1]
    for length, rev in ((fin, False), (fout, True)):
        k = min(n, int(length * sr))
        if k <= 1:
            continue
        r = np.linspace(0, 1, k)
        c = np.sin(r * np.pi / 2) ** 2 if shape == "cos" else r
        if rev:
            x[..., n - k:] *= c[::-1]
        else:
            x[..., :k] *= c
    return x


def duration(path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


# ---------- project paths + cost log ----------
def proj(root=".") -> pathlib.Path:
    p = pathlib.Path(root).resolve() / "audio"
    p.mkdir(parents=True, exist_ok=True)
    return p


def log_cost(root, endpoint, usd, note=""):
    f = proj(root) / "costs.jsonl"
    with f.open("a") as fh:
        fh.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "endpoint": endpoint,
                             "usd": round(usd, 4), "note": note}) + "\n")


def total_cost(root) -> float:
    f = proj(root) / "costs.jsonl"
    if not f.exists():
        return 0.0
    return sum(json.loads(l)["usd"] for l in f.read_text().splitlines() if l.strip())


# ---------- fal ----------
def _req(url, data=None, method=None, headers=None, timeout=120):
    h = {"Authorization": f"Key {key('FAL_KEY')}", "Content-Type": "application/json"}
    h.update(headers or {})
    body = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
    r = urllib.request.Request(url, data=body, method=method or ("POST" if data is not None else "GET"), headers=h)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else {}


def fal_upload(path) -> str:
    """Local file -> public fal CDN url (needed for video/audio inputs)."""
    path = pathlib.Path(path)
    ctype = {".mp4": "video/mp4", ".mov": "video/quicktime", ".wav": "audio/wav", ".mp3": "audio/mpeg",
             ".m4a": "audio/mp4", ".flac": "audio/flac", ".png": "image/png", ".jpg": "image/jpeg"}.get(
        path.suffix.lower(), "application/octet-stream")
    init = _req("https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3",
                {"content_type": ctype, "file_name": path.name})
    put = urllib.request.Request(init["upload_url"], data=path.read_bytes(), method="PUT",
                                 headers={"Content-Type": ctype})
    urllib.request.urlopen(put, timeout=300).read()
    return init["file_url"]


def fal_run(endpoint: str, payload: dict, timeout=900, quiet=False) -> dict:
    sub = _req(f"https://queue.fal.run/{endpoint}", payload)
    t0 = time.time()
    while True:
        st = _req(sub["status_url"])
        if st["status"] == "COMPLETED":
            break
        if time.time() - t0 > timeout:
            sys.exit(f"fal {endpoint} timed out after {timeout}s ({sub['request_id']})")
        time.sleep(2)
    try:
        res = _req(sub["response_url"])
    except urllib.error.HTTPError as e:
        sys.exit(f"fal {endpoint} failed: {e.code} {e.read().decode()[:800]}")
    if not quiet:
        print(f"  fal {endpoint} done in {time.time() - t0:.1f}s", file=sys.stderr)
    return res


def fal_audio_url(res: dict) -> str:
    for k in ("audio", "audio_file", "output", "audio_url"):
        v = res.get(k)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        if isinstance(v, str) and v.startswith("http"):
            return v
        if isinstance(v, list) and v and isinstance(v[0], dict) and v[0].get("url"):
            return v[0]["url"]
    for k in ("audios", "outputs", "tracks"):
        v = res.get(k)
        if isinstance(v, list) and v:
            return v[0]["url"] if isinstance(v[0], dict) else v[0]
    sys.exit(f"no audio url in fal response: {json.dumps(res)[:600]}")


def fal_audio_urls(res: dict) -> list[str]:
    for k in ("audios", "outputs", "tracks", "audio"):
        v = res.get(k)
        if isinstance(v, list) and v:
            return [i["url"] if isinstance(i, dict) else i for i in v]
    return [fal_audio_url(res)]


def download(url, dest) -> pathlib.Path:
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r:
        dest.write_bytes(r.read())
    return dest


def to_wav48(src, dest) -> pathlib.Path:
    """Normalize any provider output to 48 kHz stereo 24-bit WAV."""
    save(dest, load(src))
    return pathlib.Path(dest)

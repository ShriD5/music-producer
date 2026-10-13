# Master and delivery

`mix.py` masters every render: stage to -18 LUFS → glue compressor (1.8:1, 25 ms / 180 ms, ~1–2 dB) → optional tilt → gain to target → 4× oversampled lookahead true-peak limiter → iterate until within 0.15 LU. `analyze.py` re-measures independently with ffmpeg's EBU R128 meter.

## Targets (`session.master`)

| Destination | `lufs` | `tp` | Notes |
|---|---|---|---|
| Default: X, LinkedIn, website hero, YouTube | -14 | -1.0 | YouTube turns louder content down to ~-14, so going hotter only costs dynamics. |
| Feed-first IG Reels / TikTok / X autoplay where it competes with loud content | -12 to -11 | -1.0 | Common practice, not an official spec. Never hotter than -9. Expect more limiter GR; keep it < 4 dB. |
| Product Hunt / landing page (often quiet laptop) | -14 to -13 | -1.0 | |
| Podcast/audio-only | -16 | -1.0 | |
| Broadcast | -23 (EBU R128) / -24 (ATSC A/85) | -1 / -2 | Only if explicitly asked. |

Pick one in SOUND.md. If the film will be posted to several places, master for the loudest feed target and keep the -14 version as `mix.wav` from a second run (`--out audio/mix-14`).

## Hard QA (analyze.py fails the run)

- integrated loudness ±0.5 LU of target
- true peak ≤ ceiling (+0.1 tolerance for meter differences)
- zero samples at full scale

## Soft QA (warn, justify or fix)

- LRA 3–12 LU (launch films usually 4–9)
- every peak-aligned hit within 1 frame of its anchor
- VO ≥ 8 dB over the bed (speech band, worst 10 %)
- A-hits keep energy above 300 Hz
- mono fold-down loses < 3 LU, L/R correlation > 0.2
- last 50 ms below -35 dBFS (resolved ending); first 300 ms not silent
- band shares: sub < 35 %, presence > 2 %, air < 12 %
- ≤ 7 SFX events per 10 s

## Deliverables

- `renders/<name>.sound.mp4`: video stream copied untouched, AAC-LC 320 kb/s 48 kHz, `+faststart`, trimmed to the session duration.
- `audio/mix/mix.wav`: 48 kHz / 24-bit master.
- `audio/mix/stems/{vo,music,sfx,amb,room}.wav`: 32-bit float, pre-master, sum ≈ the mix before glue/limit. Hand these over if someone else will re-edit.
- `audio/mix/report.md` + `analysis.png`: the numbers you report to the user.

Vertical/cut-down versions: re-spot the new edit and re-run `mix.py` with a new session (different durations need a re-fit, not a trim of the master).

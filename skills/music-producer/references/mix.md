# Mix

`mix.py` renders `audio/session.json` → `audio/mix/stems/*.wav` (post-bus, pre-master), `mix.wav` (mastered), `render.json` (where every clip and transient landed). The schema is in the `mix.py` docstring. This file covers how to use it well.

## Bus recipes (built-in presets)

| bus | preset does | you add |
|---|---|---|
| `vo` | HPF 80 ×2, -2.5 dB @ 280 Hz (mud), +2 dB @ 3.2 kHz (presence), air shelf, 3:1 leveler + fast 6:1 peak catcher, split-band de-esser 5–10 kHz | nothing usually. Keys the ducks. |
| `music` | HPF 28 only (generated scores arrive mastered) | `duck` by vo with `mid_extra_db`, static `eq` carve (e.g. -2 dB @ 3 kHz, q 0.9) when VO is dense, `automation` |
| `sfx` | HPF 30, gentle 2:1 | `send` to the room (bus default), per-clip eq/pitch/pan |
| `amb` | HPF 60 ×2, LPF 12 kHz | `gain_db` -10 to -16, `duck` by vo 3–5 dB |
| `room` | shared reverb return (predelay → HPF → LPF → reverb) | `room.size` 0.2 (tight UI world) to 0.6 (cinematic), `return_db` |

## Level targets (relative, before master)

- VO speech band ≥ 10 dB over everything else while talking (analyze checks ≥ 8 dB at worst-10 %).
- Music with no VO: it **is** the mix. Bus around 0 dB.
- Music under VO: `depth_db` 5–8 and `mid_extra_db` 4–6 → the 250 Hz–5 kHz band drops 10–14 dB while the groove (lows) and air (highs) stay. Attack 40–80 ms, release 400–700 ms (faster release reads as pumping).
- A-hits: short-term peak 3–6 dB above the bed at that moment. If the limiter reports > 4 dB of gain reduction, a hit or the drop is too hot. Lower that clip, not the master.
- C-ticks: 8–12 dB under the bed; `lpf` them (~6 kHz) so they sit behind.
- Ambience/foley: felt, not heard, -20 to -30 dB under the VO.

## Automation moves (per bus, `automation.<bus>.gain / lpf / hpf`, breakpoints `[t, value]`)

- **Air before the reveal:** music gain `[[t-0.6, 0], [t-0.45, -30], [t-0.02, -30], [t, 0]]`. Pair with the swell ending at `t`.
- **Underwater pre-drop:** music lpf `[[0, 20000], [t-2, 20000], [t-1.9, 500], [t-0.02, 900], [t, 20000]]`, then everything opens on the reveal.
- **Radio/phone voice for the "old way":** music or sfx hpf to 400 + lpf to 3500 over a section, then open up.
- **Button:** music gain flat into the logo frame (the fitted ending does the work). Never dip the button.
- **Make room for an A-hit in a busy score:** gain `[[t-0.05, 0], [t, -3], [t+0.35, 0]]`.
- Ramps of 20–50 ms sound like edits, 150–600 ms like mixing. Choose deliberately.

## Space and movement

- Everything that should feel physical sends to the room (`send` 0.08–0.35). The A-hit tail sends most, the transient least.
- Moving objects: `pan` → `pan_to` across the clip (e.g. -0.7 → 0.7 for a left-to-right slide). Keep A-hit transients centered so they survive mono.
- `width` > 1 on beds/tails (1.2–1.5) for size, < 1 on hits for focus. analyze's mono check catches overdoing it.

## Iteration loop (do at least two passes)

1. Render → `analyze.py` → Read `analysis.png`.
2. Read the PNG like this:
   - **Loudness lane:** short-term (white) should rise into the reveal, dip in breakdowns, and land the button. A flat white line is a wall of sound: add automation. Spikes far above the white line are hot hits.
   - **Stems lane:** VO (white) clearly above music (blue) wherever VO exists. SFX (yellow) peaks on the dotted anchors and on red/green lines, not floating.
   - **Spectrogram:** vertical stripes should line up with cuts. Long horizontal bright lines that cross section changes mean a tonal clash or ringing. Check the key of the SFX.
   - **Band share:** sub > 35 % = boomy on headphones and empty on phones; presence < 2 % = dull; air > 12 % = harsh.
3. Fix with the smallest move (clip gain → clip eq → bus eq → automation → swap take → regenerate), re-render, re-analyze.
4. Mux and run `listen.py` once the measurements pass.

## Common fixes

| Symptom (report / PNG / ears) | Fix |
|---|---|
| "VO masked around 12.3 s" | raise `mid_extra_db`, or an automation dip there, or a static music eq -2 dB @ 2.5–3.5 kHz |
| limiter GR > 4 dB | find the spike in the loudness lane, lower that clip 2–4 dB |
| hit "off by +40 ms" | the take has a pre-transient (breath/swell): set `align: peak` or trim with `in` |
| hit vanishes on phones | add a transient layer with 1–4 kHz content, or `eq` +3 dB @ 2 kHz on the hit |
| LRA < 3 | not enough dynamics: automate breakdowns down 3–6 dB, add the air moment |
| LRA > 12 | intro or a breakdown is too quiet; raise it or shorten it |
| mono loss > 3 LU | reduce `width` on beds, or a phasey generated pad: swap the take |
| ending chop | use `music.py fit --end-hit`, or extend and let it ring out |
| sounds pasted on | send hits to the room, match pitch to the key, lpf/hpf each layer into its band |

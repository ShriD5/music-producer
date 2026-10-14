# Linear "Issue tracking is dead": sound

Concept: a cold, precise trailer pulse that multiplies with the issue glyphs until the grid whites out, holds its breath, then one decisive keystroke-and-boom kills the wall and the logo settles on a single clean in-key ping: issue tracking dies on a downbeat.
Sub-genre/texture: dark cinematic electronic / trailer, minimal and dry (mutation: no strings, no choir, no big drum kit; the "orchestra" is a pulsing analog sub ostinato and tiny digital ticks, so it reads as Linear-precise rather than Hollywood-epic)
Tempo: 105 BPM (bar 5 downbeat = 9.14 s, next to the 9.10 s wall break)   Key/mode: D minor (requested; tonal SFX get tuned to the analyzed key)   Lead sound: 16th-note pulsing analog sub-bass ostinato, sidechained
Product palette: Linear is keyboard-first and the picture is an LED dot-matrix grid. The palette is a mechanical key-switch click (the transient of the hit and of the signature), tiny pixel "dot lighting" ticks (C-ticks on the first glyphs, hi-hat-like), and a granular digital swarm (the riser while the grid floods). All designed and processed, nothing literal.
Refs (feel, not copy): Trent Reznor & Atticus Ross, "In Motion" (The Social Network); Ben Salisbury & Geoff Barrow, Ex Machina score (cold pulse, restraint)
Signature sound: one dry mechanical key-switch click fused to a glassy sine ping (tonic, then fifth, 2 notes) with a soft sub bloom, pitched to the analyzed tonic, plays at 9.70 s when the logo is fully resolved (setup: the first pixel tick at 0.0 s is the same click, tiny and filtered)
Banned this film: strings/choir/braams, big live drum kits, any whoosh (no camera move exists), literal glass shatter, cartoon foley, pads fading in, music fading out over the logo, more than one riser, anything vocal.

Gate vs ledger (last 3: eclipse-rescore-test chamber pop 120 D major pizzicato/music-box; road-to-1k sine blips; raptor-anatomy rocket rumble): differs on genre, tempo band (105 vs 120), key/mode (D minor vs D major), lead (sub ostinato vs pizzicato) and signature (key-switch + sine ping vs music-box tine). 5 of 5.

## Picture (from spot.png + per-frame luma)
- 0.0–2.0: black LED dot grid, single issue-icon glyphs blink on, sparse.
- 2.0–7.0: glyphs accumulate, slow density rise.
- 7.0–8.2: accelerating multiplication.
- 8.2–8.85: flood, the grid fills to white-out (luma 37 -> 71 in 0.65 s).
- 8.85–9.10: full white-out hold (frozen wall of lit dots).
- 9.10–9.70: wall breaks and collapses inward; the Linear logo emerges from the debris (legible ~9.45).
- 9.70–11.33: logo alone, clean, holds 1.6 s.
No cuts. spot.py tempo candidates come only from my 5 marks (fit 0.59, 3/5), so the edit is not rhythmic: hit the A-moment with a section boundary instead.

## Music map
| out time | section | energy (1-5) | what happens musically | why (picture) |
|---|---|---|---|---|
| 0.00–4.00 | Pulse (hook) | 3 | starts on beat 1: sub ostinato + low pulse hit, tiny ticks, no fade-in | first glyph on frame 1, autoplay hook |
| 4.00–9.10 | Build | 3 -> 5 | metallic percussion joins, pulse doubles, granular riser climbs; last ~0.25 s is air (automation) | glyphs multiply, flood, white-out |
| 8.85–9.10 | (air, automation) | 1 | music gain -30 dB, held breath | frozen white-out |
| 9.10–11.33 (plan to 12.2) | Hit + ring | 5 -> 1 | one massive unison hit on beat 1, then only the sub and the tail ring; no more drums | wall breaks -> logo |
Music ends as a ring-out of the 9.10 hit under the logo; fit trims at 11.33 with a short tail fade, never a fade of a still-playing loop.

## Hit list
| t | tier | moment | sound idea (layers incl. sub) | align |
|---|---|---|---|---|
| 0.00 | B | hook: first glyph | low dark digital thump + key-switch click, short | attack |
| 0.50, 1.95, 3.40 | C | single glyphs lighting | tiny pixel tick, round-robin, lpf, -10 dB under bed | attack |
| 7.20–8.85 | swell | flood to white-out | granular digital swarm riser, ends dead at 8.85 | end |
| 9.10 | A | wall breaks (the kill) | transient: hard mechanical key-switch slam + digital crack; body: deep cinematic boom; sub: sfx.py sub drop on tonic; score hits beat 1 with it | attack |
| 9.70 | A- (button) | logo resolved | signature: key-switch click + glassy 2-note sine ping (tonic -> fifth) + room tail | attack |

## Mix intent
Master -13 LUFS integrated, -1 dBTP, match "launch". Music carries everything; no VO. Short-term loudness climbs from ~-15 at the hook to the white-out, drops to near silence for 0.25 s (8.85–9.10), slams at 9.10 (the loudest moment), then decays under the logo with the signature on top. Underwater pre-drop: music lpf closes from 8.2 so the flood sounds like pressure building, opens on the hit. The ending is the ring of the hit + signature tail, landing below -35 dBFS by the last frame.

## As built (after measurement)
- Score: ElevenLabs Music v2.5 take `score-1` (seed 1000), fitted to 11.333 s (`audio/music/fit.wav`, 0.2 s tail fade on a ring already at -47 dB). Analyzed 103 BPM, **C# minor** (asked 105 / D minor). Picked over `score-2` because score-2 opens with 0.5 s of digital silence (kills the hook) and never hits at 9.1 (stays full to 10.0); score-1 starts on beat 1, builds, swells on 9.02-9.15 and rings out naturally.
- Hit list as mixed: hook 0.00 (hook-3, -0.53 st); flood riser swarm-1 ending 8.85; air 8.86-9.08 (music -40 dB, lpf closing to 2.5 kHz from 8.2); A-hit 9.10 = hit-trans-1 (key-slam crack, hpf 200) + hit-mid-2 (gritty low-mid body, +3 dB @ 300 Hz) + sfx.py sub C#1 drop; signature 9.70 = signature-1 pitched -5.99 st (C#5) then +0.99 st (G#5) at 9.986, room send 0.3-0.35.
- Cut in the mix passes: the three C-ticks (inaudible under the score's own ticks, and pushed density over 7/10 s) and the separate signature click (signature-1's own attack does it). The 9.10 boom layer was swapped for a low-mid body because the all-sub booms added limiter peaks but no loudness.
- Music automation: intro -3.5 dB, build -3 to -4 dB, air, -3 dB under the hit transient ramping to 0 by 9.5 s.
- Listen for: the 0.22 s air before the hit (does it read as a held breath, not a glitch?), whether the 9.10 hit feels decisive enough on laptop speakers, and whether the C#-G# signature sits in tune with the score's tail.

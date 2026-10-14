# Mix report: mix.wav (11.33s)

- PASS  integrated loudness: -13.1 LUFS (target -13)
- PASS  true peak: -1.50 dBTP (ceiling -1.0)
- PASS  loudness range: 3.6 LU (launch films live around 4-9; <3 = wall of sound, >12 = quiet bits get lost on phones)
- PASS  no clipping: 0 samples at full scale
- PASS  hits land on their frame: 4/4 hit moments attack within 1 frame (17 ms)
- PASS  not over-scored: 4.4 sound moments per 10 s, layers counted once (more than ~7 reads as a toy; pick the moments that matter)
- PASS  hits survive phone speakers: all hits keep energy above 300 Hz
- PASS  mono compatible: L/R correlation 0.77, mono fold loses 0.8 LU
- PASS  ending resolves: last 50 ms at -59 dBFS (want a ring-out / button, not a chop)
- PASS  limiter not squashing: max 3.9 dB gain reduction
- PASS  tonal balance vs launch films: sub in range | low 0.6 dB above | low-mid 0.2 dB below | mid 0.1 dB above | presence 0.3 dB above | air 1.3 dB above the reference range

## Hits
| label | anchor | transient err | from nearest cut/mark |
|---|---|---|---|
| hook | 0.000s | +2 ms | +0 ms |
| A wall break transient + A wall break body + A wall break sub | 9.100s | +1 ms | +0 ms |
| signature tonic C# | 9.700s | +0 ms | +0 ms |
| signature fifth G# | 9.986s | -0 ms | +286 ms |

## Notes
- hits not on a cut/mark/motion peak (fine if they sit on an action the detector missed; check the contact sheet): signature fifth G#@9.99s (+286ms from nearest event)
- reference films master at -17..-10 LUFS (median -13.6); this mix is -13.1

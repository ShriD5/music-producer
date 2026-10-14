# Mix report: mix.wav (24.93s)

- PASS  integrated loudness: -13.0 LUFS (target -13)
- PASS  true peak: -1.50 dBTP (ceiling -1.0)
- PASS  loudness range: 6.7 LU (launch films live around 4-9; <3 = wall of sound, >12 = quiet bits get lost on phones)
- PASS  no clipping: 0 samples at full scale
- PASS  hits land on their frame: 10/10 hit moments attack within 1 frame (33 ms)
- PASS  not over-scored: 4.0 sound moments per 10 s, layers counted once (more than ~7 reads as a toy; pick the moments that matter)
- PASS  hits survive phone speakers: all hits keep energy above 300 Hz
- PASS  mono compatible: L/R correlation 0.66, mono fold loses 1.1 LU
- PASS  ending resolves: last 50 ms at -59 dBFS (want a ring-out / button, not a chop)
- PASS  limiter not squashing: max 4.0 dB gain reduction
- PASS  tonal balance vs launch films: sub 0.3 dB above | low 0.2 dB above | low-mid 2.0 dB above | mid 1.1 dB below | presence in range | air 2.1 dB above the reference range

## Hits
| label | anchor | transient err | from nearest cut/mark |
|---|---|---|---|
| push-in | 1.150s | +0 ms | +20 ms |
| tooltip chime (setup) | 2.433s | +0 ms | +0 ms |
| edit tick | 4.467s | +0 ms | +0 ms |
| pull-back | 5.700s | +0 ms | -33 ms |
| map lift | 10.400s | +0 ms | -900 ms |
| drop snap + drop body + drop sub | 11.300s | +0 ms | +0 ms |
| tab 1 | 21.133s | +0 ms | +0 ms |
| tab 2 | 23.200s | +0 ms | +0 ms |
| button snap + button body + button sub + signature chime | 23.700s | +6 ms | +0 ms |
| bird's-eye pull-back | 23.850s | +0 ms | +117 ms |

## Notes
- hits not on a cut/mark/motion peak (fine if they sit on an action the detector missed; check the contact sheet): map lift@10.40s (-900ms from nearest event), bird's-eye pull-back@23.85s (+117ms from nearest event)
- reference films master at -17..-10 LUFS (median -13.6); this mix is -13.0

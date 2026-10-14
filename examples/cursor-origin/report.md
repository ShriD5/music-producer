# Mix report: mix.wav (30.90s)

- PASS  integrated loudness: -13.0 LUFS (target -13)
- PASS  true peak: -1.50 dBTP (ceiling -1.0)
- PASS  loudness range: 3.7 LU (launch films live around 4-9; <3 = wall of sound, >12 = quiet bits get lost on phones)
- PASS  no clipping: 0 samples at full scale
- PASS  hits land on their frame: 12/12 hit moments attack within 1 frame (33 ms)
- PASS  not over-scored: 3.9 sound moments per 10 s, layers counted once (more than ~7 reads as a toy; pick the moments that matter)
- PASS  hits survive phone speakers: all hits keep energy above 300 Hz
- PASS  mono compatible: L/R correlation 0.88, mono fold loses 0.4 LU
- PASS  ending resolves: last 50 ms at -142 dBFS (want a ring-out / button, not a chop)
- PASS  limiter not squashing: max 2.3 dB gain reduction
- PASS  tonal balance vs launch films: sub 1.3 dB above | low in range | low-mid 0.2 dB below | mid 1.1 dB above | presence 1.8 dB above | air 1.7 dB above the reference range

## Hits
| label | anchor | transient err | from nearest cut/mark |
|---|---|---|---|
| introducing glitch | 0.400s | +0 ms | +0 ms |
| zoom +New | 6.370s | +0 ms | +0 ms |
| type 1 | 7.100s | +0 ms | +167 ms |
| type 2 | 7.420s | +0 ms | +487 ms |
| type 3 | 7.780s | +0 ms | -820 ms |
| create repo click | 8.600s | +0 ms | +0 ms |
| sync click | 11.000s | +0 ms | +0 ms |
| ask cursor | 16.800s | +0 ms | +0 ms |
| merge branch A (D) | 20.200s | +0 ms | +0 ms |
| merge branch B (G) | 20.270s | +0 ms | +70 ms |
| drop impact + drop body + drop sub | 20.833s | +0 ms | +0 ms |
| logo impact + logo sub + signature G + signature D | 27.900s | +0 ms | +0 ms |

## Notes
- hits not on a cut/mark/motion peak (fine if they sit on an action the detector missed; check the contact sheet): type 1@7.10s (+167ms from nearest event), type 2@7.42s (+487ms from nearest event), type 3@7.78s (-820ms from nearest event), merge branch B (G)@20.27s (+70ms from nearest event)
- reference films master at -17..-10 LUFS (median -13.6); this mix is -13.0

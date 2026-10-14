# Notion Dashboards: sound

Concept: a felt-piano close-up that pulls back into a wide, confident neo-classical electronic groove, the way the film pulls from one menu item out to the bird's-eye view; every widget that lands in the grid is a soft felt-hammer "block snap".
Sub-genre/texture: neo-classical + electronic (felt piano, string quartet, glitchy micro-edited beat, sub swells), black-and-white minimal, dry and close, then wide.   Tempo: 116 BPM (spot.py candidate, fit 0.79; 21.13 / 23.2 are exactly one bar apart; mutated up from the 80-110 band to fit the cut)   Key/mode: requested F# minor (tune all tonal SFX to the analyzed key)   Lead sound: felt piano
Product palette: Notion's world is paper, ink and blocks on a grid. Felt-piano hammer thunks and paper-card flicks, processed into the glitch percussion, the widget drop and the signature. No literal office foley.
Refs (feel, not copy): Kiasmos (Blurred), Olafur Arnalds (re:member); Notion Calendar launch film for loudness/density.
Signature sound: "block snap + bird's-eye chime": felt-hammer snap + soft paper flick, over a sub drop, with a 3-note rising felt-piano / glass chime outlining the tonic triad (pitched to the analyzed tonic). Payoff at 23.7 s (the bird's-eye pull-back); setup in miniature at 2.433 s (the "Dashboard" tooltip appears).
Banned this film: cinematic whoosh on cuts without motion, typing/mouse-click foley, supersaw EDM, trap hats, pizzicato/celesta comedy, choir, any stock riser.

Ledger check (last 3 by date: eclipse-rescore-test 120 D major chamber pop/pizzicato, road-to-1k sine blips, raptor-anatomy rumble): differs on genre (neo-classical electronic), key/mode (F# minor), lead (felt piano), signature (block snap + chime). Tempo 116 is within 15 of 120 (eclipse-rescore); 4 of 5 differ, gate passes.

## Picture (from spot.png + extra frames)
0-1.1 wide window, Company Dashboard. 1.13 fast push-in to the "Start from scratch" view menu. 2.433 "Dashboard" tooltip appears. 3.67 menu closes. 4.467 Edit -> Done (edit mode). 5.67 fast pull-back to the whole canvas. 6-10 resizing widgets. 10.4 map widget lifted, dragged; 11.3 it drops into the top row. 11.3-18.5 scroll and resize around the board (12.97 / 13.5 / 14.4 / 15.2 are scroll jumps, continuity). 18.53 back to the top. 21.133 tab: Department hiring. 23.2 tab: Work progress. 23.7-24.0 pull-back to the whole window (bird's-eye). Hold to 24.93. No logo card: the final pull-back is the button.

## Music map
| out time | section | energy (1-5) | what happens musically | why (picture) |
|---|---|---|---|---|
| 0-5.7 | Clarity | 2 | solo felt piano motif from frame 1, soft sub swell | single-menu close-up, choosing a view |
| 5.7-11.3 | Unfold | 3 | strings + glitch fragments creep in, sub rises; air 10.85-11.28 (filter down + dip) | pull-back to canvas, arranging widgets, map lifted |
| 11.3-18.5 | Confident | 4 | full glitch beat + sub on beat 1, piano/strings unison | map lands: the dashboard is built |
| 18.5-23.7 | Lift | 4-5 | strings climb, motif up an octave | back to top, tab switches on the bar |
| 23.7-24.93 | Button | 5 -> ring | final unison hit, ring-out | bird's-eye pull-back |

## Hit list
| t | tier | moment | sound idea (layers incl. sub) | align |
|---|---|---|---|---|
| 1.13 | B | push-in | short soft air/paper swish, 0.4 s, center -> slight right | peak |
| 2.433 | B | "Dashboard" tooltip | signature in miniature: one soft glass/felt tine, quiet | attack |
| 4.467 | C | Edit -> Done | tiny felt tick, low, lpf | attack |
| 5.667 | B | pull-back to canvas | reverse-air swish, 0.35 s | peak |
| 10.4 | C | map lifted | soft paper lift tick | attack |
| 11.3 | A | map drops in (the drop) | swell ending on the frame + block-snap transient + felt body + sub drop; music enters on the frame | end / attack |
| 21.133 | B | tab Department hiring | short glitch stutter + paper flick | attack |
| 23.2 | B | tab Work progress | same, round-robin variant, pitched | attack |
| 23.7 | A | bird's-eye pull-back | wide air pull-back swish (23.7-24.1) + block snap + sub + 3-note chime (signature) on the music's final hit | attack / peak |

Two A-hits in 25 s; every scroll jump gets no sound.

## Mix intent
-13 LUFS integrated, -1 dBTP, master.match "launch". Music is the mix (no VO). Air before the 11.3 drop: music gain + lpf dip 10.85-11.28, swell ends on 11.3. Final hit spliced on 23.7 with the signature on top; ring-out to 24.93, no fade of a running loop. One room (size ~0.3, tight UI world), A-hit tails send most.

## As built (2026-10-14)
- Score: ElevenLabs Music v2.5 (fal), take score-1 (seed 1000) of 2. Neither take honoured the plan's boundaries: take 1 put its strings+beat entrance at 8.85 s (plan 11.3), take 2 opened with 1.75 s of silence and had no step at 11.3. A 3rd take with a revised plan (plan.json; v1 kept as plan-v1.json) could not be generated: fal account locked (TOP_UP) and the direct ElevenLabs key is on a free plan (Music API 402).
- Conform: `music.py fit score-1.wav --hit 11.3 --src 8.847 --end-hit 23.7 --end-src 23.336 --fout 0.8` (shift +2.453 s; the take's 21.246 downbeat lands on 23.70 anyway, so the button splice is bar-aligned). The 2.45 s of silence this leaves at the head is covered in the session by the same take started 2 bars later (in 1.68 s), crossfaded into the fit at 4.4-4.8 s (intro bars correlate 0.96-0.99 in chroma).
- Analyzed: 115.9 BPM, F# major (asked F# minor). Chime pitched +6 st (setup, 2.433) and -6 st (payoff, 23.7) so its root lands on F#.
- Actual music map: Clarity 0-11.3 (felt piano motif, strings creep in), air 10.85-11.26 (gain -12..-16 dB + lpf 700 Hz), drop 11.3 (+13.5 dB entrance), lift 19.57 (+13.8 dB; plan said 18.5), final hit 23.70, ring + 0.8 s fade to 24.93.
- Listen for: the 4.4-4.8 s intro crossfade (bar-aligned, same motif) and the 23.70 button splice (masked by the snap/body/sub/chime stack).

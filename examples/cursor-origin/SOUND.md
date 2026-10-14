# Cursor Origin: sound

Concept: Git hosting as a glitch record. A tight IDM / minimal tech-house track whose percussion is micro-edited keyboard clicks and commit "ticks", and whose signature is two branches (two glassy pings a fifth apart) merging into one chord at the logo.
Sub-genre/texture: glitch IDM over a minimal tech-house chassis: dry punchy kick, rolling clean sub, bitcrushed stutter edits, glassy FM plucks, no pads wash
Tempo: 136 bpm (20.833 drop -> 27.9 logo = exactly 4 bars)   Key/mode: E minor (requested; tonal SFX tuned to the analyzed key)   Lead sound: glassy FM pluck riff, chopped and stuttered
Product palette: mechanical key presses (hats and C-ticks), UI button clicks (rim/snare ghost), "pull/sync" data streams (reverse glitch swells), a merge (two pitched pings converging into one chord). All processed: pitched, bitcrushed, sent into one tight room.
Refs (feel, not copy): Jon Hopkins "Open Eye Signal" (precise minimal pulse), Rival Consoles / Apparat micro-edited percussion; Raycast launch films for loudness and density
Signature sound: "the merge": glassy FM ping root + fifth, played as two separate branch pings at the Squash & Merge click (20.2 s setup), then root + fifth + octave as one chord stab with sub and impact on the ORIGIN logo (27.9 s), pitched to the analyzed tonic.
Banned this film: supersaws, EDM build/drop clichés, orchestral hits, piano/strings, cinematic "braam", stock whooshes on cuts without motion, cartoon foley, vocals, the 120 bpm band of the last films, F minor / D major.

Ledger check (last 3: road-to-1k sine blips, raptor rumble, eclipse-rescore chamber pop 120 D major; eclipse-launch-v2 120 F minor EDM): differs on genre (glitch IDM / minimal), tempo (136 vs 120, 16 bpm), key (E minor), lead (FM pluck vs supersaw/pizzicato/sine), signature (merge pings vs stabs/tine/igniter). 5 of 5.

Tempo-to-picture: spot.py best candidate with marks is 160 bpm at fit 0.43 (< 0.5, edit is not rhythmic). Scored by section boundaries instead; 136 picked so the drop and logo are one 4-bar phrase apart.

## Music map
| out time | section | energy (1-5) | what happens musically | why (picture) |
|---|---|---|---|---|
| 0.00-3.93 | Hook | 3 | starts on frame 1: stuttered key-click percussion, sub pulse, filtered FM pluck motif | UI shot, "Introducing Code Hosting" at 0.4 |
| 3.93-9.83 | Build | 3 | dry kick enters four-on-floor, rolling sub, hats from key clicks | kinetic type "Create a repo...", zoom into +New, typing, Create Repo |
| 9.83-13.57 | Lift | 4 | add offbeat pluck chops, hats open up | "Or / Sync from GitHub", dashboard fills |
| 13.57-17.83 | Groove | 4 | full minimal groove, glitch fills every 2 bars | Review & Merge PRs, code diff, Ask Cursor menu |
| 17.83-20.83 | Stutter break | 2 | kick drops, stutter-gated pluck, filter closing, short air 20.45-20.83 | Ready to Merge, Squash & Merge click 20.2 |
| 20.83-24.90 | Drop | 5 | full drop on beat 1: heaviest kick + sub, bitcrushed lead | hard cut to black: Run CI from Buildkite/Depot, Push to deploy with Vercel |
| 24.90-27.90 | Rise | 4 -> air | snare/glitch roll building, filter rising; music cut to air 27.45-27.90 under a riser | white "Git hosting, at agent scale" |
| 27.90-30.90 | Button | 5 -> ring | one final unison hit on beat 1, ring-out, no more drums | ORIGIN logo assembles 27.9-28.8 |

Music ends: final hit at 27.9 rings out to 30.9 (fit --end-hit), no fade of a running loop.

## Hit list
| t | tier | moment | sound idea (layers incl. sub) | align |
|---|---|---|---|---|
| 0.40 | B | "Introducing Code Hosting" | bitcrushed key-click glitch stutter | attack |
| 6.37 | B | zoom into +New | tight 0.35 s air swish, center-in | peak |
| 7.0-7.9 | C | typing "everysphere-test" | 4 round-robin key presses, low, lpf | attack |
| 8.60 | B | Create Repo click | glassy UI click | attack |
| 11.00 | B | Sync from GitHub click | glassy UI click (other variant) + reverse data swell ending on 11.433 dashboard | attack / end |
| 16.80 | B | Ask Cursor menu pops | short glassy rising blip | attack |
| 20.20 | B (setup) | Squash & Merge click | signature: two branch pings (root, then fifth 70 ms later) | attack |
| 20.83 | A | drop: Run CI (cut to black) | impact transient + body thump + sub drop E1, reversed impact swell into it | attack / end |
| 27.90 | A | ORIGIN logo | signature chord (root+fifth+octave pings) + impact transient + sub drop + shimmer tail, riser ending on the frame | attack / end |

## Mix intent
Master -13 LUFS integrated, -1 dBTP, match "launch". No VO: music is the mix, bus around 0 dB. Short air before the drop (20.45-20.83, music -30 dB, low-passed through the break) and the main air before the logo (27.45-27.90 drop-out under the riser). Music dips 3 dB under each A-hit for 300 ms. Ends on the fitted final hit ringing out under the signature; last 50 ms near silence.

## What shipped (after generation + 6 mix passes)
- Score: ElevenLabs Music v2.5 take `score-2.wav` (analyzed 136.2 bpm, G major / G minor depending on the run; requested E minor). All three takes ignored the section dynamics the same way: a bass-less glitch intro until ~13.5 s, then one full groove to ~29.4 s. The big entrance lands at 13.49 s, on the "Review and Merge PRs" cut (13.567 s), so it was kept there instead of at 3.93 s.
- `fit.wav`: `music.py fit --end-hit 27.9 --end-src 28.11` splices the score's own stab onto the logo frame. Music is then gated to silence by 28.6 s (a hard stop button); the logo ring-out is the signature chord + shimmer + sub + room.
- `fit-lim.wav`: offline peak control (the session has no bus limiter). Intro limited ~6 dB to -3.5 dBFS peaks, about 6 LU under the groove; groove gently limited (crest 11 -> 9 dB). Script: audio/music/introlim.py.
- Break 17.83-20.83 is made in the mix: hpf 180 Hz (kick and bass out), lpf closing to 1.2 kHz, then air 20.45-20.81 and a full open on the drop at 20.833. Rise 25.3-27.4 is an lpf opening from 1.5 kHz, then air 27.45-27.88 under the riser.
- Tonal SFX tuned to G: signature = ping-2 +1.01 st (G5) and ping-2 -3.99 st / ping-3 -3.06 st (D5); sub drops land on G1.
- Things to check by ear: whether the bass-less first 13.5 s hooks hard enough on a phone; the hard stop at 28.4-28.6 s under the logo; the -3.99 st varispeed ping, which is slower and darker than the others.

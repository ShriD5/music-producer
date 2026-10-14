# Figma "Dev Mode, now in Codex": sound

Concept: a warm, bouncy organic synth-pop record that gets built while you watch: plucked "shape" notes snap together into a groove the way frames turn into a working site, and Figma's five coloured shapes become five tuned pops that resolve into the lockup chord.
Sub-genre/texture: organic electronic x synth-pop (Four Tet warmth, nu-disco bounce): kalimba/marimba-like plucked synths, round analog bass, tight live-ish drums, sidechained pads, real sub.   Tempo: 121 BPM   Key/mode: A major (bright, lydian #4 colour on pads)   Lead sound: plucked kalimba-synth hook + glassy FM bell arp
Product palette: the cursor and trackpad (Figma is multiplayer cursors), vector-pen anchor clicks, the coloured shapes themselves. Processed into music: a soft trackpad click pitched up becomes the hat-like C-tick on UI presses; one glassy "shape pop" pluck is re-pitched into the score's chord tones for every shape that appears; a filtered paper/air swish follows the camera pushes.
Refs (feel, not copy): Figma "Made in Figma" launch film (bright, dense, playful), Four Tet "Baby" / Jungle-style nu-disco bounce.
Signature sound: "the five shapes": one rounded glassy synth pop, pitched per shape to the tonic triad (root, 3rd, 5th) as the shapes burst at 34.17 / 34.42 / 35.00, paid off at the Figma x OpenAI lockup at 37.08 as a stacked root+3rd+5th+octave chord pop with a sub drop. Pitched to the analyzed key of the chosen take.
Banned this film: literal cartoon foley (boings, slide whistles), stock cinematic braam, generic whoosh on hard cuts, supersaw EDM drop, vocals, typing-sound per keystroke, a pop on every UI move.
Master: -13 LUFS integrated, -1 dBTP, match "launch". Music-led, no VO.

Ledger check (last 3: eclipse-rescore chamber pop 120 D major pizzicato/music-box; road-to-1k sine blips; raptor rumble): differs on genre, key/mode, lead instrument and signature (4 of 5). Tempo is in the same band as the eclipse rescore because 121 BPM is the tempo that puts all three A-moments on beats (28.17 -> 34.13 = 12 beats, 34.13 -> 37.08 = 6 beats).

Tempo note: spot.py with marks gives no candidate >= 0.5 in my lane (165/156/134/174), so the edit isn't rhythmic as a whole. 121 BPM is chosen from the A-hit spacing instead and `fit --hit` aligns the drop downbeat to 28.167.

## Music map
| out time | section | energy (1-5) | what happens musically | why (picture) |
|---|---|---|---|---|
| 0.00-5.25 | Intro | 2.5 | kalimba-synth hook + muted kick on beat 1 immediately, filtered bass | ChatGPT app, push-in to the sidebar, Figma icon click |
| 5.25-9.08 | Groove A | 3 | bass opens, hats + light clap join | Figma panel opens inside ChatGPT |
| 9.08-18.67 | Groove B | 3.5 | full groove, FM bell arp counter-line | Figma canvas: comments, annotation, select frames, ready-for-dev at 17.58 |
| 18.67-22.50 | Breakdown | 2 | drums out, plucks + warm pad only | composer: "3 Selected From Figma", typing the prompt |
| 22.50-28.17 | Build | 3 -> 4 | prompt sent: rising arp, snare build, filter opens; last half-bar drops out (AIR 27.55-28.10, the "Open in" click sounds alone) | Codex responds, tokens + components list, MOSF Virtual Tour card |
| 28.17-34.13 | Drop | 5 | full synth-pop chorus: four-on-floor, sub bass, hook on top | the built site appears next to the chat, browsing it |
| 33.95-34.12 | stop | - | hard musical stop (automation) | last frames of the site |
| 34.13-37.08 | Brand | 4 | half-time bounce, plucks answering the shape pops, rising into the button | black frame, Figma shapes burst and converge into the logo (36.33) |
| 37.08-40.00 | Button | 3 -> 0 | final unison hit on the lockup, ring-out to silence | Figma x OpenAI lockup |

Air before the biggest reveal: 27.55-28.10 (music to -30 dB, only the "Open in" click), drop on 28.167.

## Hit list
| t | tier | moment | sound idea (layers incl. sub) | align |
|---|---|---|---|---|
| 1.55-2.10 | C | camera push into sidebar | soft airy paper swish, panned slightly R->C, low | peak |
| 5.17 | C | Figma icon click | trackpad click, pitched up, lpf | attack |
| 12.30 | C | comment sent | trackpad click rr2 | attack |
| 17.58 | B | frames turn green, ready for dev | bright two-note glassy "done" chime in key + click | attack |
| 22.50 | B | prompt sent | send click + short soft upward synth zip (the build starts here) | attack |
| 26.80-28.10 | - | build into reveal | tonal synth riser, ends dead at 28.10, then air | end |
| 27.98 | C | "Open in" click, alone in the air | trackpad click rr3 | attack |
| 28.167 | A | built site revealed | punchy designed impact (transient) + warm felt thump body + sub drop in A + bright shimmer tail | attack |
| 34.125 | A | cut to black, shapes burst | shape pop (root) + sub drop + short glitchy body | attack |
| 34.42, 35.00 | C (signature setup) | shapes appear | shape pop re-pitched to 3rd, 5th | attack |
| 35.40-36.33 | - | shapes converge to the logo | short reverse swell of the shape pop, ending on the logo | end |
| 36.333 | B | Figma logo | soft rounded tap, low | attack |
| 37.083 | A | Figma x OpenAI lockup | signature chord pop (root+3rd+5th+octave stacked) + sub drop + score's final hit | attack |

## Mix intent
-13 LUFS, -1 dBTP, launch tonal match. Music is the mix (bus ~0 dB). Underwater lpf for the breakdown (18.67-22.5), filter opening across the build, air 27.55-28.10, everything opens on 28.167. Hard stop 33.95-34.12, brand section in at 34.125, final hit on 37.08 rings out to silence by 40.0. SFX share a tight room (size 0.3), tails send more than transients. A-hit transients centred for mono.

## As built (2026-10-14)
- Score: `audio/music/score-1.wav` (ElevenLabs Music v2.5 via fal, plan-locked, 121.1 BPM, analyzed **D major**, not the requested A major). Take 2 had a stray drop-out at 23 s and a messier tail; take 1 has sub from frame 1, a steady layering build (hats arrive ~15.5 s) and a clean ring-out right on the lockup. Neither take followed the planned breakdown/drop dynamics (every section within 1 dB); a third, more forceful take failed (fal balance exhausted), so the arc is done with automation as music.md recommends.
- Fit: `music.py fit --hit 28.167 --src 28.241` (source beat 57 onto the reveal frame; 34.125 and 37.083 then land on source beats 69 and 75). Output `audio/music/fit.wav`.
- Signature retuned to the analyzed key: one ElevenLabs "glassy pop" (measured F#3 -25c) re-pitched to D4 / F#4 / A4 (+8.25 / +12.25 / +15.25 st) for the shape pops, and stacked D3+D4+F#4+A4+D5 with a D1 sub drop on the lockup. Up an octave from the first pass because at F#3 the pops were 97 % below 300 Hz and failed the phone check.
- Automation: intro -4 dB lpf 5 kHz, groove A -3, groove B -1.5, breakdown -8 dB with lpf 900 Hz, build -6 -> -1 with lpf 1.4k -> 12k, air 27.71-28.14 (riser + the "Open in" click alone), drop re-enters -5 dB under the A-hit and opens to -0.8 by 28.6 (room for the hit, limiter <= 4 dB), hard stop 33.89-34.10, brand section enters -4.5 under the burst then -1.5, natural ring-out after 37.08.
- Justified WARN: "not over-scored 7.2 per 10 s" counts layers, not moments. There are 14 distinct sound moments in 40 s (3.5 per 10 s); the A-hits are 4-8 layers each by design.
- SFX via ElevenLabs direct (MUSIC_PRODUCER_ELEVEN_ROUTE=direct) because fal was locked out; that key is on the ElevenLabs **free** plan (about 420 credits used, logged as $0). Free-plan SFX output needs attribution and isn't licensed for commercial use, so regenerate on a paid plan or via fal before anyone ships this commercially.

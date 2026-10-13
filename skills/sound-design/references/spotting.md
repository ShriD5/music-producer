# Spotting: deciding what gets sound, and when

Spotting is the session where the director and the sound team watch the cut and decide every cue. You are both. Watch the contact sheet (`audio/spot.png`) and decide **before** generating anything.

## The arc of a 20–60 s launch film

1. **Hook (0–2 s).** Sound starts on frame 1. Feeds autoplay muted, and unmuting into silence loses people. Open on an identity element (texture, the signature motif in miniature, a distinctive first hit), not a slow pad fade-in.
2. **Problem / setup.** Sparse. Fewer elements, more space, maybe off-kilter (filtered, mono, detuned) if the story is "the old way hurts".
3. **Turn → reveal.** The biggest moment. Preceded by **air**: 0.2–1.0 s where the music drops out, filters down, or holds a single note. Then the full score enters on the reveal frame with the A-hit.
4. **Proof / features.** Driving, steady. Music carries; B-hits on the 2–4 most important UI moments only. Repetitive UI gets C-ticks at low level, round-robin.
5. **Button.** Logo/CTA: the music lands its final hit on the logo frame and rings out, with the signature sound on top. The last 0.5–2 s is decay, not a fade of a still-playing loop.

## Hit hierarchy

| Tier | Per 30 s | Level vs. bed | Examples | Construction |
|---|---|---|---|---|
| A | 1–3 | 3–6 dB over | logo, hero reveal, price/"free" moment, CTA | 3 layers: transient + body + tail, plus the score hitting with it |
| B | 3–8 | about level | key UI action, section cut, stat landing | 1–2 layers, short |
| C | as needed | 8–12 dB under | typing, list items, cursor clicks, toggles | single, round-robin variants, often band-limited |

If you're spotting more than 7 events per 10 s, you're scoring a toy. Delete C-ticks first, then B-hits that aren't story beats.

## Sync rules

- **Transient on the frame.** The ear catches 1 frame early more than 1 frame late. If a hit feels late, nudge it 1 frame (≈33 ms at 30 fps) earlier, never later.
- **Cuts vs. motion.** A hard cut wants either a hit or a musical downbeat. An in-frame move (slide, zoom, swipe) wants a movement sound **shaped like the motion**: same duration, panned the way it moves (`pan` → `pan_to`), loudest at peak velocity.
- **Swells end on the frame.** Reverse cymbals, risers and inhales use `align: end` so the swell peaks exactly at the event. Then cut the swell dead and let the hit carry.
- **J and L cuts.** Let a sound from the next shot start 2–6 frames before the cut (J), or a tail ring past it (L). It glues the edit and feels intentional.
- **Music before SFX.** First make the score land on the big moments (plan sections / fit). SFX then decorate, they don't rescue.

## What not to score

- Cuts that are just continuity (same subject, new angle) when music already carries.
- Every list item, every cursor movement, every hover.
- Text appearing on screen. Kinetic type gets the score's rhythm, not a pop per word, unless it's a deliberate C-tick pattern.
- Anything the VO is talking over, unless it's an A-hit.

## Tempo-to-picture

If the edit was cut freely, `spot.py` prints `tempo_candidates`: BPMs (and beat phase) whose grid lands on the most cuts and marks. Pick one inside your identity's tempo band, prompt the score at that BPM, and `music.py fit --bpm` the chosen take onto it. If no candidate scores ≥ 0.5, the edit isn't rhythmic. Score with texture and hit the A-moments via section boundaries instead.

## Music map from the cut

Turn marks into section boundaries (ElevenLabs chunks are ≥ 3 s, ≤ 30 sections):
- a section boundary on the reveal frame (drop/full entrance),
- one just before it for the air (a 3 s "breath" chunk, with the actual silence placed by automation),
- a final chunk that starts on the logo frame with `{final hit on beat 1, then let it ring}`,
- intro chunk that starts strong (no 4-bar fade-ins in short films).

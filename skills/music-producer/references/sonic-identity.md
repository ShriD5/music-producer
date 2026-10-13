# Sonic identity

Two questions, in this order:
1. **What does a premium launch film sound like?** That's the floor, and it's not negotiable (see "Launch film grammar").
2. **What does *this* product sound like?** That's the identity, and it lives *inside* the grammar, not instead of it.

The failure this file guards against goes both ways. Skip (2) and every film sounds like the same stock track. Skip (1) and you get something "distinctive" (pizzicato comedy, lounge jazz, chiptune) that a listener files under *royalty-free quirky corporate music* within two seconds. In a blind test against Arc, Figma, Raycast and Stripe launch films, a pizzicato-and-celesta score with cartoon foley ranked last and was called "generic stock, thin, cheap", even though it was bespoke.

## Launch film grammar (measured)

Benchmarked on real music-led launch films (`launch-reference.json`, numbers from 7 films: Arc 1.0, Figma "Made in Figma", Framer 3.0, Notion Calendar, Notion Custom Agents, Raycast Glaze, Stripe agent wallet):

- **Modern produced music.** Electronic or hybrid: cinematic electronic, glitch/IDM, house/tech-house, synth-pop, ambient-into-drop, organic electronic. Even "acoustic" premium scores are produced like electronic records: tight, sidechained, layered, wide, with sub.
- **Sub weight.** Every reference has real energy at 30–60 Hz: a sub bass, an 808, sub drops under impacts. A score without it reads thin and cheap at any loudness. `analyze.py` flags missing sub against the reference curve.
- **Dense, abstract, layered sound design** woven into the music. Risers into drops, impacts with sub, whooshes that follow camera moves, glitch stutters, reverse swells, crisp UI ticks. These sounds are *designed* (synthetic, processed, musical), not literal foley. Literal cartoon sounds (boings, gulps, yawns, springs) read cheap unless the film is a cartoon.
- **Loud and dense.** Integrated −10 to −17 LUFS (median −13.6), short-term range small (LRA median 5.4). The music is compressed and saturated. Builds and drops come from arrangement and automation, not from quiet stretches.
- **Arrangement energy follows the edit.** Hook in the first second, build, a drop on the reveal, a breakdown, a final drop or button. The energy shape changes every 5–10 s.

Risers, impacts and whooshes are **the grammar, not the cliché**. The cliché is a *stock* riser/impact/whoosh that's reused across films, generic, unsynced and untuned. Ours are designed per film, tuned to the key, layered with sub, and sit on the frame.

## Where identity lives (inside the grammar)

1. **Sub-genre and texture.** Not "electronic", but *which* electronic: glassy glitch for an AI tool, warm organic house for a consumer app, cold minimal techno for infra, cinematic hybrid for a platform launch. Pick from the palette below and mutate one axis.
2. **A sound palette sampled from the product's world.** The product's physical metaphor (a menu-bar utility is a light switch; a notch app is a tiny mechanism; a payments API is a vault bolt) becomes **percussion, transitions and the signature**: processed, pitched and layered into the electronic production, not played as literal foley. A latch becomes the snare; a switch click becomes the hi-hat; a mechanism ratchet becomes the riser.
3. **The signature sound.** One designed sound at the logo/button (below).
4. **Arrangement shaped to this edit.** The music map makes the drops land on this film's reveals.
5. **The ledger.** Vary sub-genre, tempo band, key/mode, lead sound and signature from the last 3 films. Never vary away from the grammar.

## Palette catalogue (premium foundations)

Pick one, then mutate at least one axis (lead sound, tempo, mode, texture) so it's yours. Every entry keeps modern production and sub.

| Direction | BPM | Mode | Core palette | Fits |
|---|---|---|---|---|
| Cinematic electronic / hybrid | 90–120 | minor→major | pulsing synth bass, sub, big drums, risers, string or choir pads, impacts | platform launches, "a new era" |
| Glitch / IDM | 100–140 | minor | micro-edited percussion, granular textures, bitcrush stutters, deep sub | AI, data, dev tools |
| Organic electronic (Bonobo / Four Tet) | 110–124 | dorian | chopped organic samples, warm plucks, live-ish drums, sub bass | creative tools, consumer, warm brands |
| Tech-house / minimal | 122–128 | minor | dry punchy kick, rolling bass, clicks, filter sweeps | productivity, infra, "precision" |
| Future garage / 2-step | 130–134 | minor | shuffled drums, vocal-chop textures (wordless), reese sub, airy pads | mobile, youthful, fast |
| Synth-pop / nu-disco | 110–122 | major | bright arps, plucky bass, four-on-floor, sidechained pads | playful consumer, celebrations |
| Ambient into drop | free → 120+ | lydian | swelling textures for the first third, then a hard drop into a groove | product reveals with a big turn |
| Liquid drum & bass | 172–176 | minor 9ths | rolling breaks, reese sub, airy pads | speed, realtime, performance |
| Afro-house | 118–124 | minor | log drum, shakers, marimba, deep sub | warm, global, payments |
| Neo-classical + electronic (Ólafur Arnalds) | 80–110 | minor | felt piano, strings, glitchy beat, sub swells | privacy, calm, focus, premium hardware |
| Musique concrète electronic | any | any | a full electronic track built from the product's real sounds, processed | the most ownable option; signature-heavy films |
| Trap / half-time cinematic | 140 (70) | minor | 808 sub glides, crisp hats, dark pads, impacts | confident, bold, creator tools |

Novelty genres (pizzicato comedy, ukulele, lounge, jazz trio, chiptune, polka) read as stock in launch films. Use them only when the brief is explicitly a comedy/cartoon piece, and even then produce them like a modern record (sub, compression, designed transitions).

## The signature sound

One sound, 0.3–2 s, that could only belong to this product. It plays at the logo/CTA button, and optionally once earlier as a setup so the ending pays it off.

- Build it from the metaphor, then **design** it: a real latch layered with a tonal synth ping and a sub drop; a switch click into a filtered chord stab; a mechanism tick through a pitched delay.
- **Pitch it to the score's analyzed key** (clip `pitch`). An out-of-key signature is the most common "pasted on" tell.
- If it's tonal, make it 2–4 notes that outline the tonic chord: the score's final chord + signature = the sonic logo.

## Banned

- Numpy/hand-synthesized music beds. (Designed sub drops via `sfx.py sub` are fine: that's a sound-design layer, not a score.)
- Stock SFX packs reused across films, and top-of-library music.
- Literal cartoon foley (boings, gulps, yawns, springs, slide whistles) in a premium film. For a character, use tonal designed blips: short pitched synth or processed-voice gestures in key.
- Unsynced transitions: a whoosh on a cut with no motion, a riser that doesn't resolve into a hit or drop.
- A score with no sub, or a master quieter than −16 LUFS for a music-led film.

## `audio/SOUND.md` template

```markdown
# <Film name>: sound

Concept: <one sentence: premium grammar + what this product sounds like>
Sub-genre/texture: <...>   Tempo: <bpm>   Key/mode: <...>   Lead sound: <...>
Product palette: <real-world sounds from the product's metaphor, and how they're processed into the track>
Refs (feel, not copy): <real launch film or artist>, <...>
Signature sound: <description> (pitched to <note>), plays at <t>s (setup at <t>s)
Banned this film: <...>

## Music map
| out time | section | energy (1-5) | what happens musically | why (picture) |
|---|---|---|---|---|

## Hit list
| t | tier | moment | sound idea (layers incl. sub) | align |
|---|---|---|---|---|

## Mix intent
<loudness target, where it drops, where the air is, how it ends>
```

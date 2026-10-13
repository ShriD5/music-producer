# Sonic identity

The question is not "what music fits a tech launch". It is **"what does this product sound like?"** Answer it from the product's own world before reaching for a genre.

## Derive it (in this order)

1. **The product's physical metaphor.** What does using it feel like in the hand? A menu-bar utility is a light switch, a packing app is zips, tape and a suitcase latch, a payments API is a cash drawer or a vault bolt, a dev tool is keys and a terminal bell. Those real objects become the **signature sound** and often the **percussion kit**.
2. **The user's state at the moment of value.** Relief (calm resolves), speed (driving pulse), control (precise, dry, tight), delight (playful, bouncy), power (weight, low end), focus (minimal, sparse).
3. **Brand personality vs. category cliché.** Name the category cliché out loud (SaaS = bright corporate piano + claps; AI = glassy pads + arpeggios; crypto = dark trap; fintech = soft strings). Then move at least two steps away from it, while staying true to (2).
4. **The edit's rhythm.** Fast-cut films want a tempo that lands on cuts (spot.py `tempo_candidates`). Long-take demo films want texture and pulse, not a beat fighting the UI.

## Palette catalogue (starting points, not presets)

Pick one, then mutate at least one axis (instrument, era, tempo, mode) so it's yours. BPM and mode are typical ranges.

| Direction | BPM | Mode | Core palette | Fits |
|---|---|---|---|---|
| Felt-piano minimalism | 70–90 | major/lydian | felt piano, room tone, soft pedal noise, cello harmonics | calm, privacy, focus tools |
| Analog warmth / tape soul | 84–96 | dorian | Rhodes, tape-saturated drums, upright bass, vinyl hiss | personal, human, creative tools |
| Lo-fi boom-bap | 82–92 | minor 7ths | dusty MPC drums, chopped jazz chords, sidechained hiss | indie hacker, notes, journaling |
| Neo-soul / live funk | 96–108 | dorian | clean guitar, slap/finger bass, live kit, horns stabs | social, community, consumer |
| Disco / French touch | 112–122 | major | filtered disco loop, four-on-floor, string runs | playful consumer, launches with a "party" |
| UK garage 2-step | 130–134 | minor | shuffled hats, chopped vocal-free stabs, sub bass | fast, youthful, mobile |
| Afro-house / amapiano | 112–118 | minor | log drum, shakers, marimba, deep pads | warm, global, money moving |
| Minimal techno pulse | 122–128 | phrygian | dry kick, rim, modular bleeps, long filter sweeps | infra, dev tools, precision |
| Liquid drum & bass | 172–176 | minor 9ths | rolling breaks, Reese sub, airy pads | speed, performance, realtime |
| Breakbeat / big beat | 120–135 | mixolydian | chopped breaks, distorted bass, scratch-like FX | bold, irreverent, hacker energy |
| Hybrid orchestral | 90–120 | minor→major | taiko, string ostinato, brass swells, synth sub | big platform launches, "a new era" |
| Chamber pizzicato | 110–132 | major | pizzicato strings, celesta, woodblock, bassoon | clever, cheeky, productivity hacks |
| Jazz trio brushes | 120–160 swing | ii-V | brushed kit, walking bass, piano comping | elegant, finance, craft |
| Bossa / lounge | 120–140 | major 7ths | nylon guitar, shaker, flute, soft rhodes | travel, lifestyle, ease |
| Synthwave / 80s | 96–108 | minor | gated snare, Juno pads, arps, chorus bass | nostalgia, retro UI, games |
| Chiptune / 8-bit | 120–150 | major | square leads, noise drums, arps | games, dev easter eggs, playful |
| Glitch / IDM | 90–140 | atonal/minor | micro-edits, granular, bitcrush, clicks | AI, data, "under the hood" |
| Ambient drone + granular | free | lydian | swelling textures, field recordings, no drums | research, deep tech, cinematic intros |
| Musique concrète | any | n/a | a beat built only from the product's real-world sounds | the most ownable option; best for signature-heavy films |
| Phonk / drift | 130–145 | minor | cowbell melody, distorted 808, Memphis drums | aggressive, edgy, gaming |
| Trap half-time | 140 (70) | minor | 808 glides, hats rolls, sparse keys | confident, street, creator tools |
| Indie rock live | 110–130 | major | live drums, overdriven guitar, bass, handclaps | scrappy founders, human stories |
| Gospel / choir pads (wordless) | 70–100 | major | organ, wordless choir "ooh", claps | uplifting, community, nonprofit |
| Kannada / Carnatic fusion | 90–120 | raga-based | mridangam, veena/violin, electronic sub | Indian market, regional pride |

## The signature sound

One sound, 0.3–2 s, that could only belong to this product. It plays at the logo/CTA button and optionally once earlier as a setup, so the ending pays it off.

- Build it from the metaphor: a suitcase latch + a soft bell, a light-switch click into a warm chord, a terminal bell pitched to the score's tonic.
- **Pitch it to the score's key** (`pitch` in semitones on the clip, or ask for the note in the prompt). A signature in a different key from the score is the most common "pasted on" tell.
- If it's tonal, make it 2–4 notes that outline the tonic chord: the score's final chord + signature = the sonic logo.

## Banned defaults (unless the brief explicitly asks)

- Numpy/hand-synthesized beds (supersaws, sine blips, noise risers) as the score.
- Generic stock SFX packs (the same `whoosh`, `riser`, `impact`, `glitch`, `chime` in every video) and top-of-library music hits.
- The trio "riser into bass impact into whoosh" as the shape of every reveal.
- Corporate ukulele/glockenspiel/clap-along, "inspiring" piano + strings for tech, generic future-bass drops.
- A riser before every section change; a whoosh on every cut; a click on every UI element.

## `audio/SOUND.md` template

```markdown
# <Film name>: sound

Concept: <one sentence: what this product sounds like and why>
Category cliché we're avoiding: <...>
Genre/feel: <...>   Tempo: <bpm>   Key/mode: <...>   Lead: <instrument>   Texture: <...>
Refs (feel, not copy): <artist/track>, <artist/track>
Signature sound: <description> (pitched to <note>), plays at <t>s (setup at <t>s)
Banned this film: <...>

## Music map
| out time | section | what happens musically | why (picture) |
|---|---|---|---|

## Hit list
| t | tier | moment | sound idea (layers) | align |
|---|---|---|---|---|

## Beds
<ambience / foley, where they enter and leave>

## Mix intent
<what should be loudest when, where the air is, how it ends>
```

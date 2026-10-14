# SFX: designed, not picked

Every effect is chosen or generated for its moment, in this film's world, with the score's key in mind. Recordings and generations are both raw material: layer, pitch, filter and room them.

## Providers (`cues.json` → `provider`, or `sfx.py gen --provider`)

| provider | Tier | Price | Best at |
|---|---|---|---|
| `openverse` | free, no key | $0 | CC0 field and foley recordings (mostly Freesound) via the Openverse API. Real-world sounds: clicks, knocks, paper, cloth, mechanisms, ambiences. Weak on designed/cartoon sounds. |
| `freesound` | free key | $0 | Same recordings with better search (rating, duration filters). Get a key at freesound.org/apiv2/apply. |
| `eleven` | paid | $0.002/s (fal) or your ElevenLabs credits | Designed hits, UI, impacts, transitions, creature/cartoon sounds, anything specific. 0.5–22 s, `loop` for beds. |
| `stable` | paid | $0.02/gen | Long textures, ambiences, drones, mechanical loops; negative prompts. |
| `sonilo` | paid | $0.0018/s | Natural foley and environments. |
| `sfx.py video` | paid | $0.009/s | A full-length foley/ambience bed that follows the picture (`--segments` steer each range). Put it on `amb`, low. |

### Recorded libraries (free tier)

- Write a `query` per cue: 2–3 plain words, the object + action ("wood block knock", "paper flutter", "music box"). The script widens automatically (drops the length filter, then leading words) when nothing matches.
- Recorded takes are cropped to their strongest event (`dur` long), swells (`keep_head: true`) to the `dur` seconds ending on their peak, then levelled like generated takes.
- Licenses default to CC0 (`"licenses": ["cc0"]`). Add `"by"` for more choice; attribution then goes in `audio/CREDITS.md` and must ship with the video description.
- Libraries are literal. A "cute creature hm?" comes back as bird chirps. For character voices and cartoon sounds, either build them (pitch a real sound up 5–9 st, layer two), or use the paid generator for those cues only (`"provider": "eleven"` on the cue).

## Prompt anatomy

`[source object + material] [action] [size/weight] [speed/duration], [perspective: close-mic / mid / distant], [space: dry / small room / hall], [what to exclude]`

- Always ask for **dry, close-mic, no music, no reverb** for hits. The room is added in the mix so everything shares one space.
- Name materials: glass, brushed aluminium, felt, rubber, paper, ceramic, plastic, wood, leather, fabric, water.
- Name the verb precisely: snap, latch, thunk, flick, tap, tear, slide, zip, pop, clack, flutter, crumple.
- Give the duration you need (`dur`) close to the visual action. A 0.4 s slide does not get a 3 s whoosh.
- `influence` 0.3–0.5: higher follows the prompt tighter but gives fewer variations between takes.

Examples:
- Logo latch (A-hit transient): `heavy brushed-aluminium suitcase latch snapping shut, single crisp metallic click with a short low thunk, close-mic, dry, no reverb, no music`
- Body under it: `deep soft felt-mallet thump on a large drum, short, warm, close-mic, dry`
- Tail: `soft airy shimmer of small bells decaying, tonal around E, gentle, dry`
- UI tap (C-tick): `tiny soft plastic tap on a phone screen, very short, close-mic, dry`
- Slide motion: `quick smooth fabric swish passing left to right, 0.4 seconds, close, dry, not a cinematic whoosh`
- Data landing (B-hit): `short wooden marimba-like knock with a bright paper flick, crisp, dry`
- Air before reveal (`keep_head: true`): `single slow inhale of air through a narrow tube, reversed-cymbal-like swell, 1.2 seconds, ending abruptly`

## Layering an A-hit

Clips at the same `at`, each `align: attack` (or `end` for the swell, which leads in and is not part of the hit):

| Layer | Freq focus | Job | Typical gain |
|---|---|---|---|
| Transient | 1–6 kHz | the "click" the eye syncs to; survives phone speakers | 0 dB |
| Body | 80–400 Hz | weight; felt on headphones and laptops | -3 to -6 dB |
| Tail | 2–10 kHz or tonal | space and identity; often the signature | -6 to -10 dB, send to room 0.2–0.35 |
| Sub | 30–80 Hz | the weight every launch film has: `sfx.py sub --note <tonic>1` | -4 to -8 dB, no send |
| (optional) Swell | broadband | anticipation, `align: end` on the hit | -8 to -12 dB, fade_out 0 |

Check that layers don't stack the same frequency range: hpf the tail (~1 kHz), lpf the body (~2 kHz).

## Designed, not literal

Premium launch films use *abstract* designed sounds: synthetic, processed, musical. Prompt for the design, not the object:
- Impact: `tight cinematic impact, punchy transient, short metallic ring, no reverb, no music` + a `sfx.py sub` layer
- Riser: `short tonal synth riser building tension, 1.5 seconds, ending abruptly, no drums` (`keep_head`, `align: end`)
- Whoosh: `fast airy whoosh passing left to right, 0.5 s, modern, clean` (pan with the motion)
- Glitch: `short digital glitch stutter, crisp, 0.3 s` (on an edit or a UI state change)
- UI tick: `tiny crisp synthetic UI tick, very short, high-pitched, clean` (round-robin, low)
- Character gesture (instead of a cartoon voice): `short cute rising synth blip, two notes, soft, in A major`
For the free tier, recordings work as **raw material**: pitch them, layer them with a sub drop, filter them, and run them through the room so they stop sounding like field recordings.

## What generators ignore

ElevenLabs SFX rarely obeys musical notes ("C# then G#" comes back as one random note) or band requests ("low-mid body" came back 95% sub, twice). Don't prompt for pitch: generate, then run `sfx.py tune` and set the clip `pitch`. Shape bands with clip `hpf`/`lpf`/`eq`, not prompts.

## Pitch and weight

- Clip `pitch` (semitones, varispeed) changes pitch and length together, like slowing tape. -3 to -7 st adds weight to impacts, +2 to +5 tightens UI sounds.
- Tonal hits/signature: tune to the score's key (analyze gives the key). E.g. a take that rings at A in a D-major score: +5 st or -7 st.

## Repeats

Anything heard more than twice: `sfx.py variants <take> --n 6` → `-rr1..rr6`, and rotate them in the session. Also vary `gain_db` by ±1.5 dB and `pan` by ±0.15 between repeats. Identical repeats are the machine-gun effect.

## Transitions vocabulary (use sparingly)

- **Whoosh/swish:** only when something on screen moves fast. Duration = motion duration, panned with it (`pan` → `pan_to`). Prefer material-based swishes (fabric, paper, air through a tube) over "cinematic whoosh".
- **Riser/swell:** at most once per film, before the biggest reveal, `align: end`, followed by air or a hard hit.
- **Reverse hit:** reversed tail of the actual A-hit (`reverse: true` on a copy) leading into it. Ownable and in-key.
- **Stop/tape-stop:** a hard musical stop (automation to -inf over 1–2 frames) is often stronger than any effect.

## Picking takes

`sfx.py gen` makes 3 takes per cue and prints peak offset + level. Use `listen.py audio/sfx/<id>-*.wav --compare --ask "..."`, plus your own rules: tightest transient (peak offset < 10 ms for hits), no tonal clash with the score, no embedded reverb/music. Delete the losers so the mix session can't pick them by accident.

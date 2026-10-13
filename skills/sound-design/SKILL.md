---
name: sound-design
description: Production audio for any rendered video (launch films, promos, trailers, explainers, demos, reels, social clips), free by default. Covers sonic identity, spotting, scoring to picture (local ACE-Step for free, or ElevenLabs Music / Lyria / MiniMax / Stable Audio with your own keys), designed SFX (free CC0 recordings or generated), VO processing, mixing with ducking and a shared room, mastering to LUFS/true-peak, and measured QA. Works on any mp4 from any tool (Remotion, HyperFrames, After Effects, Premiere, screen recordings). Use whenever a video needs music, sound effects, a mix or a master; when the audio is generic, samey, flat or cheap; or after picture lock in any video workflow, in place of library BGM and stock SFX packs.
---

# Sound design: score, design, mix, master

Agents make every video sound the same: one library track, the same whoosh / riser / bass-impact pack, or a hand-synthesized "EDM" bed. They add no identity and no picture sync, set flat levels and skip mastering. This skill does what a post house does: **decide what this film sounds like, spot it against picture, score to the cut, design each sound for its moment, mix in one room, master to spec, and measure everything, because you cannot hear.**

`SKILL_DIR` below is the directory of this file. All scripts are uv single-file scripts: `uv run $SKILL_DIR/scripts/<x>.py ...`, run from the video project root. Output goes to `./audio/`.

## Setup and tiers

Run `uv run $SKILL_DIR/scripts/setup.py doctor` first. It shows what works on this machine and what each missing piece would unlock. Requirements: `ffmpeg` and `uv`.

| | **free** (default) | **paid** (`SOUND_DESIGN_TIER=paid`) |
|---|---|---|
| Music | ACE-Step 1.5, local, MIT (`setup.py ace` once, ~10 GB). ~4–5 min per 40 s take on an M-series Mac, seconds on a CUDA GPU | ElevenLabs Music v2.5 plans (sections locked to the cut) via `FAL_KEY` or your own `ELEVENLABS_API_KEY`; Lyria, MiniMax, Stable Audio via fal |
| SFX | CC0 recordings: Openverse (no key) or Freesound (free `FREESOUND_API_KEY`); credits written to `audio/CREDITS.md` | Generated per prompt: ElevenLabs SFX (fal or direct), Stable Audio, video-to-foley |
| Mix, master, analysis | local, free | same |
| Ears (optional) | `OPENROUTER_API_KEY` + Gemini Flash, ~$0.005 per film | same, or `--model ~google/gemini-pro-latest` |

`auto` picks within the tier, and any call can override it with `--provider`. Keys are read from env vars, then `./.env`, then `~/.config/sound-design/keys.env`. Paid spend is logged per project in `audio/costs.jsonl`: about $0.60 for a lean 40 s film, $1.50–2 with extra takes and foley. If the free music doesn't satisfy the user, offer the paid tier for the score alone. That's where the money buys the most.

## Workflow

Do the steps in order. Each has a gate, and the measurement scripts exist so the gates aren't vibes.

### 1. Picture first
Audio is cut to a **locked** picture. Get the render (`renders/video.mp4` or similar) and, if the timeline is known (HyperFrames `data-start`, storyboard frame times), write `audio/marks.json` = `[{"t": 5.0, "label": "logo reveal"}, ...]` for the moments that matter. Exact marks beat detection.

### 2. Sonic identity → `audio/SOUND.md`
Run `uv run $SKILL_DIR/scripts/ledger.py show` first. Then read `references/sonic-identity.md` and write `audio/SOUND.md`:
- a one-sentence sonic concept tied to the product (not "upbeat tech"),
- genre / tempo / key-mode / lead instrument / texture, plus 2 reference tracks or artists for feel,
- the **signature sound**: one sound that could only belong to this product, used at the logo/CTA button,
- a banned list for this film.

**Gate:** it must differ from the last 3 ledger entries on at least 3 of: genre, tempo band (±15 BPM), key/mode, lead instrument, signature sound. If the brief truly demands similarity (series format), say so in SOUND.md.

### 3. Spot → cue sheet
`uv run $SKILL_DIR/scripts/spot.py renders/video.mp4 [--marks audio/marks.json]`, then **Read `audio/spot.png`**. Use it to see what is on screen at every sync point. Using `references/spotting.md`, add to SOUND.md:
- the **music map**: sections with output times (intro / build / drop / breakdown / button), the one moment of air before the biggest reveal, and where the music ends,
- the **hit list** with hierarchy: A-hits (1–3 per 30 s: logo, hero reveal, CTA), B-hits (key UI moments, cuts that matter), C-ticks (repeated small UI). Most cuts get **no** sound,
- ambience/foley beds if the picture has a physical world,
- tempo: if the edit has a rhythm, take a `tempo_candidates` BPM from spot.json so cuts land on beats.

### 4. Score → `audio/music/`
Read `references/music.md`. Write `audio/music/plan.json`: sections whose `until` times are the cut times from the music map, plus global styles (genre, instruments, BPM, key). The same plan drives every provider. ElevenLabs renders the sections exactly; prompt-only models (ACE-Step, Lyria, MiniMax) get it folded into a caption with BPM and key.
`uv run $SKILL_DIR/scripts/music.py gen --plan audio/music/plan.json --n 2` (tier default; `--provider eleven|ace|lyria|...` to choose)
Then:
- `music.py analyze <takes> --plan audio/music/plan.json` on every candidate (bpm, key, entrances, ending, and the level step at each planned boundary). Pick the take whose A-moment boundaries step up hardest. Use `listen.py --compare` only as a tie-breaker on genericness and artifacts,
- generated music ignores requested keys and quiet sections more often than not. Tune tonal SFX to the **analyzed** key. Enforce sections with `music.py repaint <take> --start 24 --end 29 --prompt "drums stop, sleepy celesta"` (free, local) or with automation in step 6,
- pick one, then `music.py fit` to the exact duration, aligning a source entrance to the reveal (`--hit/--src`), ending on a button (`--end-hit`) or ring-out; `music.py extend` (paid) or a longer `gen` if it's short.

**Gate:** no numpy/hand-synthesized music beds, ever. Synthesis is only for test tones.

### 5. Design SFX → `audio/sfx/`
Read `references/sfx.md`. Write `audio/sfx/cues.json`: one cue per hit, layered as **transient + body + tail** for A-hits, 3 takes each. Every cue gets a descriptive `prompt` (for generators) and a short `query` (2–3 words, for recording libraries), so it works on either tier. Then `uv run $SKILL_DIR/scripts/sfx.py gen --cues audio/sfx/cues.json`. Recorded takes are cropped to their strongest hit, levelled, and credited. Use `sfx.py variants` for anything that repeats (typing, ticks), and `sfx.py video` (paid) for a physical-world foley bed. Pick takes by the index (peak offset, duration) plus `listen.py --compare`, and delete the losers.

**Gate:** no stock "SFX pack" sounds reused across films, and no generic "whoosh" on a cut without motion. Recordings are raw material: pitch, layer, filter and room them into this film's world.

### 6. Mix → `audio/session.json` → `audio/mix/`
Read `references/mix.md`. Write the session: buses (vo / music / sfx / amb), clips with `align: "peak"` for hits and `"end"` for swells, ducking with a speech-band carve, music automation (pre-drop filter, drop-out of air, swells), pans that follow on-screen motion, and sends into the shared room. Then:
`uv run $SKILL_DIR/scripts/mix.py audio/session.json`

### 7. Measure, look, fix: at least 2 passes
`uv run $SKILL_DIR/scripts/analyze.py`, then **Read `audio/mix/analysis.png`** and `report.md`. Fix every FAIL and every WARN you can't justify in one sentence, then re-render. Then get ears:
`uv run $SKILL_DIR/scripts/mix.py audio/session.json --mux && uv run $SKILL_DIR/scripts/listen.py renders/video.sound.mp4 --brief audio/SOUND.md`
`listen.py` is optional (needs `OPENROUTER_API_KEY`). Act on its notes when the measurements agree, or when a note repeats across two passes. Its scores are inflated, and it will "hear" events the brief describes even when they aren't there. Use it to find problems, never to confirm sync or quality. When `mix.py` prints limiter hotspots, turn down the clips it names there.

**Gate (all must hold):** integrated loudness within ±0.5 LU of target, true peak ≤ ceiling, no clipping, every peak-aligned hit within 1 frame, VO ≥ 8 dB over the bed in the speech band, A-hits survive a 300 Hz high-pass (phone speakers), mono fold-down loses < 3 LU, and the ending resolves (no chop).

### 8. Deliver
`renders/<name>.sound.mp4` (video stream copied, AAC 320k), plus `audio/mix/mix.wav` (48k/24-bit) and `audio/mix/stems/`. Report to the user: the concept, what's playing, the measured numbers, the tier and spend, the credits file if recordings were used, and anything the user should check by ear (you haven't heard it). Then log it:
`uv run $SKILL_DIR/scripts/ledger.py add --project <name> --genre "..." --bpm N --key "..." --palette "..." --signature "..." --music-source "..."`

## Non-negotiables (what separates produced from generated)

1. **Silence is designed.** Leave 0.2–1.0 s of air (drop-out, filtered-down bed, or held breath) before the biggest reveal. Wall-to-wall sound is the top amateur tell.
2. **Hierarchy.** At most three A-hits per 30 s. Every sound earns its place. If two hits within 0.4 s compete, cut one.
3. **Sync by transient, not file start.** Hits use `align: peak`, swells use `align: end`, and the analyzer verifies 1-frame accuracy.
4. **One room.** SFX and foley share a reverb send, so things sound recorded in the same space, not pasted on.
5. **Never repeat a sample audibly.** Repeated hits use round-robin variants.
6. **Music is edited, not trimmed.** It enters on a downbeat or a strong entrance and ends on a button or a ring-out. Never fade the music out over the logo because the file ran out.
7. **Carve, don't bury.** Under VO, duck the speech band harder than the lows (`mid_extra_db`). Don't drop the whole track to 0.12.
8. **Phone first.** Most views are on a phone speaker, often after starting muted. The first second must hook, and hits need mid-range content, not just sub.
9. **Measure every pass.** You can't hear, so analyze.py and the PNG are your ears and listen.py is a second opinion. Never claim "sounds great". Report the numbers and what the user should listen for.

## References

| File | Read when |
|---|---|
| `references/sonic-identity.md` | Step 2: palette catalogue, signature sounds, banned defaults, SOUND.md template |
| `references/spotting.md` | Step 3: cue hierarchy, music maps, sync and silence rules, what not to score |
| `references/music.md` | Step 4: model choice + prices, composition plans, prompt anatomy, picking, fit/extend recipes |
| `references/sfx.md` | Step 5: prompt anatomy, layering, alignment, pitch, round-robin, UI/transition vocabulary |
| `references/mix.md` | Steps 6–7: level targets, bus recipes, ducking, automation moves, session schema, reading the PNG |
| `references/master.md` | Steps 7–8: platform targets, QA thresholds, delivery formats |

## With any video tool

The input is a rendered video, so it works with every stack. Render picture without music or stock SFX (keep the voiceover if there is one), then run this skill on the render and mux the result.
- **Timeline marks:** export cut and event times from whatever made the video (Remotion `<Sequence from>` frames ÷ fps, HyperFrames `data-start`, an NLE marker list, a storyboard) into `audio/marks.json`.
- **Voiceover:** put each VO file on the `vo` bus at its start time; the bus processes it and keys the ducks.
- **Pipelines with their own audio step** (e.g. HyperFrames product-launch-video's library BGM and bundled SFX): set them to silent (`music: none`, no `sfx:` cues) and do audio here.

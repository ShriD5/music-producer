# sound-design

An agent skill that gives your videos produced audio instead of the same library track and whoosh pack every time. It works free by default and on any video stack.

Point your coding agent (Claude Code, Codex, Cursor, OpenCode, ...) at a rendered video. It decides what the film should sound like, spots the cuts, scores music to the picture, designs a sound for each moment, mixes everything in one acoustic space, masters to streaming loudness, and **measures the result**, because agents can't hear.

```
npx skills add ShriD5/sound-design -g
```

Then ask your agent: *"Do the sound for renders/launch.mp4"*.

## Why

Ask an agent for audio and you get the same thing every time: one stock bed, the same riser into a bass impact into a whoosh, flat levels, no mastering. Or it writes a synth track in numpy that sounds like every other synth track it has written. This skill replaces that with a post-production workflow:

1. **Sonic identity.** What does *this* product sound like? A ledger of past films blocks repeats: each new film has to differ on genre, tempo, key, lead instrument or signature sound.
2. **Spotting.** Detects cuts (including dark, low-contrast footage), suggests tempos that land on them, and renders a contact sheet so the agent sees what's on screen at every sync point.
3. **Score to picture.** A section plan whose boundaries are the cut times. Takes are analyzed for tempo, key, entrances, ending and plan adherence, then fitted: an entrance aligned to the reveal, the track's real ending spliced onto the logo, Rubber Band tempo conform, and local repaint of sections the model ignored.
4. **Designed SFX.** A hit hierarchy, layered transient + body + tail, round-robin variants, pitched to the score's key.
5. **Mix.** Clips land on their transient, not their file start. VO ducks the music with a speech-band carve, everything sits in one shared reverb room, and gain/filter automation adds drop-outs, pre-drop sweeps and air before the reveal.
6. **Master.** Glue compression, then a 4× oversampled lookahead true-peak limiter that iterates to the target (−14 LUFS / −1 dBTP by default). It names the clips causing heavy limiting.
7. **Measure.** Loudness, LRA, true peak, per-frame hit sync, VO-over-bed in the speech band, phone-speaker survival, mono fold-down, tonal balance, endings. You get a report plus a picture the agent reads. Gemini can optionally listen as a second opinion.

## Free or paid, your choice

| | free (default) | paid (`SOUND_DESIGN_TIER=paid`) |
|---|---|---|
| Music | [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5), local, MIT. ~4–5 min per 40 s take on an M2, seconds on a CUDA GPU | ElevenLabs Music v2.5 composition plans (sections locked to the cut) via fal or your ElevenLabs key; Lyria, MiniMax, Stable Audio via fal |
| SFX | CC0 recordings via [Openverse](https://openverse.org) (no key) or [Freesound](https://freesound.org) (free key), credits written for you | ElevenLabs SFX, Stable Audio, video-to-foley |
| Mix / master / analysis | local | local |
| Ears (optional) | Gemini Flash via OpenRouter, ~$0.005 per film | same |

A typical 40 s film costs **$0** on the free tier and **$0.60–2** on the paid one. Spend is logged per project.

## Requirements

- `ffmpeg` and [`uv`](https://docs.astral.sh/uv/). The scripts are uv single-file scripts, so their dependencies install themselves.
- Free local music needs ~10 GB of disk (`uv run scripts/setup.py ace`) and works best on Apple Silicon or an NVIDIA GPU.

```bash
uv run skills/sound-design/scripts/setup.py doctor   # what works, what each key would unlock
uv run skills/sound-design/scripts/setup.py ace      # free local music model (once)
```

Keys are read from env vars, then `./.env`, then `~/.config/sound-design/keys.env`:

```
FREESOUND_API_KEY=     # free, better SFX search
OPENROUTER_API_KEY=    # optional ears
FAL_KEY=               # paid tier
ELEVENLABS_API_KEY=    # paid tier, your own plan
SOUND_DESIGN_TIER=free
SOUND_DESIGN_HOME=~/.cache/sound-design   # model weights
```

## Works with any video tool

The input is a rendered video. Render picture without music (keep VO if you have it), and optionally export cut times into `audio/marks.json` (Remotion sequence frames, HyperFrames `data-start`, NLE markers). The skill then writes `renders/<name>.sound.mp4` (video stream copied), a 48 kHz/24-bit master, stems, and a report.

## Scripts

| script | does |
|---|---|
| `setup.py` | `doctor`, `ace` (install local music), `keys` |
| `ledger.py` | sonic-identity history so films don't repeat |
| `spot.py` | cuts, motion, tempo-to-picture, contact sheet |
| `music.py` | `gen` (any provider, one plan format), `analyze` (+ plan adherence), `fit`, `repaint`, `extend` |
| `sfx.py` | `gen` (libraries or generators), `variants` (round-robin), `video` (foley bed), `index` |
| `mix.py` | session → buses → room → master → mux, limiter hotspots |
| `analyze.py` | measured QA report + analysis.png |
| `listen.py` | optional Gemini critique / blind candidate comparison |

## Adding a provider

Providers live in `scripts/providers.py`: one registry entry (cost, route, kind) plus a fetch function returning audio bytes. Everything downstream (trim, level, crop, index, mix) is shared.

## Licenses

The code is MIT. The things it pulls in have their own terms:
- ACE-Step 1.5 is MIT.
- Openverse/Freesound recordings default to CC0. If you enable CC-BY, ship the generated `audio/CREDITS.md` attribution with your video.
- Paid providers' output is governed by their terms (fal, ElevenLabs).

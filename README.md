# music-producer

**A music producer for your coding agent.** Give Claude Code, Codex, Cursor or any agent a rendered video and it scores it to the cut, designs the sound effects, mixes, masters, and checks the result against real launch films. Free by default, works with any video stack.

```
npx skills add ShriD5/music-producer -g
```

Then ask your agent: *"Produce the audio for renders/launch.mp4"*.

## vs. hiring a music producer

| | a human producer | your agent + music-producer |
|---|---|---|
| Custom track for a 40 s launch film | typically hundreds of dollars and up | $0 on your machine, ~$1–2 with paid models |
| Turnaround | days, plus revision rounds | minutes; regenerate a section in place |
| Scored to your exact cut | yes | yes: section times come from the cut, hits land within a frame |
| Sound design, mix, master | often separate people | included, mastered to −13 LUFS and measured against real launch films |
| Taste | the real thing | AI music plus measured craft, and you pick the take by ear |

A great human producer still wins on taste. This takes your agent from "same stock loop on every video" to launch-film grammar in one run.

## There, fixed it

These top launch videos shipped with **no sound at all**. Four agents, each with only this skill and a $2 cap, scored one each: concept, music, designed SFX, mix and master.

| Film | What the agent made it sound like | QA | |
|---|---|---|---|
| [Linear: "Issue tracking is dead"](https://x.com/linear/status/2036502198062821842) | a cold, precise trailer pulse that multiplies with the issue glyphs until the grid whites out, holds its breath, then one decisive keystroke-and-boom … | -13.1 LUFS, 4/4 hits on the frame | [recipe](examples/linear-issue-tracking-dead) |
| [Cursor: Origin](https://x.com/cursor_ai/status/2089399057659596847) | Git hosting as a glitch record. A tight IDM / minimal tech-house track whose percussion is micro-edited keyboard clicks and commit "ticks", and whose … | -13.0 LUFS, 12/12 hits on the frame | [recipe](examples/cursor-origin) |
| [Notion: Dashboards](https://x.com/NotionHQ/status/2031098248941940790) | a felt-piano close-up that pulls back into a wide, confident neo-classical electronic groove, the way the film pulls from one menu item out to the bir… | -13.0 LUFS, 10/10 hits on the frame | [recipe](examples/notion-dashboards) |
| [Figma: Dev Mode in Codex](https://x.com/figma/status/2104994048381792487) | a warm, bouncy organic synth-pop record that gets built while you watch: plucked "shape" notes snap together into a groove the way frames turn into a … | -13.0 LUFS, 12/12 hits on the frame | [recipe](examples/figma-devmode-codex) |

Music cost $0.24–0.96 per film.

## What it does

Ask an agent for audio and you get the same thing every time: one stock bed, the same riser into a bass impact into a whoosh, flat levels, no mastering. Or it writes a synth track in numpy that sounds like every other synth track it has written. This skill gives it a producer's workflow:

1. **Sonic identity.** What does *this* product sound like? A ledger of past films blocks repeats: each new film has to differ on genre, tempo, key, lead instrument or signature sound.
2. **Spotting.** Detects cuts (including dark, low-contrast footage), suggests tempos that land on them, and renders a contact sheet so the agent sees what's on screen at every sync point.
3. **Score to picture.** A section plan whose boundaries are the cut times. Takes are analyzed for tempo, key, entrances, ending and plan adherence, then fitted: an entrance aligned to the reveal, the track's real ending spliced onto the logo, Rubber Band tempo conform, and local repaint of sections the model ignored.
4. **Designed SFX.** A hit hierarchy, layered transient + body + tail, round-robin variants, pitched to the score's key.
5. **Mix.** Clips land on their transient, not their file start. VO ducks the music with a speech-band carve, everything sits in one shared reverb room, and gain/filter automation adds drop-outs, pre-drop sweeps and air before the reveal.
6. **Master.** Glue compression, then a 4× oversampled lookahead true-peak limiter that iterates to the target (−13 LUFS / −1 dBTP for launch films). It names the clips causing heavy limiting.
7. **Measure against real launch films.** Tonal balance against a curve measured from real launch films (Arc, Figma, Framer, Notion, Raycast, Stripe), loudness, LRA, true peak, hit sync verified per layered moment, VO-over-bed, phone-speaker survival, mono fold-down, endings. You get a report plus a picture the agent reads.
8. **Human ears decide quality.** A blind, loudness-matched listening page (candidates mixed with real reference films) so you pick by ear in a minute. AI listeners are only used to spot problems: in testing, Gemini ranked a real Arc launch film last.

## Free or paid, your choice

| | free (default) | paid (`MUSIC_PRODUCER_TIER=paid`) |
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
uv run skills/music-producer/scripts/setup.py doctor   # what works, what each key would unlock
uv run skills/music-producer/scripts/setup.py ace      # free local music model (once)
```

Keys are read from env vars, then `./.env`, then `~/.config/music-producer/keys.env`:

```
FREESOUND_API_KEY=     # free, better SFX search
OPENROUTER_API_KEY=    # optional ears
FAL_KEY=               # paid tier
ELEVENLABS_API_KEY=    # paid tier, your own plan
MUSIC_PRODUCER_TIER=free
MUSIC_PRODUCER_HOME=~/.cache/music-producer   # model weights
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
| `sfx.py` | `gen` (libraries or generators), `sub` (designed sub drop in key), `tune` (pitch takes to the score's key), `variants` (round-robin), `video` (foley bed), `index` |
| `mix.py` | session → buses → room → master → mux, limiter hotspots |
| `analyze.py` | measured QA report + analysis.png |
| `pack.py` | blind, loudness-matched listening page (candidates + real reference films) for the human to pick |
| `listen.py` | optional Gemini critique (spots problems; not a quality judge) |

## Adding a provider

Providers live in `scripts/providers.py`: one registry entry (cost, route, kind) plus a fetch function returning audio bytes. Everything downstream (trim, level, crop, index, mix) is shared.

## Licenses

The code is MIT. The things it pulls in have their own terms:
- ACE-Step 1.5 is MIT.
- Openverse/Freesound recordings default to CC0. If you enable CC-BY, ship the generated `audio/CREDITS.md` attribution with your video.
- Paid providers' output is governed by their terms (fal, ElevenLabs).

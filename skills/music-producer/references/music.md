# Music: scoring to picture

## Which model

| `--provider` | Route | Price | Use it for |
|---|---|---|---|
| `ace` (free default) | local ACE-Step 1.5 (MIT) | $0 | Any genre, honours BPM and key well, instrumental. Takes the plan as a caption, so the arc is loose: enforce sections with `repaint` and mix automation. ~4–5 min per 40 s take on an M-series Mac (8 steps), seconds on CUDA. `--lm auto` uses the 0.6B planner only with >= 24 GB RAM; `--lm acestep-5Hz-lm-0.6B` forces it (CPU offload kicks in on 16 GB). In testing the planner gave more arc but a more generic sound, so on small machines make take 2 a planner take and compare. |
| `eleven` (paid default) | fal `elevenlabs/music/v2.5`, or ElevenLabs direct with your key | $0.60/min on fal; your plan's credits direct | **Structure locked to the edit.** Up to 30 sections with exact ms durations and per-section styles. Best when the drop must land on a frame. |
| `lyria` | fal `google/lyria-3.5` | $0.10/gen | Rich, natural arrangements and live-instrument genres (jazz, soul, orchestral, world). Returns ~2 min whatever you ask: fit afterwards. |
| `lyria3pro` | fal `fal-ai/lyria3/pro` | $0.08/gen | Lyria alternative with a different character. Cheap second opinion. |
| `minimax` | fal `minimax/music-3` | $0.002/s | Good pop/electronic production; supports duration. |
| `stable` | fal Stable Audio 3 medium | $0.04/gen | Textures, ambient beds, loops, drones; negative prompts; up to 380 s. Also powers `music.py extend`. |
| `sonilo` | fal video-to-music | $0.009/s | Watches the video and scores it. A **candidate generator** when you're stuck, rarely the final pick. |

Generate **2 candidates from your main provider + 1 from a contrasting one** when budget allows. Pick with `analyze` + `listen.py --compare`. Never ship the first take unexamined.

### Free tier (ACE-Step) workflow

1. `gen --plan` with BPM and key in the plan (ACE-Step follows both closely; measured 120.0 BPM when asked for 120).
2. `analyze --plan`: expect weak section contrast (the caption describes the arc, but it isn't time-locked).
3. Fix the arc where it matters: `repaint` the quiet section or the pre-reveal stretch with a direct prompt, then re-analyze. Repaint keeps the rest of the take.
4. Do the rest in the mix: drop-outs, filter sweeps, swells and the air before the reveal are automation anyway.
5. Fit with `--hit/--src` so the strongest entrance lands on the reveal, and `--end-hit` for the button.

## The plan file (every provider; exact sections on eleven)

`audio/music/plan.json`. `until` is the absolute **output** time where the section ends, so sections are cut times:

```json
{
  "styles": ["live funk", "slap bass", "tight dry drum kit", "clavinet", "horn stabs", "104 bpm", "E dorian",
             "great production quality", "instrumental"],
  "negative": ["vocals", "edm drop", "supersaw", "riser", "corporate"],
  "chunks": [
    {"name": "Intro", "until": 4.0, "styles": ["solo clavinet riff", "room mic"],
     "text": "{starts immediately on beat 1, no fade in, riff alone}"},
    {"name": "Build", "until": 9.5, "styles": ["bass joins", "hi-hat 16ths"],
     "text": "{tension, drums enter halfway, last bar drops to just the clav}"},
    {"name": "Groove", "until": 26.0, "styles": ["full band", "horn stabs on 2 and 4"], "adherence": "high",
     "text": "{full band hits on beat 1, confident groove, horn stab accents}"},
    {"name": "Breakdown", "until": 30.0, "styles": ["bass and clav only"], "text": "{strip back, half-time feel}"},
    {"name": "Button", "until": 34.0, "styles": ["full band unison hit"],
     "text": "{one big unison hit on beat 1 then let it ring out, no more drums}"}
  ]
}
```

Rules that matter:
- **Chunk ≥ 3 s.** Shorter moments (a 0.5 s drop-out) go inside a chunk's `{direction}` and are enforced later by automation in the mix.
- **First chunk's styles set the whole track.** Put genre, tempo, key, instrumentation and "great production quality" in the global `styles`. Use per-chunk styles only for what changes.
- **Directions in braces** describe arrangement events: entrances, drop-outs, fills, "hit on beat 1", "ring out".
- The total plan length = the film length (or + up to 2 s if the button rings past the end, trimmed by fit).
- Put tempo and key in the styles so the analyze step can confirm them. If the analyzed BPM is off, conform with `fit --bpm`.
- Seeds: `--n 2` uses different seeds. Same seed + same plan reproduces a take.
- `force_instrumental` is rejected together with a plan; the script leaves it out. Keep "instrumental" in styles and "vocals" in negative.

### What the plan actually controls (measured, Oct 2026)

- **Tempo: reliable.** Asked 120, got 120.0.
- **Boundaries: mostly.** Big entrances usually land on the planned boundary, but not on every take (one take entered a bar early).
- **Key: often ignored.** Asked B-flat major, got D and G. Always tune signature/tonal SFX to the **analyzed** key, not the requested one.
- **Section dynamics: loose.** "Drums stop, nearly silent" sections often stay full. Enforce quiet sections with mix automation (gain + lpf) instead of regenerating.

So always run `music.py analyze <takes> --plan audio/music/plan.json`. Pick the take with the largest positive **step at start** on your A-moments (reveal, button), not the best section averages.

## Prompt anatomy (lyria / minimax / stable)

`[genre + era], [tempo] BPM, [key/mode], [lead instrument + playing style], [rhythm section], [texture/space], [arc over time], [production adjectives], instrumental, no vocals`

Good: `Late-70s Philly soul instrumental, 104 BPM, E dorian, clavinet riff and slap bass lead, tight dry live drums, warm tape saturation, horn stabs, starts immediately on a strong downbeat, builds to a full-band groove at 10 s, big unison hit and ring-out at the end, crisp modern mix, instrumental, no vocals`

Bad: `upbeat energetic modern tech music for a product launch`. That's the prompt that produced every launch video so far.

Production adjectives that help: `crisp modern mix`, `wide stereo`, `punchy transients`, `analog warmth`, `dry close-mic`, `big room`, `sidechained`, `tape saturation`, `lo-fi`. Name **instruments and playing techniques**, not feelings.

## Picking a take

Run `music.py analyze` on each. Prefer the take that:
1. starts strong in its first second (energy list from analyze: first value within ~6 dB of the median),
2. has a clear entrance near where your reveal is, or one you can align with `--hit/--src`,
3. has a **natural ending** (`ending: natural`) if you need a ring-out,
4. matches the planned BPM/key (±2 BPM),
5. wins `listen.py --compare` for identity and artifacts (warble, smeared drums, metallic cymbals). Treat Gemini as a tie-breaker. It inflates scores and will "hear" events the brief asks for, so structure is decided by `analyze --plan`.

Lyria returns ~2 min tracks whatever you ask for. Pick the best 40 s window with `fit --hit/--src` (entrances) and `--end-hit` (its real ending, `final_hit`).

## Conforming (`music.py fit`)

- **Align an entrance to the reveal:** `--hit 9.5 --src <entrance downbeat from analyze>`. The source is shifted so that event plays at 9.5 s.
- **Button ending:** `--end-hit 34.0 [--end-src auto]` splices the track's own final hit onto the logo frame and lets its real tail ring. The splice is hard by design. Place the A-hit SFX on it to mask the seam.
- **Tempo to picture:** `--bpm <spot.py candidate>`. Rubber Band stretch. Stay within ±8 %.
- **Too short:** `music.py extend file --after N` (Stable Audio outpainting). The model re-encodes the source and leaves ~1 s of near-silence before resuming on the beat grid. The script keeps your original untouched, skips that gap in whole beats and crossfades. Re-analyze and look at the energy list around the seam. If there's still a hole, extend from an earlier downbeat (trim the source first) or regenerate longer.
- `--fin` only if the take truly starts on a weak upbeat; default is 0 (start on the downbeat).
- Drop-outs, filter sweeps and swells are **mix automation** (see mix.md), not edits to the music file.

## Score + SFX relationship

On an A-hit, the score should hit too (unison hit, drop entrance, or a stop). The SFX adds texture and the signature, not the whole impact. If the score is busy where an A-hit lands, automate a 2–4 dB dip in the music 50 ms before the hit and release over 300 ms, or cut to air.

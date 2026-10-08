---
name: dj-mixtape
description: Build continuous DJ mixes from existing recordings, with source intake, cue preparation, sequencing, designed transitions, editable timelines and verified audio exports. Use for DJ sets and continuous mixtapes; original songwriting and beat reconstruction are separate workflows.
---

# DJ Mixtape

Deliver a continuous audio set, an editable timeline and a timestamped tracklist. Preserve the user's genre, energy, track count or duration contract, and source choices. Use an offline audio workflow unless the user requests a live controller performance. Do not install a different DAW merely because it appears in a reference.

## Working contract

Resolve audience, genres, track count or duration contract, and source policy from the conversation. A count-defined set has no implicit time target; select musical sections first, then calculate the resulting duration. Ask only for preferences that materially affect selection and progress on intake meanwhile. Keep sources, analysis, prepared media, outputs and receipts in a dedicated project directory outside this skill. Do not publish the set or upload source recordings unless requested.

Use six modules, reading the linked detail as needed:

1. [Crate curation](references/curation.md): choose recordings and alternatives with source URLs and uploader evidence.
2. [Track preparation](references/preparation.md): inspect delivery audio, estimate grid/key, select cue candidates and retain provenance.
3. [Set sequencing](references/sequencing.md): design the energy arc and compute audible duration after overlaps and stretching.
4. [Transition design](references/transitions.md): choose a technique for each adjacency, rather than uniformly crossfading every pair.
5. [Timeline construction](references/construction.md): create individual media items, automation, cue markers and source routing.
6. [Quality and delivery](references/quality.md): inspect the actual candidate's audio, source resolution and playback with current hashes.

## Reusable helpers

- `scripts/intake.py discover --queries QUERY_JSON --output CANDIDATES_JSON --yt-dlp PATH`: bounded YouTube search returning candidates for selection, not automatic verification of official status.
- `scripts/intake.py download --catalog CATALOG_JSON --root PROJECT_DIR --yt-dlp PATH`: downloads selected URLs, decodes stereo WAV using the actual delivery extension and writes sanitized provenance.
- `scripts/analyze.py --root PROJECT_DIR`: analyzes source WAVs. Requires NumPy, soundfile and librosa; Beat This is optional. Predictions are not verified cues.
- `scripts/render.py --plan PLAN_JSON --root PROJECT_DIR`: constructs prepared clips, transition envelopes, effect layers and a streaming mix with FFmpeg; exports an editable REAPER audio project and explicit plan. Requires NumPy, soundfile and SciPy.
- `scripts/verify.py --plan PLAN_JSON --root PROJECT_DIR`: checks actual audio, creates a listening export and timestamped tracklist. Requires NumPy and soundfile.
- `assets/player/`: streaming player template using one media element, not full-length decoded stems.

Find executables through arguments or PATH. Keep credentials and signed delivery URLs out of receipts. The local mix request authorizes source intake within the user's stated source choice, not unrelated account changes or public hosting.

## Completion standard

Retain source mappings, cut offsets, rates, overlaps, gains and effect parameters. State which processing is baked and which remains editable. A generated REAPER project is not a REAPER-rendered or reopened project unless that was actually executed. Respect the user's execution environment; Docker is not required.

Treat separated stems and detected beat/key/vocal activity as estimates. Measurements are not musicality scores. Give playable full audio, project, tracklist and material limitations. A playlist, several transition clips or an analysis report alone does not complete a requested continuous set.

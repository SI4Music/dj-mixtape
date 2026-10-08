# DJ Mixtape

A Codex skill for building continuous hiphop, trap, drill and other DJ sets from existing recordings. It covers source selection, cue preparation, sequencing, designed transitions, native audio rendering, an editable REAPER timeline and a full-length streaming player.

The set can be defined by a **track count** or an explicit duration. For a count-defined set, choose the musical entries and exits first and calculate duration afterward. The skill does not divide a time budget equally among songs or make a long closer absorb a remainder.

## Install

Clone into the Codex skills directory on a machine where `dj-mixtape` is not already installed:

```sh
gh repo clone toreleon/dj-mixtape ~/.codex/skills/dj-mixtape
```

Alternatively, clone the repository elsewhere and copy the directory containing `SKILL.md` into your Codex skills directory. For a custom `CODEX_HOME`, use its `skills/` directory. Reload skill discovery or start a new Codex session as needed.

Example request:

> Use $dj-mixtape to build a continuous 20-track Vietnamese hiphop set with high-energy trap/drill. Choose musical entries and exits without a duration target. Deliver the full audio, editable timeline and timestamped tracklist.

## Runtime

The native helpers were used with Python 3.12. Install FFmpeg and ffprobe through your usual system package manager, then create an environment outside the installed skill:

```sh
python3.12 -m venv ~/dj-runtime
~/dj-runtime/bin/python -m pip install -r ~/.codex/skills/dj-mixtape/requirements.txt
```

The pinned Python dependencies match the base environment used for the workflow. Beat This is optional for neural beat/downbeat estimates; without it, analysis uses librosa with assumed downbeats. Demucs was used in project-specific transition preparation, but stem separation is not bundled into these generic helpers. Model weights and recordings are not part of this repository.

An installed REAPER application and Docker are not required. The helper renders with native FFmpeg and writes an RPP project; exporting that file does not mean REAPER opened or rendered it.

## Workflow and files

`SKILL.md` is the agent entry point. `references/` contains curation, preparation, sequencing, transition theory, timeline construction and delivery guidance. `agents/openai.yaml` supplies Codex UI metadata. `assets/player/` is a local player template with chapter buttons and seekable HTTP Range streaming.

Keep each mix project outside the skill directory. A project's `catalog.json` uses a `tracks` array; selected tracks provide `id`, `artist`, `title` and `url`. The intake helper accepts individual YouTube watch URLs and writes delivery provenance and stereo 44.1 kHz float WAVs. Keep recording selection and playback rights within the user's requested source policy.

Run the helpers from any working directory using absolute paths:

```sh
~/dj-runtime/bin/python ~/.codex/skills/dj-mixtape/scripts/intake.py download \
  --catalog /path/to/mix/catalog.json --root /path/to/mix \
  --yt-dlp ~/dj-runtime/bin/yt-dlp

~/dj-runtime/bin/python ~/.codex/skills/dj-mixtape/scripts/analyze.py \
  --root /path/to/mix

# Design and save the arrangement as plan.json before rendering.
~/dj-runtime/bin/python ~/.codex/skills/dj-mixtape/scripts/render.py \
  --root /path/to/mix --plan /path/to/mix/plan.json

~/dj-runtime/bin/python ~/.codex/skills/dj-mixtape/scripts/verify.py \
  --root /path/to/mix --plan /path/to/mix/plan.json

~/dj-runtime/bin/python /path/to/mix/listen/serve.py --port 0
```

For bounded discovery, use `intake.py discover --queries QUERIES_JSON --output CANDIDATES_JSON`; queries are an array of objects with `id` and `query`. Discovery returns candidates for deliberate selection. It does not verify official upload status or build an arrangement automatically.

The arrangement schema is described in [construction](references/construction.md). Source offsets are source seconds; positions and fades are output seconds. `playrate` is the output tempo divided by the source tempo, and output excerpt length is `source_length / playrate`. Use the source sample rate in the plan; the intake workflow uses 44100 Hz. Bridges must already be aligned to the intended output tempo. Optional dynamic normalization is available when measured source peaks make uniform gain unsuitable.

Outputs include:

- `output/mix.wav` and `listen/mix.mp3`: the complete continuous set.
- `output/mixtape.rpp` and `media/`: individual prepared recordings and effect layers. Keep these directories together. Processing is baked; item positions and track/master gains remain editable.
- `TRACKLIST.md`, `plan.json`, `layers.json` and receipts: timestamps, source mapping, processing parameters and verification evidence.
- `listen/`: full-length player on loopback, with one media element for the set.

The generated RPP has a static 140 BPM project grid. Audio rates are baked per excerpt; the helper does not write a tempo envelope. Source recordings and the plan allow prepared media to be regenerated when changing baked cuts or processing.

## Verification and musical review

The workflow checks selected clip frame counts, actual output duration, finite samples, sample/true peaks, unexpected silence, layer sums at handoffs and REAPER media paths/positions. The installed skill was exercised on a 20-track set; the helper revision fixes a timestamp-based trim issue after dynamic normalization by ending clips at their selected sample count.

Beat, key, cue and separated-stem observations are estimates. Musical phrasing, vocal coherence and momentum require listening assessment; a technical PASS is not a listening approval. [Transition thinking](references/transition-thinking.md) records source-grounded ideas from DJ Jazzy Jeff, Craze, A-Trak, Laidback Luke and other practitioners, with attribution limits.

This repository contains reusable instructions, code and player assets. Mix projects, downloaded recordings, model caches and generated media belong in separate project directories.

# Vocal selection and interludes

Read when phrasing is technically aligned but the singer/rapper handoff feels forced. Judge the outgoing performance and the first incoming statement, not a whole-track energy tag or the artist's reputation.

## Describe the actual voices

Keep lyrics/phrase completion separate from delivery: projected versus intimate tone, consonant attack, rap density versus sustained notes, accent placement/swing, register, doubles/ad-libs and room/reverb. Describe the intended trajectory: hold, lift, ease or reset. A louder master, faster tempo or brighter spectrum cannot establish an equally forceful performance. High-energy selection can include relaxed voices if the groove and context make their entrance purposeful.

Audition several entry statements rather than blindly taking the first full-beat cue. Preserve pickups relative to the following downbeat; do not start on the downbeat when the word began before it. Select a complete statement with the right delivery. Where neither a new cue nor a short bridge makes an adjacency convincing, consider an alternate order or recording within the user's selection contract.

`scripts/vocal_audit.py --vocal VOCAL_WAV --reference ALIGNED_ORIGINAL_WAV --start SECONDS --duration SECONDS --output JSON` reports relative vocal level, activity, envelope peaks and spectral descriptors, with 4-second windows. Inputs must share time origin, sample rate and processing gain; keep model stems on the original mix scale. It does not separate audio or classify vocal energy. Use descriptors to locate contrast and audition candidates, never to auto-sort singers or infer emotion. Envelope peaks are not syllables; activity is not speech detection. Separated reverb/ad-libs may remain after the lead ends, and instrumental leakage can look like vocal attack.

Research on speech/nonverbal voices links aspects of intensity and voice quality with perceived activation, but this does not validate a rap/DJ energy detector. Singer baselines and production matter. Spectral centroid alone does not establish tense versus breathy delivery. [Voice quality experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC7592904/), [speaker-relative arousal framework](https://pmc.ncbi.nlm.nih.gov/articles/PMC4334478/).

## Optional lyric timing with ASR

Honor the user's provider/model choice; do not silently substitute another recognizer. External transcription requires authorization for that service/audio. Keep credentials in an environment variable or hidden input, out of commands, logs, receipts, browser code and Git. Start with bounded probes around candidate cues, preserving exact source offsets; retain request/model metadata and uploaded-audio hashes.

When Deepgram is selected, its prerecorded API returns word offsets and confidence. Nova-3 supports `language=vi`; verify current model/language support when executing. Map `source_time = probe_source_start + response_time`, then convert through the actual playback rate for the set. Check cue-inside-word and likely clause boundaries alongside the audio. Nonrecognition is not proof of silence; inspect the original mix if a separated vocal estimate fails. Vietnamese-only recognition can miss English ad-libs. An utterance boundary is not automatically a song phrase, confidence is not correctness, and ASR does not rate vocal effort. Do not publish transcripts with the skill. [Prerecorded API](https://developers.deepgram.com/docs/pre-recorded-audio), [models/languages](https://developers.deepgram.com/docs/models-languages-overview).

## Design a bridge with a role and payoff

An interlude is a small arrangement: a departure, connection and arrival. Work backward from the incoming vocal statement/full groove. Its length follows those phrases and the listening result, not a universal bar count. Keep the lead and bass owner explicit at each point.

| Situation | Candidate | What must be checked |
|---|---|---|
| Outgoing lead remains active at the planned cut | Continue its natural vocal tail over an incoming instrumental entrance | Complete the sentence; incoming lead waits for a complete entry, not an arbitrary fade-in halfway through a word |
| Incoming recognizable pickup can connect two voices | Preview the original pickup over outgoing percussion or a vocal-free pocket, then bring its complete mix | Respect the pickup-to-downbeat offset; avoid two independent foreground lines |
| Delivery becomes more relaxed while beat remains strong | Short instrumental handoff with a retained groove and a purposeful new vocal statement | Avoid adding a long empty intro or compensating with louder vocals |
| Delivery becomes denser/more projected | Establish incoming rhythm underneath a completed outgoing statement, then exchange bass and lead | Do not suppress the opening consonants or double 808 fundamentals |
| Tempo/feel changes substantially | Finish the lead, shorten tonal overlap and deliberately reset the pulse before the new statement | Keep unrelated subdivisions out of a long blend; a neutral texture is not a beatmatch |
| Melody or vocal separation sounds poor | Use a complete original passage and a clean cut, or choose another cue | Extra echo can expose rather than hide stem artifacts |

Use original continuous stem passages before word chopping unless a recognizable, complete fragment has been reviewed. Call-and-response needs an actual relationship and enough space; do not invent it from two unrelated lyrics. A texture or drum loop alone may prepare a groove but does not bridge singer delivery automatically. Effects should mark a decision already made in the arrangement.

Jazzy Jeff's interview supports using isolated voices, instrumentals and replacement drums to reshape the arrangement; specific recipes here are our inference. [Interview](https://www.digitaldjtips.com/jazzy-jeffs-3-tips-for-djing-with-stems/). Ean Golden's phrasing lesson emphasizes the outgoing payoff and incoming section, including short hiphop introductions. [Lesson](https://djtechtools.com/2009/01/26/phrasing-the-perfect-mix/). Serato documents independent stem mutes and vocal echo; an echo is a control, not a completed musical design. [Controls](https://support.serato.com/hc/en-us/articles/5700921209615-Using-Stems).

## Verify in context

Render A/B of the same pair with comparable pre-transition loudness and enough complete vocal statements before/after. Retain the old candidate. Check pickup alignment, processing gain, residual reconstruction, consonant clipping, two-lead overlap, bass exchange and stem artifacts. Make the isolated voice and accompaniment available for short diagnostic listening where useful. Record whether lyrical completion, vocal delivery and groove were actually auditioned; technical checks do not confirm a smooth set. Keep sources and media outside the skill/repository.

# Editable timeline construction

Use the user's available environment. This helper uses native FFmpeg; Docker and a installed DAW are unnecessary. It prepares individual tempo-corrected excerpts, applies explicit fades and filtered transition layers, then streams the sum to disk. The exported REAPER project contains each processed segment/effect as an individual item, not the flattened master pasted into one track. Original recordings and exact processing parameters remain available.

Plan JSON: `title`, `duration`, `sample_rate`, `master_gain_db`, `segments`, `transitions`. Each segment has `id`, `artist`, `title`, `file` relative to project root, `source_start`, `source_length`, `playrate`, `position`, `gain_db`, `fade_in`, `fade_out`, optional `filter_out` (last output seconds highpassed), and optional `echo` (`source_offset` relative to prepared excerpt, `source_length`, `position` on mix timeline, `delay`, `decay`, `gain_db`). Rate is source/output; item length is source_length/playrate. Fades/position are output seconds.

Keep original filenames unambiguous and paths relative to project. Prepared clip gain/fades/filter/rate and echoes are baked; item placement, source selection and track gain remain editable. Regenerate prepared media to change baked decisions. The plan is the reproducible control surface.

Optional `bridges` contain `name`, `file`, `source_start`, `source_length`, integer `repeats`, `position` and `gain_db`. The helper repeats a short stereo slice, filters low frequencies and applies de-click fades. Pre-align a bridge slice to the intended output tempo; this path does not apply additional stretching. When the slice comes from separated drums, retain model/source provenance and label it as an estimate.

Bridge `highpass_hz`, `fade_in` and `fade_out` optionally control its cutoff and output-second envelopes (defaults 150 Hz, 0.03 s, 0.12 s). A bridge can sit underneath an outgoing phrase as preparation; it need not add time between songs.

Segment `normalization: dynamic_loudnorm` optionally constrains source peaks while targeting clip loudness before the usual gain/fades. Use only when actual source/entry measurements warrant dynamic processing; disclose it and audition dynamics. Default normalization remains uniform gain. The per-segment render receipt records the chosen mode.

Do not claim the project was opened or rendered in REAPER merely because a syntactically valid RPP was written. Label FFmpeg as the render engine. If REAPER is present, reopen a focused project and verify source/rate/fade resolution. Keep application installation separate from routine rendering.

Use disk/block processing for hour-long audio; allocating a dense array per full-length track is unnecessary. The player should use HTTP Range for seekable streaming. Deliver a saved plan and individual prepared media together with the project.

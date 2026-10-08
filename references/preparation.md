# Track preparation

Estimate tempo from coherent pulse regions and examine phase residuals. A global fit across detector subdivision changes can return a plausible but wrong BPM. Retain half/double-time counting explicitly. A detected downbeat is not automatically a good entry or a section boundary: inspect whether the incoming phrase has drums/bass, a vocal pickup or a long cold intro.

Decode original delivery to consistent stereo floating-point WAV, preserving codec overshoots until clip gain is applied. Integer decode can introduce additional hard clipping before mixing. Retain the original download and sanitized metadata. Measure chosen excerpts separately; source-wide loudness may include video dialogue.

Estimate tempo from active audio; half/double-time labels can be equivalent. A precise BPM does not establish the first downbeat. Retain beat/downbeat arrays and candidate phrase cues. Preserve microtiming and avoid indiscriminate quantization. Key predictions are advisory for sparse/bass-heavy passages.

Find phrase boundaries around intros/hooks/breaks/outros; trim video-only silence and avoid starting mid-word. Where direct listening is unavailable, label cue predictions honestly. Use short separation probes only for concrete blend decisions; full-track separation is unnecessary for a cut. Do not normalize separated stems independently.

Reference: [Serato beatgrids](https://support.serato.com/hc/en-us/articles/360001274936-Beatgrids).

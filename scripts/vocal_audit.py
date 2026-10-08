#!/usr/bin/env python3
"""Describe aligned vocal estimates; does not infer singer emotion or DJ energy."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import soundfile as sf
from scipy.signal import find_peaks


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def describe(vocal, reference, sr):
    """40 ms overlapping frames; level gate is activity, not voiced-speech detection."""
    size, hop = round(.04 * sr), round(.02 * sr)
    n = min(len(vocal), len(reference))
    if n < size:
        return {'insufficient_audio': True}
    # Stereo power avoids cancellation when a doubled vocal is out of phase.
    vf = np.lib.stride_tricks.sliding_window_view(vocal[:n], size, axis=0)[::hop]
    rf = np.lib.stride_tricks.sliding_window_view(reference[:n], size, axis=0)[::hop]
    power = np.mean(vf * vf, axis=(1, 2))
    ref_power = np.mean(rf * rf, axis=(1, 2))
    levels = 10 * np.log10(power + 1e-24)
    gate = max(-55., float(np.percentile(levels, 90)) - 18.)
    active = levels > gate
    result = {
        'duration_seconds': n / sr,
        'activity_gate_dbfs': gate,
        'estimated_active_fraction': float(np.mean(active)),
        'vocal_rms_dbfs': float(10 * np.log10(np.mean(vocal[:n] ** 2) + 1e-24)),
        'reference_rms_dbfs': float(10 * np.log10(np.mean(reference[:n] ** 2) + 1e-24)),
        'active_vocal_to_reference_db': None,
        'active_spectral_centroid_hz': None,
        'active_hf500_ratio_db': None,
        'envelope_peaks_per_second': None,
        'active_level_p90_p10_db': None,
        'crest_db': None,
    }
    if not np.any(active):
        return result
    spectrum = np.mean(np.abs(np.fft.rfft(vf[active] * np.hanning(size), axis=-1)) ** 2, axis=1)
    freq = np.fft.rfftfreq(size, 1 / sr)
    band = (freq >= 80) & (freq <= 8000)
    lo, hi = (freq >= 80) & (freq <= 500), (freq > 500) & (freq <= 8000)
    centroid = np.sum(spectrum[:, band] * freq[band], axis=1) / (np.sum(spectrum[:, band], axis=1) + 1e-24)
    ratio = 10 * np.log10((np.sum(spectrum[:, hi], axis=1) + 1e-24) / (np.sum(spectrum[:, lo], axis=1) + 1e-24))
    envelope = np.maximum(levels, gate)
    peaks, _ = find_peaks(envelope, prominence=3., distance=max(1, round(.10 * sr / hop)))
    peaks = peaks[active[peaks]]
    result.update({
        'active_vocal_to_reference_db': float(np.median(10 * np.log10((power[active] + 1e-24) / (ref_power[active] + 1e-24)))),
        'active_spectral_centroid_hz': float(np.median(centroid)),
        'active_hf500_ratio_db': float(np.median(ratio)),
        'envelope_peaks_per_second': len(peaks) / (n / sr),
        'active_level_p90_p10_db': float(np.percentile(levels[active], 90) - np.percentile(levels[active], 10)),
        'crest_db': float(20 * np.log10(np.max(np.abs(vocal[:n])) / (np.sqrt(np.mean(vocal[:n] ** 2)) + 1e-24) + 1e-24)),
    })
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vocal', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True, help='Time-aligned original mix, at the same gain and sample rate')
    p.add_argument('--start', type=float, default=0)
    p.add_argument('--duration', type=float, required=True)
    p.add_argument('--window', type=float, default=4)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    vi, ri = sf.info(a.vocal), sf.info(a.reference)
    if vi.samplerate != ri.samplerate:
        p.error('Input sample rates must match; align and resample before auditing')
    if a.start < 0 or a.duration <= 0 or a.window <= 0:
        p.error('Start must be nonnegative; duration and window must be positive')
    sr = vi.samplerate
    first, count = round(a.start * sr), round(a.duration * sr)
    if first + count > min(vi.frames, ri.frames):
        p.error('Selected interval extends past an input')
    v, _ = sf.read(a.vocal, start=first, frames=count, always_2d=True)
    r, _ = sf.read(a.reference, start=first, frames=count, always_2d=True)
    if not np.isfinite(v).all() or not np.isfinite(r).all():
        p.error('Input contains non-finite samples')
    result = {
        'vocal_file': str(a.vocal), 'reference_file': str(a.reference),
        'vocal_sha256': digest(a.vocal), 'reference_sha256': digest(a.reference),
        'sample_rate': sr, 'start_seconds': first / sr, 'selected_frames': count,
        'method': 'RMS-gated 40 ms spectra and 3 dB envelope peaks; no speech or emotion model',
        'limitations': 'Separation leakage, reverb, doubles, mastering and singer baseline affect these descriptors. Envelope peaks are not syllable counts. Gate activity is not speech detection. Brightness is not vocal effort.',
        'perceptual_energy_rating': None, 'listening_review': None,
        'overall': describe(v, r, sr), 'windows': [],
    }
    step = max(1, round(a.window * sr))
    for i in range(0, count, step):
        result['windows'].append({'start_seconds': (first + i) / sr, **describe(v[i:i+step], r[i:i+step], sr)})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(a.output), 'windows': len(result['windows']), 'perceptual_energy_rating': None}))


if __name__ == '__main__':
    main()

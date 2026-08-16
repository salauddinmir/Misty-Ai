"""Audio feature encoder.

Extracts spectral band-energy features from raw audio samples using only
NumPy (no heavy model dependency). A production-grade backend (e.g.
Whisper embeddings or a pretrained CNN) can be plugged in later by
subclassing ``ModalityEncoder``.

Feature layout (total ``feature_size`` = 64 by default):
- 1  : RMS energy (volume)
- 1  : zero-crossing rate
- 1  : spectral centroid (normalized)
- 1  : spectral flatness
- 16 : mel-like log band energies (log-spaced frequency bands)
- 16 : band energy standard deviation across time frames
- 28 : MFCC-free mel-ish energy snapshot at segment midpoints (14 frames
        x 2 statistics: energy + dominant band)

Inputs:
- ``np.ndarray`` of shape (N,) raw PCM samples in [-1, 1] (mono)
- ``(samples, sample_rate)`` tuple — ``sample_rate`` is used for the
  frequency axis of the spectral features
"""

import numpy as np

from brain.perception.encoder import ModalityEncoder


class AudioEncoder(ModalityEncoder):
    """Encode raw PCM audio into a 64-dimensional feature vector."""

    modality = "audio"
    feature_size = 64
    n_bands = 16
    n_frames = 14

    def _extract(self, raw) -> np.ndarray:
        if isinstance(raw, tuple) and len(raw) == 2:
            samples, sample_rate = raw
            sample_rate = float(sample_rate)
        elif isinstance(raw, np.ndarray):
            samples, sample_rate = raw, 16000.0
        else:
            raise TypeError(f"Unsupported audio input type: {type(raw)}")

        samples = np.asarray(samples, dtype=np.float64).flatten()
        if sample_rate <= 0.0:
            sample_rate = 16000.0
        return self._features(samples, sample_rate)

    def _features(self, samples: np.ndarray, sample_rate: float) -> np.ndarray:
        eps = 1e-10

        # Global statistics
        rms = float(np.sqrt(np.mean(samples**2) + eps))
        zcr = float(np.mean(np.abs(np.diff(np.sign(samples)))))
        spectrum = np.abs(np.fft.rfft(samples))
        freqs = np.fft.rfftfreq(samples.size, d=1.0 / sample_rate)
        centroid = float(np.sum(freqs * spectrum) / max(np.sum(spectrum), eps)) / (sample_rate / 2.0)
        log_spectrum = np.log(spectrum + eps)
        flatness = float(np.exp(np.mean(log_spectrum)) / max(np.exp(np.mean(np.log(np.abs(samples) + eps))), eps))
        flatness = min(flatness, 1.0)

        # Log-spaced band energies (average over whole signal)
        lo = np.log(max(freqs[1], eps))
        hi = np.log(max(freqs[-1], eps))
        edges = np.exp(np.linspace(lo, hi, self.n_bands + 1))
        band_mean = np.zeros(self.n_bands, dtype=np.float64)
        band_std = np.zeros(self.n_bands, dtype=np.float64)
        chunk = max(samples.size // self.n_frames, 1)
        frame_energies = np.zeros((self.n_frames, self.n_bands), dtype=np.float64)
        for i in range(self.n_frames):
            frame = samples[i * chunk : (i + 1) * chunk]
            if frame.size < 16:
                continue
            spec = np.abs(np.fft.rfft(frame))
            for b in range(self.n_bands):
                sel = spec[(freqs[: spec.size] >= edges[b]) & (freqs[: spec.size] < edges[b + 1])]
                e = float(np.mean(np.log(sel + eps))) if sel.size else -10.0
                frame_energies[i, b] = e
        band_mean = frame_energies.mean(axis=0)
        band_std = frame_energies.std(axis=0)

        # Frame snapshots: per-frame total energy and dominant band index
        total_e = frame_energies.sum(axis=1)
        dom_b = frame_energies.argmax(axis=1).astype(np.float64) / max(self.n_bands - 1, 1)
        # Normalize snapshot statistics
        e_max = max(float(np.abs(total_e).max()), eps)
        snapshot = np.zeros(self.n_frames * 2, dtype=np.float64)
        snapshot[0::2] = total_e / e_max
        snapshot[1::2] = dom_b

        return np.concatenate(
            [
                np.array([rms, zcr, centroid, flatness]),
                band_mean,
                band_std,
                snapshot,
            ]
        )

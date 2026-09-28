"""
mel_features.py — Log-Mel spectrogram extraction.

Implements:
  FFT magnitude spectrum → Mel filterbank → log transformation

Parameters must match firmware audio_config.h exactly to prevent
training / inference mismatch.
"""

from __future__ import annotations

import numpy as np

# ──────────────────────────────────────────────────────────────
# Feature parameters — keep in sync with audio_config.h
# ──────────────────────────────────────────────────────────────
SAMPLE_RATE: int = 16_000
N_FFT: int = 512           # FFT points (next power-of-2 above frame_size=400)
N_MELS: int = 40           # Mel filterbank bins
FMIN: float = 20.0         # Minimum frequency (Hz)
FMAX: float = 8_000.0      # Maximum frequency (Hz — Nyquist for 16 kHz)
LOG_OFFSET: float = 1e-6   # Added before log to avoid log(0)


def hz_to_mel(freq_hz: float) -> float:
    """Convert frequency in Hz to the Mel scale."""
    return 2595.0 * np.log10(1.0 + freq_hz / 700.0)


def mel_to_hz(mel: float) -> float:
    """Convert Mel frequency to Hz."""
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def build_mel_filterbank(
    n_fft: int = N_FFT,
    n_mels: int = N_MELS,
    sample_rate: int = SAMPLE_RATE,
    fmin: float = FMIN,
    fmax: float = FMAX,
) -> np.ndarray:
    """
    Build a triangular Mel filterbank matrix.

    Returns:
        Array of shape [n_mels, n_fft // 2 + 1].
        Each row is one Mel filter applied to FFT magnitude bins.
    """
    n_freqs = n_fft // 2 + 1
    # Frequency axis (Hz) for each FFT bin
    fft_freqs = np.linspace(0, sample_rate / 2, n_freqs)

    # n_mels + 2 equally-spaced Mel points between fmin and fmax
    mel_min = hz_to_mel(fmin)
    mel_max = hz_to_mel(fmax)
    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = np.array([mel_to_hz(m) for m in mel_points])

    # Build filterbank
    filterbank = np.zeros((n_mels, n_freqs), dtype=np.float32)
    for m in range(1, n_mels + 1):
        f_left = hz_points[m - 1]
        f_center = hz_points[m]
        f_right = hz_points[m + 1]
        for k, f in enumerate(fft_freqs):
            if f_left <= f <= f_center:
                filterbank[m - 1, k] = (f - f_left) / (f_center - f_left + 1e-12)
            elif f_center < f <= f_right:
                filterbank[m - 1, k] = (f_right - f) / (f_right - f_center + 1e-12)

    return filterbank


# Pre-compute the filterbank once at import time for efficiency
_FILTERBANK: np.ndarray | None = None


def get_filterbank() -> np.ndarray:
    """Return the cached Mel filterbank (built on first call)."""
    global _FILTERBANK
    if _FILTERBANK is None:
        _FILTERBANK = build_mel_filterbank()
    return _FILTERBANK


def compute_log_mel(
    windowed_frames: np.ndarray,
    n_fft: int = N_FFT,
    filterbank: np.ndarray | None = None,
    log_offset: float = LOG_OFFSET,
) -> np.ndarray:
    """
    Compute Log-Mel spectrogram from windowed frames.

    Args:
        windowed_frames: 2-D array [n_frames, frame_size] after windowing.
        n_fft: FFT size (should be >= frame_size).
        filterbank: Pre-computed Mel filterbank [n_mels, n_fft//2+1].
                    If None, the default filterbank is used.
        log_offset: Small value added before log to avoid log(0).

    Returns:
        Log-Mel feature matrix [n_frames, n_mels], dtype float32.
    """
    if windowed_frames.ndim != 2:
        raise ValueError(f"Expected 2-D windowed frames, got shape {windowed_frames.shape}")

    if filterbank is None:
        filterbank = get_filterbank()

    # FFT magnitude spectrum [n_frames, n_fft//2+1]
    fft_mag = np.abs(
        np.fft.rfft(windowed_frames, n=n_fft, axis=1)
    ).astype(np.float32)

    # Power spectrum
    power = fft_mag ** 2

    # Apply Mel filterbank: [n_frames, n_mels]
    mel_energy = power @ filterbank.T

    # Log compression
    log_mel = np.log(mel_energy + log_offset)

    return log_mel.astype(np.float32)


def normalize_features(
    features: np.ndarray,
    mean: np.ndarray | None = None,
    std: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Normalize log-Mel features to zero mean, unit variance.

    Args:
        features: 2-D array [n_frames, n_mels].
        mean: Pre-computed mean [n_mels]. If None, computed from features.
        std: Pre-computed std [n_mels]. If None, computed from features.

    Returns:
        (normalized_features, mean, std)
    """
    if mean is None:
        mean = features.mean(axis=0)
    if std is None:
        std = features.std(axis=0)
    std_safe = np.where(std > 1e-8, std, 1.0)
    return ((features - mean) / std_safe).astype(np.float32), mean, std

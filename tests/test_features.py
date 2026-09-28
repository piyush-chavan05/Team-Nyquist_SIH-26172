"""
test_features.py — Tests for Log-Mel feature extraction.

Run with: pytest tests/test_features.py -v
"""

from __future__ import annotations

import numpy as np
import pytest

from ml.preprocessing.mel_features import (
    build_mel_filterbank, compute_log_mel, hz_to_mel, mel_to_hz,
    normalize_features, N_MELS, N_FFT, SAMPLE_RATE
)
from ml.preprocessing.framing import frame_audio, hann_window, apply_window


def make_windowed_frames(n_samples: int = 16000) -> np.ndarray:
    """Generate windowed frames from a sine wave."""
    audio = np.sin(2 * np.pi * 440 * np.arange(n_samples) / SAMPLE_RATE).astype(np.float32)
    frames = frame_audio(audio, frame_size=400, hop_size=160, pad=False)
    w = hann_window(400)
    return apply_window(frames, w)


class TestMelConversion:
    def test_hz_to_mel_zero(self):
        assert abs(hz_to_mel(0.0) - 0.0) < 1e-3

    def test_hz_to_mel_1000(self):
        # mel(1000 Hz) ≈ 999.98 Mel
        assert 990 < hz_to_mel(1000) < 1010

    def test_round_trip(self):
        """hz → mel → hz should be close to identity."""
        for f in [100, 500, 1000, 4000, 8000]:
            assert abs(mel_to_hz(hz_to_mel(float(f))) - f) < 1e-3


class TestFilterbank:
    def test_shape(self):
        fb = build_mel_filterbank()
        assert fb.shape == (N_MELS, N_FFT // 2 + 1)

    def test_non_negative(self):
        fb = build_mel_filterbank()
        assert np.all(fb >= 0)

    def test_rows_sum_positive(self):
        """Each filter row should have some non-zero values."""
        fb = build_mel_filterbank()
        row_sums = fb.sum(axis=1)
        assert np.all(row_sums > 0), "Some Mel filter rows are all-zero"

    def test_custom_params(self):
        fb = build_mel_filterbank(n_fft=256, n_mels=20, sample_rate=16000)
        assert fb.shape == (20, 129)


class TestComputeLogMel:
    def test_output_shape(self):
        windowed = make_windowed_frames()
        log_mel = compute_log_mel(windowed)
        assert log_mel.shape == (windowed.shape[0], N_MELS)

    def test_output_dtype(self):
        windowed = make_windowed_frames()
        log_mel = compute_log_mel(windowed)
        assert log_mel.dtype == np.float32

    def test_deterministic(self):
        """Same input → same output."""
        audio = np.random.default_rng(0).random(16000).astype(np.float32)
        frames = frame_audio(audio, frame_size=400, hop_size=160, pad=False)
        w = hann_window(400)
        windowed = apply_window(frames, w)

        out1 = compute_log_mel(windowed)
        out2 = compute_log_mel(windowed)
        np.testing.assert_array_equal(out1, out2)

    def test_no_nan_or_inf(self):
        windowed = make_windowed_frames()
        log_mel = compute_log_mel(windowed)
        assert not np.any(np.isnan(log_mel)), "NaN in log-Mel output"
        assert not np.any(np.isinf(log_mel)), "Inf in log-Mel output"

    def test_silent_audio(self):
        """All-zero audio should not produce NaN or -inf."""
        silent = np.zeros((10, 400), dtype=np.float32)
        log_mel = compute_log_mel(silent)
        assert not np.any(np.isnan(log_mel))

    def test_invalid_input_raises(self):
        with pytest.raises(ValueError):
            compute_log_mel(np.zeros(400, dtype=np.float32))  # 1D not 2D


class TestNormalizeFeatures:
    def test_output_shape(self):
        features = np.random.randn(98, 40).astype(np.float32)
        norm, mean, std = normalize_features(features)
        assert norm.shape == features.shape
        assert mean.shape == (40,)
        assert std.shape == (40,)

    def test_near_zero_mean(self):
        features = np.random.randn(1000, 40).astype(np.float32)
        norm, mean, std = normalize_features(features)
        # Normalized mean should be near zero
        assert np.max(np.abs(norm.mean(axis=0))) < 0.5  # within ±0.5 std after normalization

    def test_provided_stats(self):
        features = np.ones((10, 5), dtype=np.float32) * 3.0
        mean = np.ones(5, dtype=np.float32) * 3.0
        std = np.ones(5, dtype=np.float32)
        norm, _, _ = normalize_features(features, mean=mean, std=std)
        np.testing.assert_allclose(norm, np.zeros((10, 5)), atol=1e-6)

    def test_constant_feature_no_div_zero(self):
        """Features with zero std should not crash."""
        features = np.ones((10, 40), dtype=np.float32)
        norm, mean, std = normalize_features(features)
        assert not np.any(np.isnan(norm))

"""
test_audio.py — Tests for audio I/O and preprocessing.

Run with: pytest tests/test_audio.py -v
"""

from __future__ import annotations

import io
import struct
import tempfile
from pathlib import Path

import numpy as np
import pytest

from ml.preprocessing.audio_io import load_wav, validate_wav, TARGET_SR
from ml.preprocessing.framing import (
    frame_audio, hann_window, apply_window, FRAME_SIZE, HOP_SIZE
)


# ──────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────

def make_wav_file(
    samples: np.ndarray,
    sr: int = 16000,
    channels: int = 1,
    tmp_dir: str | None = None,
) -> str:
    """Write a minimal WAV file and return its path."""
    import soundfile as sf
    with tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False,
        dir=tmp_dir
    ) as f:
        sf.write(f.name, samples, sr)
        return f.name


# ──────────────────────────────────────────────────────
# audio_io tests
# ──────────────────────────────────────────────────────

class TestLoadWav:
    def test_loads_mono_16k(self, tmp_path):
        """Load a 16 kHz mono WAV correctly."""
        audio = np.sin(2 * np.pi * 440 * np.arange(16000) / 16000).astype(np.float32)
        wav_path = make_wav_file(audio, sr=16000, channels=1, tmp_dir=str(tmp_path))

        loaded, sr = load_wav(wav_path)
        assert sr == TARGET_SR
        assert loaded.ndim == 1
        assert len(loaded) == 16000
        assert loaded.dtype == np.float32

    def test_converts_stereo_to_mono(self, tmp_path):
        """Stereo input is averaged to mono."""
        import soundfile as sf
        stereo = np.random.randn(8000, 2).astype(np.float32)
        wav_path = str(tmp_path / "stereo.wav")
        sf.write(wav_path, stereo, 16000)

        loaded, sr = load_wav(wav_path)
        assert loaded.ndim == 1
        assert len(loaded) == 8000

    def test_resamples_if_needed(self, tmp_path):
        """File at 8 kHz is resampled to 16 kHz."""
        audio_8k = np.zeros(8000, dtype=np.float32)
        wav_path = make_wav_file(audio_8k, sr=8000, tmp_dir=str(tmp_path))

        loaded, sr = load_wav(wav_path, target_sr=16000)
        assert sr == 16000
        assert len(loaded) > 8000  # upsampled

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_wav("/nonexistent/path/file.wav")

    def test_normalize_flag(self, tmp_path):
        """Normalization scales to [-1, 1]."""
        audio = np.array([0.1, 0.5, -0.3, 0.8], dtype=np.float32)
        wav_path = make_wav_file(audio, sr=16000, tmp_dir=str(tmp_path))
        loaded, _ = load_wav(wav_path, normalize=True)
        assert np.max(np.abs(loaded)) <= 1.0 + 1e-5


class TestValidateWav:
    def test_valid_file(self, tmp_path):
        audio = np.zeros(16000, dtype=np.float32)
        wav_path = make_wav_file(audio, sr=16000, tmp_dir=str(tmp_path))
        result = validate_wav(wav_path)
        assert result["ok"] is True
        assert result["sr"] == 16000

    def test_wrong_sr_is_warning(self, tmp_path):
        audio = np.zeros(8000, dtype=np.float32)
        wav_path = make_wav_file(audio, sr=8000, tmp_dir=str(tmp_path))
        result = validate_wav(wav_path, expected_sr=16000)
        # Wrong SR produces a warning/error in the list
        assert any("8000" in e for e in result["errors"])

    def test_nonexistent_file(self):
        result = validate_wav("/no/such/file.wav")
        assert result["ok"] is False


# ──────────────────────────────────────────────────────
# framing tests
# ──────────────────────────────────────────────────────

class TestFrameAudio:
    def test_basic_shape(self):
        audio = np.zeros(16000, dtype=np.float32)
        frames = frame_audio(audio, frame_size=400, hop_size=160)
        assert frames.ndim == 2
        assert frames.shape[1] == 400

    def test_correct_frame_count(self):
        """Verify frame count formula."""
        n = 16000
        frames = frame_audio(np.zeros(n, dtype=np.float32), frame_size=400, hop_size=160, pad=False)
        expected = (n - 400) // 160 + 1
        assert frames.shape[0] == expected

    def test_overlap_correctness(self):
        """Each frame starts hop_size samples after the previous."""
        audio = np.arange(1000, dtype=np.float32)
        frames = frame_audio(audio, frame_size=100, hop_size=50, pad=False)
        assert frames[0, 0] == 0.0
        assert frames[1, 0] == 50.0
        assert frames[2, 0] == 100.0

    def test_empty_audio(self):
        audio = np.zeros(0, dtype=np.float32)
        frames = frame_audio(audio, frame_size=400, hop_size=160)
        assert frames.shape[0] == 0

    def test_invalid_input_raises(self):
        with pytest.raises(ValueError):
            frame_audio(np.zeros((10, 2), dtype=np.float32))


class TestHannWindow:
    def test_length(self):
        w = hann_window(400)
        assert len(w) == 400

    def test_endpoints_near_zero(self):
        w = hann_window(400)
        assert abs(w[0]) < 1e-6

    def test_peak_near_one(self):
        w = hann_window(400)
        assert abs(w[200] - 1.0) < 0.01


class TestApplyWindow:
    def test_shape_preserved(self):
        frames = np.ones((10, 400), dtype=np.float32)
        w = hann_window(400)
        windowed = apply_window(frames, w)
        assert windowed.shape == (10, 400)

    def test_values_scaled(self):
        frames = np.ones((1, 4), dtype=np.float32)
        w = np.array([0.0, 0.5, 0.5, 0.0], dtype=np.float32)
        windowed = apply_window(frames, w)
        np.testing.assert_allclose(windowed[0], w)

    def test_mismatched_window_raises(self):
        frames = np.ones((5, 400), dtype=np.float32)
        w = np.ones(300, dtype=np.float32)
        with pytest.raises(ValueError):
            apply_window(frames, w)

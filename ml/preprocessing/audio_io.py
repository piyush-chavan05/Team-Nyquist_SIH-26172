"""
audio_io.py — WAV file loading and validation.

Handles loading, sample rate checking/resampling, mono conversion,
and basic amplitude normalization.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

# Target audio parameters — must match firmware audio_config.h
TARGET_SR: int = 16_000
TARGET_CHANNELS: int = 1  # mono


def load_wav(
    path: str | Path,
    target_sr: int = TARGET_SR,
    normalize: bool = False,
) -> Tuple[np.ndarray, int]:
    """
    Load a WAV file, validate and resample if needed, convert to mono.

    Args:
        path: Path to the WAV file.
        target_sr: Target sample rate in Hz.
        normalize: If True, normalize audio to [-1, 1] peak amplitude.

    Returns:
        (audio, sample_rate) where audio is a 1-D float32 numpy array
        and sample_rate is target_sr after resampling.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be read as PCM audio.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
    # audio shape: [samples, channels]

    # Convert to mono
    if audio.shape[1] > 1:
        logger.debug("Converting %s from %d channels to mono", path.name, audio.shape[1])
        audio = audio.mean(axis=1)
    else:
        audio = audio[:, 0]

    # Resample if necessary
    if sr != target_sr:
        logger.debug("Resampling %s from %d Hz to %d Hz", path.name, sr, target_sr)
        audio = _resample(audio, sr, target_sr)

    if normalize:
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak

    return audio.astype(np.float32), target_sr


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Simple linear resampling via scipy if available, else raise.
    scipy.signal.resample_poly is preferred for quality.
    """
    try:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(target_sr, orig_sr)
        up = target_sr // g
        down = orig_sr // g
        return resample_poly(audio, up, down).astype(np.float32)
    except ImportError as exc:
        raise ImportError(
            "scipy is required for resampling. Install it with: pip install scipy"
        ) from exc


def validate_wav(path: str | Path, expected_sr: int = TARGET_SR) -> dict:
    """
    Validate a WAV file without fully loading it.

    Returns a dict with keys:
        - ok (bool)
        - sr (int)
        - channels (int)
        - frames (int)
        - duration_s (float)
        - errors (list[str])
    """
    path = Path(path)
    errors: list[str] = []

    if not path.exists():
        return {"ok": False, "errors": [f"File not found: {path}"]}

    try:
        info = sf.info(str(path))
    except Exception as exc:
        return {"ok": False, "errors": [f"Cannot read file: {exc}"]}

    sr = info.samplerate
    channels = info.channels
    frames = info.frames
    duration_s = frames / sr if sr > 0 else 0.0

    if sr != expected_sr:
        errors.append(f"Sample rate {sr} Hz (expected {expected_sr} Hz) — will be resampled")
    if channels > 2:
        errors.append(f"Unusual channel count: {channels}")
    if duration_s < 0.1:
        errors.append(f"Very short clip: {duration_s:.3f} s")
    if duration_s > 10.0:
        errors.append(f"Unusually long clip: {duration_s:.3f} s (expected < 10 s for KWS)")

    return {
        "ok": len([e for e in errors if "will be resampled" not in e]) == 0,
        "sr": sr,
        "channels": channels,
        "frames": frames,
        "duration_s": duration_s,
        "errors": errors,
    }

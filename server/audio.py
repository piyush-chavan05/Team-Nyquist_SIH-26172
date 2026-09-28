"""
audio.py — Audio reception and format validation for the ASR server.
"""

from __future__ import annotations

import numpy as np
from . import config


class AudioValidationError(Exception):
    pass


def validate_headers(headers: dict) -> None:
    """Validate audio stream request headers. Raises AudioValidationError on failure."""
    content_type = headers.get("content-type", headers.get("Content-Type", ""))
    if "application/octet-stream" not in content_type:
        raise AudioValidationError(
            f"Expected Content-Type: application/octet-stream, got: {content_type}"
        )

    try:
        sr = int(headers.get("x-sample-rate", headers.get("X-Sample-Rate", 0)))
    except ValueError:
        raise AudioValidationError("X-Sample-Rate must be an integer")
    if sr != config.EXPECTED_SAMPLE_RATE:
        raise AudioValidationError(
            f"Expected sample rate {config.EXPECTED_SAMPLE_RATE} Hz, got {sr} Hz"
        )

    try:
        ch = int(headers.get("x-channels", headers.get("X-Channels", 0)))
    except ValueError:
        raise AudioValidationError("X-Channels must be an integer")
    if ch != config.EXPECTED_CHANNELS:
        raise AudioValidationError(
            f"Expected {config.EXPECTED_CHANNELS} channel(s), got {ch}"
        )


def pcm_bytes_to_float(data: bytes, bit_depth: int = 16) -> np.ndarray:
    """Convert raw PCM bytes to float32 numpy array in [-1, 1]."""
    if bit_depth == 16:
        pcm = np.frombuffer(data, dtype=np.int16)
        return pcm.astype(np.float32) / 32768.0
    elif bit_depth == 32:
        pcm = np.frombuffer(data, dtype=np.int32)
        return pcm.astype(np.float32) / 2147483648.0
    else:
        raise AudioValidationError(f"Unsupported bit depth: {bit_depth}")


def validate_audio_data(audio: np.ndarray, sample_rate: int) -> None:
    """Validate decoded audio array. Raises AudioValidationError on failure."""
    duration_s = len(audio) / sample_rate
    if duration_s > config.MAX_AUDIO_DURATION_S:
        raise AudioValidationError(
            f"Audio too long: {duration_s:.1f}s (max {config.MAX_AUDIO_DURATION_S}s)"
        )
    if len(audio) == 0:
        raise AudioValidationError("Empty audio data")

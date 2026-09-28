"""
framing.py — Audio framing and windowing.

Produces overlapping frames from a 1-D audio array for STFT / feature extraction.
"""

from __future__ import annotations

import numpy as np


# Default framing parameters — must match firmware audio_config.h
FRAME_SIZE: int = 400    # samples (25 ms at 16 kHz)
HOP_SIZE: int = 160      # samples (10 ms at 16 kHz)


def frame_audio(
    audio: np.ndarray,
    frame_size: int = FRAME_SIZE,
    hop_size: int = HOP_SIZE,
    pad: bool = True,
) -> np.ndarray:
    """
    Split a 1-D audio array into overlapping frames.

    Args:
        audio: 1-D float32 numpy array (samples).
        frame_size: Number of samples per frame.
        hop_size: Step between frame starts (samples).
        pad: If True, zero-pad the end so that all audio is covered.

    Returns:
        2-D array of shape [n_frames, frame_size].
    """
    if audio.ndim != 1:
        raise ValueError(f"Expected 1-D audio array, got shape {audio.shape}")
    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("frame_size and hop_size must be positive")
    if hop_size > frame_size:
        raise ValueError("hop_size should be <= frame_size for overlapping frames")

    if len(audio) == 0:
        return np.empty((0, frame_size), dtype=audio.dtype)

    if pad:
        # Pad so that the last partial frame is included
        n_frames = 1 + max(0, (len(audio) - frame_size + hop_size - 1) // hop_size)
        pad_length = (n_frames - 1) * hop_size + frame_size - len(audio)
        if pad_length > 0:
            audio = np.pad(audio, (0, pad_length), mode="constant")
    else:
        n_frames = max(0, (len(audio) - frame_size) // hop_size + 1)

    if n_frames == 0:
        return np.empty((0, frame_size), dtype=audio.dtype)

    # Use stride tricks for efficient framing (no copy)
    shape = (n_frames, frame_size)
    strides = (audio.strides[0] * hop_size, audio.strides[0])
    frames = np.lib.stride_tricks.as_strided(audio, shape=shape, strides=strides)
    return frames.copy()  # copy to make writable


def hann_window(frame_size: int) -> np.ndarray:
    """
    Return a Hann window of the given size.

    w[n] = 0.5 * (1 - cos(2π·n / (N-1)))
    """
    return np.hanning(frame_size).astype(np.float32)


def apply_window(frames: np.ndarray, window: np.ndarray | None = None) -> np.ndarray:
    """
    Apply a window function to each frame.

    Args:
        frames: 2-D array [n_frames, frame_size].
        window: 1-D window array of shape [frame_size].
                If None, a Hann window is created automatically.

    Returns:
        Windowed frames, same shape as input.
    """
    if frames.ndim != 2:
        raise ValueError(f"Expected 2-D frames array, got shape {frames.shape}")
    frame_size = frames.shape[1]
    if window is None:
        window = hann_window(frame_size)
    if window.shape != (frame_size,):
        raise ValueError(
            f"Window shape {window.shape} does not match frame size {frame_size}"
        )
    return frames * window[np.newaxis, :]

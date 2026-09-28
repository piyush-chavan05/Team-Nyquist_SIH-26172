"""
test_ring_buffer.py — Tests for the Python ring buffer reference implementation.

This tests the host-side Python ring buffer which mirrors the logic of
firmware/esp32-s3/main/buffer/ring_buffer.c.

Run with: pytest tests/test_ring_buffer.py -v
"""

from __future__ import annotations

import numpy as np
import pytest


class RingBuffer:
    """
    Host-side Python reference implementation of the ring buffer.

    Mirrors the fixed-size circular buffer used in the ESP32-S3 firmware.
    Stores audio samples (int16 or float32).

    This is NOT the firmware implementation — it is a host-side reference
    used for testing the buffer logic before porting to C.
    """

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._buf = np.zeros(capacity, dtype=np.float32)
        self._capacity = capacity
        self._write_pos = 0
        self._count = 0  # number of valid samples currently in buffer

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def count(self) -> int:
        return self._count

    @property
    def is_full(self) -> bool:
        return self._count == self._capacity

    def write(self, samples: np.ndarray):
        """Write samples into the ring buffer (overwrites oldest on overflow)."""
        n = len(samples)
        for s in samples:
            self._buf[self._write_pos] = s
            self._write_pos = (self._write_pos + 1) % self._capacity
        self._count = min(self._count + n, self._capacity)

    def read_latest(self, n: int) -> np.ndarray:
        """
        Read the n most recent samples in chronological order.
        Returns fewer than n if buffer has fewer samples.
        """
        n = min(n, self._count)
        if n == 0:
            return np.array([], dtype=np.float32)

        # Compute start position for the n most recent samples
        # write_pos points to the next write position (oldest if full)
        end = self._write_pos
        start = (end - n) % self._capacity

        if start < end:
            return self._buf[start:end].copy()
        else:
            return np.concatenate([self._buf[start:], self._buf[:end]])

    def clear(self):
        self._write_pos = 0
        self._count = 0


# ──────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────

class TestRingBufferBasic:
    def test_initial_state(self):
        rb = RingBuffer(1000)
        assert rb.count == 0
        assert rb.capacity == 1000
        assert not rb.is_full

    def test_invalid_capacity(self):
        with pytest.raises(ValueError):
            RingBuffer(0)

    def test_write_and_read_simple(self):
        rb = RingBuffer(100)
        data = np.arange(10, dtype=np.float32)
        rb.write(data)
        result = rb.read_latest(10)
        np.testing.assert_array_equal(result, data)

    def test_read_count_increments(self):
        rb = RingBuffer(100)
        rb.write(np.zeros(50, dtype=np.float32))
        assert rb.count == 50

    def test_full_state(self):
        rb = RingBuffer(50)
        rb.write(np.zeros(50, dtype=np.float32))
        assert rb.is_full
        assert rb.count == 50


class TestRingBufferWraparound:
    def test_wraparound_overwrites_oldest(self):
        """Writing beyond capacity overwrites oldest samples."""
        rb = RingBuffer(5)
        rb.write(np.array([1, 2, 3, 4, 5], dtype=np.float32))
        rb.write(np.array([6, 7], dtype=np.float32))

        result = rb.read_latest(5)
        # Should contain [3, 4, 5, 6, 7] — oldest 1, 2 overwritten
        expected = np.array([3, 4, 5, 6, 7], dtype=np.float32)
        np.testing.assert_array_equal(result, expected)

    def test_multiple_overwrites(self):
        """Buffer can be overwritten many times."""
        rb = RingBuffer(10)
        for i in range(50):
            rb.write(np.array([float(i)], dtype=np.float32))
        assert rb.count == 10
        result = rb.read_latest(10)
        expected = np.arange(40.0, 50.0, dtype=np.float32)
        np.testing.assert_array_equal(result, expected)

    def test_read_fewer_than_available(self):
        rb = RingBuffer(100)
        rb.write(np.arange(50, dtype=np.float32))
        result = rb.read_latest(20)
        expected = np.arange(30.0, 50.0, dtype=np.float32)
        np.testing.assert_array_equal(result, expected)


class TestPreRoll:
    def test_preroll_retrieval(self):
        """
        Pre-roll test: write 2 seconds of audio, confirm pre-roll contains
        the most recent samples before the trigger.
        """
        sr = 16000
        preroll_duration = 0.5  # 0.5 second pre-roll
        rb = RingBuffer(sr * 2)  # 2-second ring buffer

        # Simulate 2 seconds of audio (numbered samples for easy verification)
        audio = np.arange(sr * 2, dtype=np.float32)
        rb.write(audio)

        # Wake is detected now — retrieve 0.5s pre-roll
        preroll = rb.read_latest(int(sr * preroll_duration))
        assert len(preroll) == int(sr * preroll_duration)
        # Should be the most recent 8000 samples: 24000..31999
        expected_start = sr * 2 - int(sr * preroll_duration)
        np.testing.assert_array_equal(preroll[0], float(expected_start))
        np.testing.assert_array_equal(preroll[-1], float(sr * 2 - 1))

    def test_read_empty_buffer(self):
        rb = RingBuffer(1000)
        result = rb.read_latest(100)
        assert len(result) == 0

    def test_read_more_than_count(self):
        rb = RingBuffer(100)
        rb.write(np.ones(10, dtype=np.float32))
        result = rb.read_latest(50)
        assert len(result) == 10  # Only 10 available


class TestRingBufferClear:
    def test_clear_resets_state(self):
        rb = RingBuffer(100)
        rb.write(np.ones(50, dtype=np.float32))
        rb.clear()
        assert rb.count == 0
        assert not rb.is_full
        result = rb.read_latest(10)
        assert len(result) == 0

"""
test_wake_logic.py — Tests for wake detection logic.

Tests: threshold, temporal confirmation, cooldown, noise-adaptive adjustment.

Run with: pytest tests/test_wake_logic.py -v
"""

from __future__ import annotations

import numpy as np
import pytest


# ──────────────────────────────────────────────────────
# Host-side wake detector reference (mirrors firmware wake_detector.c)
# ──────────────────────────────────────────────────────

class WakeDetector:
    """
    Host-side reference implementation of the wake detection logic.

    Parameters correspond to those in firmware/esp32-s3/main/wake/wake_detector.h
    """

    def __init__(
        self,
        base_threshold: float = 0.80,
        n_confirm: int = 3,
        max_gap: int = 1,
        cooldown_windows: int = 20,
        min_threshold: float = 0.65,
        max_threshold: float = 0.95,
        noise_alpha: float = 0.05,
        noise_offset_low: float = 0.05,
        noise_offset_moderate: float = 0.0,
        noise_offset_high: float = -0.05,
        noise_low_threshold: float = 0.01,
        noise_high_threshold: float = 0.05,
    ):
        self.base_threshold = base_threshold
        self.n_confirm = n_confirm
        self.max_gap = max_gap
        self.cooldown_windows = cooldown_windows
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.noise_alpha = noise_alpha
        self.noise_offset_low = noise_offset_low
        self.noise_offset_moderate = noise_offset_moderate
        self.noise_offset_high = noise_offset_high
        self.noise_low_threshold = noise_low_threshold
        self.noise_high_threshold = noise_high_threshold

        # State
        self._confirm_count = 0
        self._gap_count = 0
        self._cooldown_remaining = 0
        self._noise_estimate = 0.0
        self._current_threshold = base_threshold

    @property
    def current_threshold(self) -> float:
        return self._current_threshold

    def _update_noise(self, frame_energy: float):
        """Exponential moving average noise estimate."""
        self._noise_estimate = (
            self.noise_alpha * frame_energy
            + (1 - self.noise_alpha) * self._noise_estimate
        )
        # Adjust threshold
        if self._noise_estimate < self.noise_low_threshold:
            offset = self.noise_offset_low
        elif self._noise_estimate > self.noise_high_threshold:
            offset = self.noise_offset_high
        else:
            offset = self.noise_offset_moderate

        self._current_threshold = float(np.clip(
            self.base_threshold + offset,
            self.min_threshold,
            self.max_threshold
        ))

    def process(self, confidence: float, frame_energy: float = 0.0) -> bool:
        """
        Process one window confidence score.

        Args:
            confidence: Model keyword confidence in [0, 1].
            frame_energy: RMS energy of the frame (for noise adaptation).

        Returns:
            True if wake word is confirmed in this window.
        """
        # Cooldown
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1
            return False

        # Update noise estimate (only during non-confirm windows)
        if self._confirm_count == 0:
            self._update_noise(frame_energy)

        if confidence >= self._current_threshold:
            self._confirm_count += 1
            self._gap_count = 0
        else:
            if self._confirm_count > 0:
                self._gap_count += 1
                if self._gap_count > self.max_gap:
                    self._confirm_count = 0
                    self._gap_count = 0

        if self._confirm_count >= self.n_confirm:
            self._confirm_count = 0
            self._gap_count = 0
            self._cooldown_remaining = self.cooldown_windows
            return True

        return False

    def reset(self):
        self._confirm_count = 0
        self._gap_count = 0
        self._cooldown_remaining = 0


# ──────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────

class TestThreshold:
    def test_below_threshold_no_wake(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=1)
        assert not wd.process(0.79)

    def test_at_threshold_triggers(self):
        # Noise offset in quiet room raises threshold slightly above base;
        # use noise_offset_moderate=0 and force low-noise path off by setting
        # noise_high_threshold very low so a realistic quiet frame stays moderate.
        wd = WakeDetector(
            base_threshold=0.80, n_confirm=1,
            noise_alpha=0.0,  # freeze noise — no threshold change
            noise_offset_low=0.0,
            noise_offset_moderate=0.0,
            noise_offset_high=0.0,
        )
        assert wd.process(0.80)

    def test_above_threshold_triggers(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=1)
        assert wd.process(0.95)


class TestTemporalConfirmation:
    def test_single_window_insufficient(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=3)
        assert not wd.process(0.99)
        assert not wd.process(0.99)

    def test_n_confirm_windows_triggers(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=3)
        results = [wd.process(0.99) for _ in range(3)]
        assert results[-1] is True
        assert results[0] is False

    def test_gap_resets_counter(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=3, max_gap=0)
        wd.process(0.99)
        wd.process(0.99)
        wd.process(0.10)  # below threshold — gap exceeded
        # Counter reset; 2 more high-confidence not enough
        assert not wd.process(0.99)
        assert not wd.process(0.99)

    def test_gap_within_max_gap_allowed(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=3, max_gap=1)
        wd.process(0.99)
        wd.process(0.99)
        wd.process(0.10)  # gap — allowed since max_gap=1
        result = wd.process(0.99)  # confirm_count reaches 3
        assert result is True


class TestCooldown:
    def test_cooldown_prevents_retriggering(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=1, cooldown_windows=5)
        assert wd.process(0.99)  # triggers
        # Next 5 windows should not trigger regardless of confidence
        for _ in range(5):
            assert not wd.process(0.99)
        # After cooldown, should trigger again
        assert wd.process(0.99)

    def test_cooldown_zero_allows_immediate_retrigger(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=1, cooldown_windows=0)
        assert wd.process(0.99)
        assert wd.process(0.99)


class TestNoiseAdaptation:
    def test_threshold_increases_in_low_noise(self):
        wd = WakeDetector(
            base_threshold=0.80,
            noise_alpha=1.0,  # instant update
            noise_offset_low=+0.05,
            noise_low_threshold=0.01,
            noise_high_threshold=0.05,
            n_confirm=10,  # prevent accidental wake
        )
        wd.process(0.01, frame_energy=0.001)  # very quiet
        assert wd.current_threshold > 0.80

    def test_threshold_decreases_in_high_noise(self):
        wd = WakeDetector(
            base_threshold=0.80,
            noise_alpha=1.0,
            noise_offset_high=-0.05,
            noise_low_threshold=0.01,
            noise_high_threshold=0.05,
            n_confirm=10,
        )
        wd.process(0.01, frame_energy=0.10)  # high noise
        assert wd.current_threshold < 0.80

    def test_threshold_clamped_at_minimum(self):
        wd = WakeDetector(
            base_threshold=0.70,
            noise_alpha=1.0,
            noise_offset_high=-0.10,
            min_threshold=0.65,
            noise_high_threshold=0.05,
            n_confirm=10,
        )
        wd.process(0.01, frame_energy=0.10)
        assert wd.current_threshold >= 0.65

    def test_threshold_clamped_at_maximum(self):
        wd = WakeDetector(
            base_threshold=0.90,
            noise_alpha=1.0,
            noise_offset_low=+0.10,
            max_threshold=0.95,
            noise_low_threshold=0.01,
            n_confirm=10,
        )
        wd.process(0.01, frame_energy=0.0001)
        assert wd.current_threshold <= 0.95

    def test_reset_clears_state(self):
        wd = WakeDetector(base_threshold=0.80, n_confirm=2, cooldown_windows=5)
        wd.process(0.99)  # 1 confirm
        wd.reset()
        assert not wd.process(0.99)  # counter was reset, 1 not enough for n_confirm=2

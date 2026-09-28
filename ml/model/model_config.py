"""
model_config.py — Centralized DS-CNN model configuration.

All configurable values live here. Change here only — not scattered through code.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class ModelConfig:
    # ── Input ────────────────────────────────────────────
    sample_rate: int = 16_000
    frame_size: int = 400       # samples (25 ms)
    hop_size: int = 160         # samples (10 ms)
    n_fft: int = 512
    n_mels: int = 40
    target_duration_s: float = 1.0

    # Derived: number of time steps in one feature window
    # = (target_samples - frame_size) // hop_size + 1 ≈ 98
    @property
    def n_time_steps(self) -> int:
        target_samples = int(self.target_duration_s * self.sample_rate)
        return max(1, (target_samples - self.frame_size) // self.hop_size + 1)

    # ── Classes ──────────────────────────────────────────
    # 0 = keyword, 1 = unknown, 2 = silence
    n_classes: int = 3
    class_names: List[str] = field(default_factory=lambda: ["keyword", "unknown", "silence"])

    # ── Architecture ─────────────────────────────────────
    initial_filters: int = 32       # First standard Conv2D filters
    ds_block_filters: List[int] = field(
        default_factory=lambda: [64, 64, 128, 128]
    )                                # Filters for each DS block
    kernel_size: int = 3            # Conv kernel size (square)
    dropout_rate: float = 0.25

    # ── Training ─────────────────────────────────────────
    batch_size: int = 64
    epochs: int = 50
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    lr_step_size: int = 20          # StepLR: reduce LR every N epochs
    lr_gamma: float = 0.5           # StepLR: multiply LR by this factor

    # ── Paths ─────────────────────────────────────────────
    features_dir: str = "ml/artifacts/features/"
    model_save_path: str = "ml/artifacts/model.pth"
    tflite_save_path: str = "ml/artifacts/model.tflite"
    normalization_stats_path: str = "ml/artifacts/norm_stats.npz"

    # ── Wake detection (not used during training) ─────────
    # Documented here for traceability to firmware config
    base_threshold: float = 0.80       # Development value — requires tuning
    n_confirm_windows: int = 3
    cooldown_s: float = 2.0
    noise_alpha: float = 0.05          # EMA smoothing for noise estimate


# Default config instance
DEFAULT_CONFIG = ModelConfig()

"""
model.py — Compact DS-CNN for keyword spotting.

Architecture: Standard Conv2D → N Depthwise-Separable blocks
              → Global Average Pooling → Dropout → Dense(n_classes)

Designed for embedded deployment (TFLite export path).
"""

from __future__ import annotations

import torch
import torch.nn as nn
from .model_config import ModelConfig, DEFAULT_CONFIG


class DepthwiseSeparableBlock(nn.Module):
    """
    One depthwise-separable convolution block.

    Depthwise conv (one filter per input channel) followed by
    pointwise conv (1×1) to mix channels.
    Both followed by BatchNorm + ReLU.
    """

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3):
        super().__init__()
        self.depthwise = nn.Sequential(
            nn.Conv2d(
                in_channels, in_channels,
                kernel_size=kernel_size,
                padding=kernel_size // 2,
                groups=in_channels,
                bias=False,
            ),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
        )
        self.pointwise = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.depthwise(x)
        x = self.pointwise(x)
        return x


class DSCNN(nn.Module):
    """
    Depthwise Separable CNN for keyword spotting.

    Input shape:  [batch, 1, n_time_steps, n_mels]
    Output shape: [batch, n_classes]  (raw logits)
    """

    def __init__(self, config: ModelConfig = DEFAULT_CONFIG):
        super().__init__()
        self.config = config

        # Initial standard convolution
        self.input_conv = nn.Sequential(
            nn.Conv2d(
                1, config.initial_filters,
                kernel_size=config.kernel_size,
                padding=config.kernel_size // 2,
                bias=False,
            ),
            nn.BatchNorm2d(config.initial_filters),
            nn.ReLU(inplace=True),
        )

        # Depthwise-separable blocks
        ds_blocks = []
        in_ch = config.initial_filters
        for out_ch in config.ds_block_filters:
            ds_blocks.append(DepthwiseSeparableBlock(in_ch, out_ch, config.kernel_size))
            in_ch = out_ch
        self.ds_blocks = nn.Sequential(*ds_blocks)

        # Global Average Pooling: [batch, C, T, M] → [batch, C]
        self.gap = nn.AdaptiveAvgPool2d(1)

        # Classifier
        self.classifier = nn.Sequential(
            nn.Dropout(config.dropout_rate),
            nn.Linear(in_ch, config.n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch, 1, n_time_steps, n_mels]
        Returns:
            logits: [batch, n_classes]
        """
        x = self.input_conv(x)
        x = self.ds_blocks(x)
        x = self.gap(x)
        x = x.view(x.size(0), -1)  # flatten: [batch, C]
        x = self.classifier(x)
        return x

    def count_parameters(self) -> int:
        """Return total trainable parameter count."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def model_size_kb(self) -> float:
        """Approximate model size in KB (float32 weights only)."""
        n_params = self.count_parameters()
        return n_params * 4 / 1024  # 4 bytes per float32


def build_model(config: ModelConfig = DEFAULT_CONFIG) -> DSCNN:
    """Construct and return a DSCNN model."""
    model = DSCNN(config)
    return model

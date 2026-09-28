"""
export.py — Export trained DS-CNN to TFLite format for ESP32-S3 deployment.

Note: TFLite export via PyTorch requires ONNX → TFLite conversion or
using torch2tflite. This script documents the supported export path.

For ESP32-S3, two runtime options are evaluated:
  1. TFLite Micro (via TensorFlow Lite)
  2. ESP-DL (Espressif's own inference framework)

The export path here targets TFLite as the primary format.

Usage:
    python ml/model/export.py \
        --model ml/artifacts/model.pth \
        --output ml/artifacts/model.tflite \
        --config ml/model/model_config.py
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import numpy as np
import torch

from .model import DSCNN, build_model
from .model_config import ModelConfig, DEFAULT_CONFIG

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_model(model_path: str, config: ModelConfig = DEFAULT_CONFIG) -> DSCNN:
    """Load a trained DSCNN checkpoint."""
    model = build_model(config)
    state = torch.load(model_path, map_location="cpu", weights_only=True)
    if "model_state_dict" in state:
        model.load_state_dict(state["model_state_dict"])
    else:
        model.load_state_dict(state)
    model.eval()
    return model


def export_onnx(model: DSCNN, output_path: str, config: ModelConfig = DEFAULT_CONFIG):
    """Export to ONNX format (intermediate step for TFLite conversion)."""
    dummy_input = torch.zeros(1, 1, config.n_time_steps, config.n_mels)
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        input_names=["input"],
        output_names=["output"],
        opset_version=11,
        do_constant_folding=True,
    )
    logger.info("Exported ONNX model: %s", output_path)


def export_tflite_via_onnx(
    model: DSCNN,
    output_dir: str,
    config: ModelConfig = DEFAULT_CONFIG,
) -> str:
    """
    Export DSCNN to TFLite via ONNX.

    Requires: onnx, onnx-tf, tensorflow (heavy dependencies).
    These are NOT in requirements.txt by default.
    Install with: pip install onnx onnx-tf tensorflow

    Returns path to TFLite file if successful, else raises.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    onnx_path = str(output_dir / "model.onnx")
    tflite_path = str(output_dir / "model.tflite")

    # Step 1: PyTorch → ONNX
    export_onnx(model, onnx_path, config)

    # Step 2: ONNX → TensorFlow SavedModel
    try:
        import onnx
        from onnx_tf.backend import prepare as onnx_tf_prepare
        onnx_model = onnx.load(onnx_path)
        tf_rep = onnx_tf_prepare(onnx_model)
        savedmodel_path = str(output_dir / "savedmodel")
        tf_rep.export_graph(savedmodel_path)
        logger.info("Converted to TF SavedModel: %s", savedmodel_path)
    except ImportError as exc:
        raise ImportError(
            "onnx-tf and tensorflow are required for TFLite export. "
            "Install with: pip install onnx onnx-tf tensorflow"
        ) from exc

    # Step 3: TF SavedModel → TFLite
    import tensorflow as tf
    converter = tf.lite.TFLiteConverter.from_saved_model(savedmodel_path)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]  # INT8 quantization-friendly
    tflite_model = converter.convert()

    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    size_kb = os.path.getsize(tflite_path) / 1024
    logger.info("Exported TFLite model: %s (%.1f KB)", tflite_path, size_kb)
    return tflite_path


def print_model_info(model: DSCNN):
    """Print parameter count and estimated size."""
    n_params = model.count_parameters()
    size_kb = model.model_size_kb()
    logger.info("Parameters: %d (%.1f K)", n_params, n_params / 1000)
    logger.info("Float32 model size: %.1f KB", size_kb)
    logger.info("NOTE: Embedded RAM footprint must be measured on ESP32-S3 target.")


def main():
    parser = argparse.ArgumentParser(description="Export DS-CNN to TFLite")
    parser.add_argument("--model", required=True, help="Path to .pth checkpoint")
    parser.add_argument("--output-dir", default="ml/artifacts/",
                        help="Output directory for exported files")
    args = parser.parse_args()

    config = DEFAULT_CONFIG
    model = load_model(args.model, config)
    print_model_info(model)

    try:
        tflite_path = export_tflite_via_onnx(model, args.output_dir, config)
        logger.info("Export complete: %s", tflite_path)
    except ImportError as exc:
        logger.warning("TFLite export skipped: %s", exc)
        # At minimum, export ONNX for later conversion
        onnx_path = str(Path(args.output_dir) / "model.onnx")
        export_onnx(model, onnx_path, config)
        logger.info("ONNX export saved to: %s", onnx_path)
        logger.info("Convert to TFLite with: pip install onnx onnx-tf tensorflow")


if __name__ == "__main__":
    main()

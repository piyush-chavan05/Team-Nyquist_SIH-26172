"""
evaluate.py — Evaluate a trained DS-CNN model on the test set.

Usage:
    python -m ml.training.evaluate \
        --model ml/artifacts/model.pth \
        --features-dir ml/artifacts/features/ \
        [--split ml/dataset/splits/test.json]
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from ml.model.model import build_model
from ml.model.model_config import DEFAULT_CONFIG
from ml.training.metrics import print_metrics

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@torch.no_grad()
def evaluate(model_path: str, features_dir: str, config=DEFAULT_CONFIG):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load model
    model = build_model(config).to(device)
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        trained_epoch = checkpoint.get("epoch", "?")
        trained_val_acc = checkpoint.get("val_acc", "?")
        logger.info("Loaded checkpoint: epoch=%s  val_acc=%s", trained_epoch, trained_val_acc)
    else:
        model.load_state_dict(checkpoint)
    model.eval()

    # Load features
    features_dir = Path(features_dir)
    features = np.load(str(features_dir / "features.npy"))
    labels = np.load(str(features_dir / "labels.npy"))

    # Load normalization stats
    norm_path = Path(config.normalization_stats_path)
    if norm_path.exists():
        stats = np.load(str(norm_path))
        mean, std = stats["mean"], stats["std"]
        std = np.where(std > 1e-8, std, 1.0)
        features = (features - mean[np.newaxis, np.newaxis, :]) / std[np.newaxis, np.newaxis, :]
    else:
        logger.warning("No normalization stats found — features used as-is")

    X = torch.from_numpy(features.astype(np.float32)[:, np.newaxis, :, :])
    y = torch.from_numpy(labels.astype(np.int64))
    loader = DataLoader(TensorDataset(X, y), batch_size=64, shuffle=False)

    all_preds = []
    all_labels = []

    for X_batch, y_batch in loader:
        logits = model(X_batch.to(device))
        preds = logits.argmax(dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(y_batch.numpy())

    y_true = np.array(all_labels)
    y_pred = np.array(all_preds)

    print_metrics(y_true, y_pred, config.n_classes, config.class_names)

    logger.info("NOTE: These are host-side metrics on extracted features.")
    logger.info("Embedded inference metrics require validation on ESP32-S3 hardware.")


def main():
    parser = argparse.ArgumentParser(description="Evaluate DS-CNN keyword spotting model")
    parser.add_argument("--model", required=True, help="Path to .pth checkpoint")
    parser.add_argument("--features-dir", default=DEFAULT_CONFIG.features_dir)
    args = parser.parse_args()

    evaluate(args.model, args.features_dir)


if __name__ == "__main__":
    main()

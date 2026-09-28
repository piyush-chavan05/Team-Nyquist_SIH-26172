"""
train.py — Training script for DS-CNN keyword spotting model.

Usage:
    python -m ml.training.train \
        --features-dir ml/artifacts/features/ \
        --output-dir ml/artifacts/ \
        [--epochs 50] [--batch-size 64] [--lr 0.001]

Requirements: torch, numpy
"""

from __future__ import annotations

import argparse
import logging
import pickle
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split

from ml.model.model import build_model
from ml.model.model_config import ModelConfig, DEFAULT_CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_features(features_dir: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load pre-extracted features and labels."""
    features_dir = Path(features_dir)
    features_path = features_dir / "features.npy"
    labels_path = features_dir / "labels.npy"

    if not features_path.exists():
        raise FileNotFoundError(
            f"Features not found at {features_path}. "
            "Run ml/preprocessing/extract_features.py first."
        )

    features = np.load(str(features_path))  # [N, T, M]
    labels = np.load(str(labels_path))       # [N]
    logger.info("Loaded features: %s  labels: %s", features.shape, labels.shape)
    return features, labels


def prepare_tensors(
    features: np.ndarray,
    labels: np.ndarray,
    config: ModelConfig,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Normalize and reshape features for the model."""
    # Load or compute normalization stats
    norm_path = Path(config.normalization_stats_path)
    if norm_path.exists():
        stats = np.load(str(norm_path))
        mean = stats["mean"]
        std = stats["std"]
        logger.info("Loaded normalization stats from %s", norm_path)
    else:
        mean = features.reshape(-1, features.shape[-1]).mean(axis=0)
        std = features.reshape(-1, features.shape[-1]).std(axis=0)
        std = np.where(std > 1e-8, std, 1.0)
        norm_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(str(norm_path), mean=mean, std=std)
        logger.info("Saved normalization stats to %s", norm_path)

    features_norm = (features - mean[np.newaxis, np.newaxis, :]) / std[np.newaxis, np.newaxis, :]
    features_norm = features_norm.astype(np.float32)

    # Add channel dim: [N, T, M] → [N, 1, T, M]
    X = torch.from_numpy(features_norm[:, np.newaxis, :, :])
    y = torch.from_numpy(labels.astype(np.int64))
    return X, y


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    """Run one training epoch. Returns (avg_loss, accuracy)."""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(y_batch)
        preds = logits.argmax(dim=1)
        correct += (preds == y_batch).sum().item()
        total += len(y_batch)

    return total_loss / total, correct / total


@torch.no_grad()
def eval_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    """Evaluate model. Returns (avg_loss, accuracy)."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        total_loss += loss.item() * len(y_batch)
        preds = logits.argmax(dim=1)
        correct += (preds == y_batch).sum().item()
        total += len(y_batch)

    return total_loss / total, correct / total


def train(config: ModelConfig = DEFAULT_CONFIG, args=None):
    # CLI overrides
    if args:
        if hasattr(args, "epochs") and args.epochs:
            config.epochs = args.epochs
        if hasattr(args, "batch_size") and args.batch_size:
            config.batch_size = args.batch_size
        if hasattr(args, "lr") and args.lr:
            config.learning_rate = args.lr
        if hasattr(args, "features_dir") and args.features_dir:
            config.features_dir = args.features_dir
        if hasattr(args, "output_dir") and args.output_dir:
            config.model_save_path = str(Path(args.output_dir) / "model.pth")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Training device: %s", device)

    # Load data
    features, labels = load_features(config.features_dir)
    X, y = prepare_tensors(features, labels, config)

    # Split: 80% train, 20% val (from loaded features)
    # Note: proper speaker-split is done in split_dataset.py
    n = len(X)
    n_val = max(1, int(n * 0.2))
    n_train = n - n_val
    dataset = TensorDataset(X, y)
    train_ds, val_ds = random_split(
        dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_ds, batch_size=config.batch_size, shuffle=True,
                              num_workers=0, pin_memory=device.type == "cuda")
    val_loader = DataLoader(val_ds, batch_size=config.batch_size, shuffle=False, num_workers=0)

    # Model
    model = build_model(config).to(device)
    logger.info("Parameters: %d (%.1f K)", model.count_parameters(),
                model.count_parameters() / 1000)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.StepLR(
        optimizer, step_size=config.lr_step_size, gamma=config.lr_gamma
    )

    best_val_acc = 0.0
    output_path = Path(config.model_save_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting training: %d epochs", config.epochs)
    for epoch in range(1, config.epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc = eval_epoch(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        logger.info(
            "Epoch %3d/%d | train loss %.4f acc %.3f | val loss %.4f acc %.3f | %.1fs",
            epoch, config.epochs, train_loss, train_acc, val_loss, val_acc, elapsed
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "config": config,
            }, str(output_path))
            logger.info("  → Saved best model (val_acc=%.3f)", val_acc)

    logger.info("Training complete. Best val accuracy: %.3f", best_val_acc)
    logger.info("Model saved to: %s", output_path)
    return model, best_val_acc


def main():
    parser = argparse.ArgumentParser(description="Train DS-CNN keyword spotting model")
    parser.add_argument("--features-dir", default=DEFAULT_CONFIG.features_dir)
    parser.add_argument("--output-dir", default="ml/artifacts/")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    args = parser.parse_args()

    train(DEFAULT_CONFIG, args)


if __name__ == "__main__":
    main()

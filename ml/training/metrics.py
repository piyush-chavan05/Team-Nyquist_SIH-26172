"""
metrics.py — Evaluation metrics for KWS model.

Provides: accuracy, confusion matrix, per-class precision/recall/F1.
"""

from __future__ import annotations

from typing import List

import numpy as np


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Overall classification accuracy."""
    if len(y_true) == 0:
        return 0.0
    return float((y_true == y_pred).mean())


def confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int,
) -> np.ndarray:
    """
    Compute confusion matrix.

    Returns:
        Array of shape [n_classes, n_classes] where cm[i, j] = number of
        samples of true class i predicted as class j.
    """
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < n_classes and 0 <= p < n_classes:
            cm[t, p] += 1
    return cm


def per_class_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int,
    class_names: List[str] | None = None,
) -> List[dict]:
    """
    Compute precision, recall, F1 per class.

    Returns list of dicts with keys: class, precision, recall, f1, support.
    """
    cm = confusion_matrix(y_true, y_pred, n_classes)
    results = []
    for i in range(n_classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = cm[i, :].sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)
               if (precision + recall) > 0 else 0.0)

        name = class_names[i] if class_names and i < len(class_names) else str(i)
        results.append({
            "class": name,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(support),
        })
    return results


def print_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int,
    class_names: List[str] | None = None,
):
    """Print a formatted classification report."""
    acc = accuracy(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, n_classes)
    per_class = per_class_metrics(y_true, y_pred, n_classes, class_names)

    print(f"\nOverall accuracy: {acc:.4f}  ({(y_true == y_pred).sum()}/{len(y_true)})\n")

    # Per-class table
    header = f"{'Class':>12}  {'Precision':>10}  {'Recall':>8}  {'F1':>8}  {'Support':>8}"
    print(header)
    print("-" * len(header))
    for m in per_class:
        print(f"  {m['class']:>10}  {m['precision']:>10.4f}  {m['recall']:>8.4f}"
              f"  {m['f1']:>8.4f}  {m['support']:>8}")

    # Confusion matrix
    names = class_names or [str(i) for i in range(n_classes)]
    print(f"\nConfusion matrix (rows=true, cols=predicted):")
    header_cm = "         " + "  ".join(f"{n:>8}" for n in names)
    print(header_cm)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>8}" for v in row)
        print(f"  {names[i]:>6}  {row_str}")
    print()

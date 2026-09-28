"""
split_dataset.py — Split dataset into train / validation / test sets.

Supports splitting by speaker to prevent data leakage.

Usage:
    python ml/dataset/split_dataset.py \
        --data-dir ml/dataset/data/ \
        --output-dir ml/dataset/splits/ \
        --train 0.70 --val 0.15 --test 0.15 \
        --split-by speaker
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CLASSES = ["keyword", "unknown", "silence"]


def collect_files_by_speaker(data_dir: Path) -> dict:
    """
    Walk dataset and group files by (class, speaker).

    Returns:
        {class_name: {speaker_id: [Path, ...]}}
    """
    grouped: dict = {cls: defaultdict(list) for cls in CLASSES}

    for cls in CLASSES:
        cls_dir = data_dir / cls
        if not cls_dir.exists():
            continue
        for wav in sorted(cls_dir.rglob("*.wav")) + sorted(cls_dir.rglob("*.WAV")):
            speaker = wav.parent.name
            grouped[cls][speaker].append(wav)

    return grouped


def split_by_speaker(
    grouped: dict,
    train_frac: float,
    val_frac: float,
    test_frac: float,
    seed: int = 42,
) -> dict:
    """
    Split speakers (not files) into train/val/test.

    Returns:
        {"train": {cls: [Path,...]}, "val": ..., "test": ...}
    """
    rng = random.Random(seed)
    splits = {"train": {cls: [] for cls in CLASSES},
              "val":   {cls: [] for cls in CLASSES},
              "test":  {cls: [] for cls in CLASSES}}

    for cls in CLASSES:
        speakers = sorted(grouped[cls].keys())
        rng.shuffle(speakers)

        n = len(speakers)
        n_test = max(1, round(n * test_frac)) if n > 2 else min(1, n)
        n_val = max(1, round(n * val_frac)) if n > 2 else min(1, n - n_test)
        n_train = n - n_val - n_test

        if n_train < 1:
            logger.warning("Class '%s': too few speakers (%d) for a clean 3-way split", cls, n)
            # Fallback: all to train
            for spk in speakers:
                splits["train"][cls].extend(grouped[cls][spk])
            continue

        train_spk = speakers[:n_train]
        val_spk = speakers[n_train:n_train + n_val]
        test_spk = speakers[n_train + n_val:]

        for spk in train_spk:
            splits["train"][cls].extend(grouped[cls][spk])
        for spk in val_spk:
            splits["val"][cls].extend(grouped[cls][spk])
        for spk in test_spk:
            splits["test"][cls].extend(grouped[cls][spk])

    return splits


def split_by_file(
    grouped: dict,
    train_frac: float,
    val_frac: float,
    test_frac: float,
    seed: int = 42,
) -> dict:
    """
    Split individual files (not speaker-aware).

    Use only when speaker metadata is not available.
    """
    rng = random.Random(seed)
    splits = {"train": {cls: [] for cls in CLASSES},
              "val":   {cls: [] for cls in CLASSES},
              "test":  {cls: [] for cls in CLASSES}}

    for cls in CLASSES:
        all_files = []
        for spk_files in grouped[cls].values():
            all_files.extend(spk_files)
        rng.shuffle(all_files)

        n = len(all_files)
        n_test = round(n * test_frac)
        n_val = round(n * val_frac)
        n_train = n - n_val - n_test

        splits["train"][cls] = all_files[:n_train]
        splits["val"][cls] = all_files[n_train:n_train + n_val]
        splits["test"][cls] = all_files[n_train + n_val:]

    return splits


def save_splits(splits: dict, output_dir: Path):
    """Save split file lists to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name, class_files in splits.items():
        split_data = {}
        for cls, paths in class_files.items():
            split_data[cls] = [str(p) for p in paths]
        out_path = output_dir / f"{split_name}.json"
        with open(out_path, "w") as f:
            json.dump(split_data, f, indent=2)
        total = sum(len(v) for v in split_data.values())
        logger.info("Saved %s: %d files → %s", split_name, total, out_path)


def main():
    parser = argparse.ArgumentParser(description="Split KWS dataset into train/val/test")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--test", type=float, default=0.15)
    parser.add_argument("--split-by", choices=["speaker", "file"], default="speaker",
                        help="'speaker': prevent speaker leakage (recommended). "
                             "'file': random file split.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if abs(args.train + args.val + args.test - 1.0) > 1e-6:
        parser.error("train + val + test must sum to 1.0")

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    grouped = collect_files_by_speaker(data_dir)

    if args.split_by == "speaker":
        splits = split_by_speaker(grouped, args.train, args.val, args.test, args.seed)
    else:
        splits = split_by_file(grouped, args.train, args.val, args.test, args.seed)

    save_splits(splits, output_dir)

    print("\nSplit summary:")
    for split_name in ["train", "val", "test"]:
        totals = {cls: len(splits[split_name][cls]) for cls in CLASSES}
        total = sum(totals.values())
        print(f"  {split_name:5s}: {total:4d} files  |  "
              + "  ".join(f"{cls}: {c}" for cls, c in totals.items()))
    print()


if __name__ == "__main__":
    main()

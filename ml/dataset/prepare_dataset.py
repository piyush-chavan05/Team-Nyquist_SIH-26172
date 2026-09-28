"""
prepare_dataset.py — Inspect dataset directory and report statistics.

Usage:
    python ml/dataset/prepare_dataset.py --data-dir ml/dataset/data/
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from collections import defaultdict

import soundfile as sf

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EXPECTED_SR = 16_000
CLASSES = ["keyword", "unknown", "silence"]


def inspect_dataset(data_dir: Path) -> dict:
    """
    Walk dataset directory and collect statistics per class.

    Returns:
        Dict mapping class_name -> {count, total_duration_s, speakers, issues}
    """
    stats = {}

    for cls in CLASSES:
        cls_dir = data_dir / cls
        if not cls_dir.exists():
            logger.warning("Class directory not found: %s", cls_dir)
            stats[cls] = {"count": 0, "total_duration_s": 0.0, "speakers": set(), "issues": []}
            continue

        wav_files = list(cls_dir.rglob("*.wav")) + list(cls_dir.rglob("*.WAV"))
        count = 0
        total_duration = 0.0
        speakers = set()
        issues = []

        for f in wav_files:
            # Speaker is the immediate parent directory name
            speaker = f.parent.name
            speakers.add(speaker)

            try:
                info = sf.info(str(f))
                duration_s = info.frames / info.samplerate
                total_duration += duration_s
                count += 1

                if info.samplerate != EXPECTED_SR:
                    issues.append(f"{f.name}: SR={info.samplerate} (expected {EXPECTED_SR})")
                if info.channels > 2:
                    issues.append(f"{f.name}: {info.channels} channels")
                if duration_s < 0.1:
                    issues.append(f"{f.name}: very short ({duration_s:.3f}s)")
            except Exception as exc:
                issues.append(f"{f.name}: cannot read ({exc})")

        stats[cls] = {
            "count": count,
            "total_duration_s": total_duration,
            "speakers": speakers,
            "issues": issues,
        }

    return stats


def main():
    parser = argparse.ArgumentParser(description="Inspect KWS dataset")
    parser.add_argument("--data-dir", required=True, help="Root dataset directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("Data directory not found: %s", data_dir)
        return

    stats = inspect_dataset(data_dir)

    print("\n=== Dataset Statistics ===\n")
    total_files = 0
    for cls, s in stats.items():
        total_files += s["count"]
        print(f"  {cls:12s}: {s['count']:4d} files  |  "
              f"{s['total_duration_s']:7.1f} s  |  "
              f"{len(s['speakers'])} speaker(s)")
        if s["issues"]:
            print(f"    Issues ({len(s['issues'])}):")
            for issue in s["issues"][:10]:
                print(f"      - {issue}")
            if len(s["issues"]) > 10:
                print(f"      ... and {len(s['issues']) - 10} more")

    print(f"\n  Total files: {total_files}")

    if total_files == 0:
        print("\n  *** No data found. See docs/dataset.md for collection instructions. ***\n")
    else:
        # Class balance check
        counts = {cls: stats[cls]["count"] for cls in CLASSES}
        max_count = max(counts.values()) if counts.values() else 1
        print("\n  Class balance:")
        for cls, c in counts.items():
            ratio = c / max_count if max_count > 0 else 0
            bar = "█" * int(ratio * 20)
            print(f"    {cls:12s}: {bar:<20s} {c}")
        print()


if __name__ == "__main__":
    main()

"""
validate_dataset.py — Validate all audio files in the dataset directory.

Checks: WAV format, sample rate, channel count, duration, file integrity.

Usage:
    python ml/dataset/validate_dataset.py --data-dir ml/dataset/data/
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import soundfile as sf

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EXPECTED_SR = 16_000
MIN_DURATION_S = 0.1
MAX_DURATION_S = 10.0


def validate_file(path: Path) -> dict:
    """Validate a single audio file. Returns a result dict."""
    errors = []
    warnings = []

    try:
        info = sf.info(str(path))
    except Exception as exc:
        return {"path": path, "ok": False, "errors": [f"Cannot read: {exc}"], "warnings": []}

    duration_s = info.frames / info.samplerate if info.samplerate > 0 else 0.0

    if info.samplerate != EXPECTED_SR:
        warnings.append(f"SR={info.samplerate} (expected {EXPECTED_SR}, will be resampled)")
    if info.channels != 1:
        warnings.append(f"channels={info.channels} (expected 1 — will be converted to mono)")
    if duration_s < MIN_DURATION_S:
        errors.append(f"Too short: {duration_s:.3f}s (min {MIN_DURATION_S}s)")
    if duration_s > MAX_DURATION_S:
        warnings.append(f"Long clip: {duration_s:.1f}s (max expected {MAX_DURATION_S}s)")

    # Try reading a small portion to catch corrupted files
    try:
        sf.read(str(path), frames=256, dtype="float32")
    except Exception as exc:
        errors.append(f"Cannot read audio data: {exc}")

    return {
        "path": path,
        "ok": len(errors) == 0,
        "sr": info.samplerate,
        "channels": info.channels,
        "duration_s": duration_s,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate KWS dataset audio files")
    parser.add_argument("--data-dir", required=True, help="Root dataset directory")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("Data directory not found: %s", data_dir)
        return

    wav_files = list(data_dir.rglob("*.wav")) + list(data_dir.rglob("*.WAV"))
    if not wav_files:
        print("No WAV files found. See docs/dataset.md for collection instructions.")
        return

    print(f"\nValidating {len(wav_files)} files in {data_dir}\n")

    ok_count = 0
    error_count = 0
    warning_count = 0

    for wav_path in sorted(wav_files):
        result = validate_file(wav_path)
        if result["ok"] and not result.get("warnings"):
            ok_count += 1
        elif result["errors"]:
            error_count += 1
            rel = wav_path.relative_to(data_dir)
            print(f"  ERROR   {rel}")
            for e in result["errors"]:
                print(f"           ✗ {e}")
        elif result.get("warnings"):
            warning_count += 1
            if args.strict:
                error_count += 1
                rel = wav_path.relative_to(data_dir)
                print(f"  WARNING {rel}")
                for w in result["warnings"]:
                    print(f"           ⚠ {w}")
            else:
                ok_count += 1  # Warnings are non-fatal

    print(f"\nResults: {ok_count} ok  |  {warning_count} warnings  |  {error_count} errors")
    if error_count > 0:
        print("Fix errors before training.")
    else:
        print("All files validated successfully.")
    print()


if __name__ == "__main__":
    main()

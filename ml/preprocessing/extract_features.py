"""
extract_features.py — End-to-end feature extraction script.

Usage:
    python ml/preprocessing/extract_features.py \
        --data-dir ml/dataset/data/ \
        --output-dir ml/artifacts/features/ \
        [--frame-size 400] [--hop-size 160] [--n-mels 40]
"""

from __future__ import annotations

import argparse
import logging
import pickle
from pathlib import Path

import numpy as np

from .audio_io import load_wav, validate_wav, TARGET_SR
from .framing import frame_audio, hann_window, apply_window, FRAME_SIZE, HOP_SIZE
from .mel_features import compute_log_mel, N_MELS, N_FFT

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

LABEL_MAP = {"keyword": 0, "unknown": 1, "silence": 2}


def extract_for_file(
    path: Path,
    frame_size: int = FRAME_SIZE,
    hop_size: int = HOP_SIZE,
    n_fft: int = N_FFT,
    n_mels: int = N_MELS,
    target_duration_s: float = 1.0,
) -> np.ndarray:
    """
    Load a WAV file and return a fixed-length Log-Mel feature array.

    Returns:
        Float32 array of shape [n_frames, n_mels].
        Padded or truncated to target_duration_s.
    """
    info = validate_wav(path)
    if not info["ok"]:
        logger.warning("Skipping %s: %s", path.name, info["errors"])
        return None

    audio, sr = load_wav(path, target_sr=TARGET_SR)

    # Pad or trim to target length
    target_samples = int(target_duration_s * sr)
    if len(audio) < target_samples:
        audio = np.pad(audio, (0, target_samples - len(audio)))
    elif len(audio) > target_samples:
        audio = audio[:target_samples]

    # Frame → window → Log-Mel
    frames = frame_audio(audio, frame_size=frame_size, hop_size=hop_size)
    window = hann_window(frame_size)
    windowed = apply_window(frames, window)
    log_mel = compute_log_mel(windowed, n_fft=n_fft)

    return log_mel


def main():
    parser = argparse.ArgumentParser(description="Extract Log-Mel features from dataset")
    parser.add_argument("--data-dir", required=True, help="Root dataset directory")
    parser.add_argument("--output-dir", required=True, help="Output directory for features")
    parser.add_argument("--frame-size", type=int, default=FRAME_SIZE)
    parser.add_argument("--hop-size", type=int, default=HOP_SIZE)
    parser.add_argument("--n-mels", type=int, default=N_MELS)
    parser.add_argument("--n-fft", type=int, default=N_FFT)
    parser.add_argument("--duration", type=float, default=1.0, help="Target clip duration (s)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_features = []
    all_labels = []
    skipped = 0

    for class_name, label in LABEL_MAP.items():
        class_dir = data_dir / class_name
        if not class_dir.exists():
            logger.warning("Class directory not found: %s", class_dir)
            continue

        wav_files = list(class_dir.rglob("*.wav")) + list(class_dir.rglob("*.WAV"))
        logger.info("Class '%s': found %d files", class_name, len(wav_files))

        for wav_path in wav_files:
            features = extract_for_file(
                wav_path,
                frame_size=args.frame_size,
                hop_size=args.hop_size,
                n_fft=args.n_fft,
                n_mels=args.n_mels,
                target_duration_s=args.duration,
            )
            if features is None:
                skipped += 1
                continue
            all_features.append(features)
            all_labels.append(label)

    if not all_features:
        logger.error("No features extracted. Check data directory and file formats.")
        return

    features_array = np.array(all_features, dtype=np.float32)
    labels_array = np.array(all_labels, dtype=np.int64)

    logger.info("Feature matrix shape: %s", features_array.shape)
    logger.info("Labels shape: %s", labels_array.shape)
    logger.info("Skipped: %d files", skipped)

    # Class distribution
    for class_name, label in LABEL_MAP.items():
        count = (labels_array == label).sum()
        logger.info("  %s: %d samples", class_name, count)

    # Save
    np.save(output_dir / "features.npy", features_array)
    np.save(output_dir / "labels.npy", labels_array)

    # Save metadata
    metadata = {
        "frame_size": args.frame_size,
        "hop_size": args.hop_size,
        "n_fft": args.n_fft,
        "n_mels": args.n_mels,
        "sample_rate": TARGET_SR,
        "duration_s": args.duration,
        "n_samples": len(all_features),
        "label_map": LABEL_MAP,
    }
    with open(output_dir / "metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)

    logger.info("Saved features to %s", output_dir)


if __name__ == "__main__":
    main()

"""
record_samples.py — Record wake word samples using the host microphone.

Captures WAV files for building the keyword dataset.
Recordings are saved to ml/dataset/data/{class_name}/{speaker_id}/

Usage:
    python scripts/record_samples.py \
        --class keyword \
        --speaker speaker_001 \
        --n-samples 50 \
        --output-dir ml/dataset/data/

Requirements:
    pip install sounddevice soundfile

    To list available audio devices:
    python -c "import sounddevice; print(sounddevice.query_devices())"
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np


def record_sample(duration_s: float = 1.0, sr: int = 16_000, device=None) -> np.ndarray:
    """Record one audio clip from the microphone."""
    try:
        import sounddevice as sd
    except ImportError:
        raise ImportError("Install sounddevice: pip install sounddevice")

    n_samples = int(duration_s * sr)
    audio = sd.rec(n_samples, samplerate=sr, channels=1, dtype="float32", device=device)
    sd.wait()
    return audio[:, 0]


def save_wav(audio: np.ndarray, path: Path, sr: int = 16_000):
    import soundfile as sf
    sf.write(str(path), audio, sr)


def main():
    parser = argparse.ArgumentParser(description="Record wake word samples")
    parser.add_argument("--class", dest="cls", required=True,
                        choices=["keyword", "unknown", "silence"],
                        help="Class label for these recordings")
    parser.add_argument("--speaker", required=True,
                        help="Speaker ID (e.g. speaker_001)")
    parser.add_argument("--n-samples", type=int, default=50,
                        help="Number of samples to record")
    parser.add_argument("--output-dir", default="ml/dataset/data/",
                        help="Root dataset directory")
    parser.add_argument("--duration", type=float, default=1.0,
                        help="Duration of each recording in seconds")
    parser.add_argument("--pause", type=float, default=0.5,
                        help="Pause between recordings (seconds)")
    parser.add_argument("--device", type=int, default=None,
                        help="Audio input device index (see sounddevice.query_devices())")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) / args.cls / args.speaker
    output_dir.mkdir(parents=True, exist_ok=True)

    # Count existing recordings
    existing = list(output_dir.glob("*.wav"))
    start_idx = len(existing) + 1

    print(f"\nRecording {args.n_samples} × '{args.cls}' clips for speaker '{args.speaker}'")
    print(f"Output: {output_dir}")
    print(f"Duration: {args.duration}s  |  Pause: {args.pause}s\n")
    print("Press Ctrl+C to stop early.\n")

    try:
        for i in range(args.n_samples):
            idx = start_idx + i
            filename = f"{args.cls}_{idx:04d}.wav"
            path = output_dir / filename

            print(f"  [{i + 1}/{args.n_samples}] Ready. Say the wake word... ", end="", flush=True)
            time.sleep(args.pause)
            print("RECORDING...", end="", flush=True)

            audio = record_sample(duration_s=args.duration, device=args.device)
            save_wav(audio, path)

            rms = float(np.sqrt((audio ** 2).mean()))
            print(f" done  (RMS: {rms:.4f})  → {filename}")

            if rms < 0.001:
                print("    ⚠ Very quiet clip — check microphone input level")

    except KeyboardInterrupt:
        print("\n\nRecording stopped early.")

    wav_count = len(list(output_dir.glob("*.wav")))
    print(f"\nTotal recordings in {output_dir}: {wav_count}")
    print("Run ml/dataset/validate_dataset.py to check all files.\n")


if __name__ == "__main__":
    main()

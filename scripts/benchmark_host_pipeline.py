"""
benchmark_host_pipeline.py — Benchmark host-side audio preprocessing pipeline.

Measures: framing time, feature extraction time, model inference time (if available).

NOTE: These are HOST-side measurements.
Embedded measurements must be done on ESP32-S3 hardware.
Do NOT report these numbers as embedded performance.

Usage:
    python scripts/benchmark_host_pipeline.py [--n-iters 100]
"""

from __future__ import annotations

import argparse
import time
import sys
from pathlib import Path

import numpy as np

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.preprocessing.framing import frame_audio, hann_window, apply_window
from ml.preprocessing.mel_features import compute_log_mel

SAMPLE_RATE = 16_000
FRAME_SIZE = 400
HOP_SIZE = 160
N_MELS = 40


def time_fn(fn, n_iters: int = 100):
    """Run fn n_iters times and return (mean_ms, std_ms, min_ms)."""
    times = []
    for _ in range(n_iters):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    times_arr = np.array(times)
    return times_arr.mean(), times_arr.std(), times_arr.min()


def benchmark_framing(n_iters: int):
    audio = np.random.randn(SAMPLE_RATE).astype(np.float32)  # 1 second
    window = hann_window(FRAME_SIZE)

    def run():
        frames = frame_audio(audio, FRAME_SIZE, HOP_SIZE)
        apply_window(frames, window)

    mean, std, mn = time_fn(run, n_iters)
    print(f"  Framing + windowing (1s audio):  {mean:.2f} ± {std:.2f} ms  (min: {mn:.2f} ms)")
    return mean


def benchmark_feature_extraction(n_iters: int):
    audio = np.random.randn(SAMPLE_RATE).astype(np.float32)
    window = hann_window(FRAME_SIZE)
    frames = frame_audio(audio, FRAME_SIZE, HOP_SIZE)
    windowed = apply_window(frames, window)

    def run():
        compute_log_mel(windowed)

    mean, std, mn = time_fn(run, n_iters)
    print(f"  Log-Mel extraction (1s audio):   {mean:.2f} ± {std:.2f} ms  (min: {mn:.2f} ms)")
    return mean


def benchmark_model_inference(n_iters: int):
    """Benchmark model inference if torch is available."""
    try:
        import torch
        from ml.model.model import build_model
        from ml.model.model_config import DEFAULT_CONFIG

        model = build_model(DEFAULT_CONFIG)
        model.eval()

        # Feature window shape: [1, 1, n_time_steps, n_mels]
        config = DEFAULT_CONFIG
        dummy = torch.zeros(1, 1, config.n_time_steps, config.n_mels)

        @torch.no_grad()
        def run():
            model(dummy)

        mean, std, mn = time_fn(run, n_iters)
        n_params = model.count_parameters()
        size_kb = model.model_size_kb()
        print(f"  DS-CNN inference (host/CPU):     {mean:.2f} ± {std:.2f} ms  (min: {mn:.2f} ms)")
        print(f"    Parameters: {n_params:,} ({n_params/1000:.1f} K) | Float32 size: {size_kb:.1f} KB")
        print(f"    NOTE: Embedded inference latency must be measured on ESP32-S3 hardware.")
        return mean
    except ImportError:
        print("  DS-CNN inference: skipped (torch not installed)")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark host-side audio pipeline (NOT embedded measurements)"
    )
    parser.add_argument("--n-iters", type=int, default=100,
                        help="Number of benchmark iterations (default: 100)")
    args = parser.parse_args()

    n = args.n_iters
    print(f"\n=== Host-side Pipeline Benchmark (n={n}) ===")
    print("  Platform: Python {}.{}.{}".format(*sys.version_info[:3]))
    print("  WARNING: These are host measurements. Embedded performance MUST be measured separately.\n")

    benchmark_framing(n)
    benchmark_feature_extraction(n)
    benchmark_model_inference(n)

    print(f"\nBenchmark complete.\n")


if __name__ == "__main__":
    main()

# Scripts

Utility scripts for dataset preparation, benchmarking, server testing, and environment setup.

## Available scripts

| Script | Purpose | Requirements |
|---|---|---|
| `setup_python.py` | Create venv + install deps | Python 3.10+ |
| `record_samples.py` | Record wake word samples via host mic | sounddevice, soundfile |
| `benchmark_host_pipeline.py` | Benchmark framing + features + inference | numpy, scipy, soundfile, (torch) |
| `test_server.py` | Quick integration test for ASR server | stdlib only |

## Usage

```bash
# Setup
python scripts/setup_python.py

# Record samples
python scripts/record_samples.py \
    --class keyword \
    --speaker speaker_001 \
    --n-samples 50

# Benchmark host pipeline
python scripts/benchmark_host_pipeline.py --n-iters 100

# Test server (run server first)
uvicorn server.app:app --host 0.0.0.0 --port 8080 &
python scripts/test_server.py
```

> **Important:** `benchmark_host_pipeline.py` measures HOST performance only.
> Embedded latency must be measured on physical ESP32-S3 hardware.

# Tests

Host-side unit tests for the voice activator project.

## Running tests

```bash
# Install dependencies first
.\scripts\setup_python.ps1   # Windows
# or
bash scripts/setup_python.sh

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_audio.py -v
pytest tests/test_features.py -v
pytest tests/test_ring_buffer.py -v
pytest tests/test_wake_logic.py -v
pytest tests/test_protocol.py -v
```

## Test coverage

| Test file | What is tested |
|---|---|
| `test_audio.py` | WAV loading, mono conversion, resampling, framing, windowing |
| `test_features.py` | Mel filterbank, log-Mel extraction, determinism, edge cases |
| `test_ring_buffer.py` | Ring buffer write/read, wraparound, overflow, pre-roll retrieval |
| `test_wake_logic.py` | Threshold, temporal confirmation, cooldown, noise adaptation bounds |
| `test_protocol.py` | Header validation, PCM encoding, response format, end-of-command |

## Hardware-dependent tests

The following cannot be tested without physical hardware:
- ESP32-S3 audio capture quality
- Embedded feature extraction accuracy vs host reference
- KWS inference latency on target
- Ring buffer behavior under DMA pressure
- Wi-Fi streaming stability

These are documented in `docs/benchmarking.md`.

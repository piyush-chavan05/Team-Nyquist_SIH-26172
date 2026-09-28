# Implementation Plan

## Development phases

---

### Phase 1 — Repository setup ✅

- Initialize Git repository
- Create `.gitignore`, `LICENSE`, `AGENTS.md`
- Write main `README.md`
- Create documentation structure
- Create utility scripts

---

### Phase 2 — Host audio pipeline ✅

- Implement WAV loading (`ml/preprocessing/audio_io.py`)
- Implement framing and windowing (`ml/preprocessing/framing.py`)
- Implement Mel filterbank and log transformation (`ml/preprocessing/mel_features.py`)
- Implement end-to-end feature extraction (`ml/preprocessing/extract_features.py`)
- Write tests: `tests/test_audio.py`, `tests/test_features.py`
- Run tests

---

### Phase 3 — Dataset tooling ✅

- Define dataset directory convention (`docs/dataset.md`)
- Implement dataset inspection (`ml/dataset/prepare_dataset.py`)
- Implement sample rate and format validation (`ml/dataset/validate_dataset.py`)
- Implement train/validation/test split (`ml/dataset/split_dataset.py`)
- Generate labels
- Report class balance

---

### Phase 4 — DS-CNN model ✅

- Define model configuration (`ml/model/model_config.py`)
- Implement DS-CNN architecture (`ml/model/model.py`)
- Implement training script (`ml/training/train.py`)
- Implement evaluation script (`ml/training/evaluate.py`)
- Implement metrics (`ml/training/metrics.py`)
- Implement TFLite export (`ml/model/export.py`)

> **Awaiting:** wake word recordings (positive and negative samples).
> Model architecture and training code exist. Trained weights pending data.

---

### Phase 5 — ESP32-S3 audio acquisition 🔶 Hardware-dependent

- Select exact ESP32-S3 development board
- Select digital MEMS microphone
- Confirm digital audio interface (PDM or I²S)
- Implement correct ESP-IDF driver for selected microphone
- Verify 16 kHz mono capture
- Verify continuous ring-buffer write

---

### Phase 6 — Embedded feature extraction 🔶 Hardware-dependent

- Port Log-Mel pipeline to ESP32-S3 C implementation
- Validate feature output matches host Python reference
- Measure execution time on target
- Optimize if necessary (fixed-point arithmetic, lookup tables)

---

### Phase 7 — Embedded KWS 🔶 Hardware-dependent

- Select embedded inference runtime (TFLite Micro or ESP-DL)
- Document runtime trade-offs
- Integrate trained model
- Run inference on ESP32-S3
- Validate classification output

---

### Phase 8 — Wake detection logic 🔶 Hardware-dependent

- Configure threshold (initial `0.80` — requires tuning)
- Implement temporal confirmation
- Implement cooldown
- Implement noise-adaptive threshold adjustment
- Tune on real hardware in different noise conditions

---

### Phase 9 — Command capture ✅ (firmware scaffolded, hardware validation pending)

- Implement state machine transitions
- Implement pre-roll retrieval from ring buffer
- Capture audio after wake until end-of-command

---

### Phase 10 — Wi-Fi 🔶 Hardware-dependent

- Configure Wi-Fi credentials via `menuconfig`
- Implement connection/reconnection logic
- Validate TCP/IP stack on hardware

---

### Phase 11 — ASR server ✅ (scaffolded)

- Implement FastAPI server (`server/app.py`)
- Implement audio reception
- Implement configurable ASR backend
- Validate server runs independently on host

---

### Phase 12 — Integration 🔶 Hardware-dependent

- Connect ESP32-S3 to host ASR server
- End-to-end command test: wake word → command → recognized text
- Fix integration issues

---

### Phase 13 — Measurement 🔶 Hardware-dependent

- Measure runtime RAM
- Measure CPU utilization during continuous listening
- Measure KWS inference time
- Run false-activation test over controlled period
- Measure wake-to-ASR latency

---

### Phase 14 — Optimization 🔶 Hardware-dependent

- If RAM > 256 KB: reduce buffer sizes, quantize model further
- If CPU > 10%: optimize feature extraction, reduce inference frequency
- If false activations too high: tune threshold / confirmation window

---

### Phase 15 — Final validation 🔶 Hardware-dependent

- Functional test (wake word → confirm)
- Negative test (normal speech → no wake)
- Noise test (multiple environments)
- Distance test (multiple distances)
- False activation test (measured rate)
- Resource test (RAM, CPU, inference time)
- End-to-end test (wake → ASR result)
- Record conditions and update `benchmarks/RESULTS.md`

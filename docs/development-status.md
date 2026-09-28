# Development Status

Last updated: 2026-09-28

---

## Status legend

| Symbol | Meaning |
|---|---|
| ✅ Complete | Implemented and tested |
| 🔄 In progress | Being actively implemented |
| 🔶 Hardware-dependent | Cannot proceed without physical hardware |
| ❌ Planned | Not yet started |

---

## Stage 0 — Repository foundation

| Item | Status |
|---|---|
| Git repository initialized | ✅ Complete |
| `.gitignore` | ✅ Complete |
| `LICENSE` | ✅ Complete |
| `AGENTS.md` | ✅ Complete |
| Main `README.md` | ✅ Complete |
| `docs/` structure | ✅ Complete |
| `scripts/` setup | ✅ Complete |

---

## Stage 1 — Host audio pipeline

| Item | Status |
|---|---|
| WAV loading and validation | ✅ Complete |
| Sample rate check / resampling | ✅ Complete |
| Mono conversion | ✅ Complete |
| Framing with overlap | ✅ Complete |
| Hann windowing | ✅ Complete |
| FFT | ✅ Complete |
| Mel filterbank | ✅ Complete |
| Log transformation | ✅ Complete |
| Feature extraction script | ✅ Complete |
| Audio pipeline tests | ✅ Complete |

---

## Stage 2 — Dataset tooling + DS-CNN model

| Item | Status |
|---|---|
| Dataset directory convention | ✅ Complete |
| Dataset inspection script | ✅ Complete |
| Sample rate / format validation | ✅ Complete |
| Train / validation / test split | ✅ Complete |
| Class balance reporting | ✅ Complete |
| DS-CNN model architecture | ✅ Complete |
| Model configuration | ✅ Complete |
| Training script | ✅ Complete |
| Evaluation script | ✅ Complete |
| Metrics (accuracy, confusion matrix) | ✅ Complete |
| TFLite export script | ✅ Complete |
| Actual trained model | ❌ Pending recordings |
| Training accuracy | ❌ Pending recordings |

---

## Stage 3 — ESP-IDF firmware foundation

| Item | Status |
|---|---|
| ESP-IDF project structure | ✅ Scaffolded |
| `CMakeLists.txt` | ✅ Scaffolded |
| `sdkconfig.defaults` | ✅ Scaffolded |
| `partitions.csv` | ✅ Scaffolded |
| `main.c` | ✅ Scaffolded |
| `app_controller` | ✅ Scaffolded |
| `audio_capture` abstraction | ✅ Scaffolded |
| `ring_buffer` | ✅ Scaffolded |
| `feature_extractor` interface | ✅ Scaffolded |
| `kws` inference interface | ✅ Scaffolded |
| `wake_detector` | ✅ Scaffolded |
| `state_machine` | ✅ Scaffolded |
| `network/wifi` | ✅ Scaffolded |
| `network/audio_stream` | ✅ Scaffolded |
| `diagnostics` | ✅ Scaffolded |
| Physical ESP-IDF compilation | 🔶 Hardware-dependent |

---

## Stage 4 — Embedded KWS integration

| Item | Status |
|---|---|
| Model runtime selection (TFLite Micro / ESP-DL) | 🔶 Hardware-dependent |
| Model deployment to ESP32-S3 | 🔶 Hardware-dependent |
| Embedded feature extraction validation | 🔶 Hardware-dependent |
| KWS inference on target | 🔶 Hardware-dependent |
| Wake threshold tuning on target | 🔶 Hardware-dependent |

---

## Stage 5 — Network + ASR server

| Item | Status |
|---|---|
| Remote ASR server (FastAPI) | ✅ Scaffolded |
| ASR backend interface | ✅ Scaffolded |
| Audio reception | ✅ Scaffolded |
| Protocol definition | ✅ Complete |
| Protocol tests | ✅ Complete |
| Wi-Fi firmware module | ✅ Scaffolded |
| Audio stream firmware module | ✅ Scaffolded |
| End-to-end hardware streaming | 🔶 Hardware-dependent |

---

## Stage 6 — Integration

| Item | Status |
|---|---|
| Host pipeline integration | ✅ Complete |
| Hardware end-to-end | 🔶 Hardware-dependent |

---

## Stage 7 — Benchmark framework

| Item | Status |
|---|---|
| Host benchmark scripts | ✅ Complete |
| `RESULTS.md` template | ✅ Complete |
| Hardware measurements | 🔶 Hardware-dependent |

---

## Stage 8 — Final documentation pass

| Item | Status |
|---|---|
| README | ✅ Complete |
| Architecture | ✅ Complete |
| Implementation plan | ✅ Complete |
| Hardware documentation | ✅ Complete |
| Audio pipeline documentation | ✅ Complete |
| KWS design documentation | ✅ Complete |
| Dataset documentation | ✅ Complete |
| Protocol documentation | ✅ Complete |
| Benchmarking documentation | ✅ Complete |

---

## Hardware-dependent checklist

```
[ ] ESP32-S3 board selected
[ ] Digital MEMS microphone selected
[ ] Interface confirmed (PDM/I²S)
[ ] Wiring verified
[ ] 16 kHz capture verified
[ ] Continuous audio capture verified
[ ] Embedded feature extraction verified
[ ] KWS model deployed
[ ] Wake threshold tuned
[ ] Ring buffer verified on hardware
[ ] Wi-Fi streaming verified
[ ] Remote ASR verified end-to-end
[ ] End-to-end command verified
[ ] RAM measured
[ ] CPU measured
[ ] Inference time measured
[ ] False activations/hour measured
[ ] Wake-to-ASR latency measured
```

---

## Known blockers

1. **Wake word not finalized** — placeholder `hey_activator` used throughout. Training cannot begin until recordings are collected.
2. **ESP32-S3 board not selected** — firmware cannot be physically compiled or flashed.
3. **Microphone not selected** — I²S/PDM driver cannot be finalized.
4. **No training data** — model architecture exists but trained weights are pending.

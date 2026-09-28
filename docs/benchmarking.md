# Benchmarking

## Overview

This document defines the benchmarking methodology for the project. All metrics will be populated only after actual measurements are performed on physical hardware.

> **No hardware measurements have been performed. All measured values in RESULTS.md are TBD.**

---

## Metrics

### 1. Runtime RAM

**Definition:** The actual RAM used by the running KWS application during continuous listening, measured on the ESP32-S3.

**Measurement method:**
- Use `esp_get_free_heap_size()` before and after application initialization
- Use FreeRTOS heap reporting
- Compare with total available SRAM

**Target:** < 256 KB

**Status:** Pending hardware.

---

### 2. CPU utilization during continuous listening

**Definition:** The fraction of CPU time consumed by the KWS loop (audio capture + feature extraction + inference) during continuous listening, excluding Wi-Fi and command capture.

**Measurement method:**
- FreeRTOS task runtime stats (`vTaskGetRunTimeStats()`)
- Compare KWS task ticks to total system ticks

**Target:** < 10%

**Status:** Pending hardware.

---

### 3. KWS inference time

**Definition:** Time from the start of model inference to the output (confidence values), for one audio window.

**Measurement method:**
- Use `esp_timer_get_time()` or a hardware timer before and after `model_infer()`

**Target:** Minimize (must fit within one hop period, i.e., < 10 ms, for real-time operation)

**Status:** Pending hardware.

---

### 4. False activations per hour

**Definition:** Number of spurious wake detections when the wake word is not spoken, measured over a defined test period.

**Measurement method:**
1. Play controlled non-keyword audio (conversation, music, background noise) for at least 1 hour.
2. Count all wake events logged by the system.
3. Report as: `false_activations / test_duration_hours`

**Test conditions to document:**
- Audio source
- Volume level
- Distance
- Background noise level
- Threshold setting used

**Target:** Minimize.

**Status:** Pending field test.

---

### 5. Wake-to-ASR latency

**Definition:** Time from the moment the wake word is confirmed by the system to the moment the ASR server returns a recognized result.

**Measurement method:**
1. Record `T_wake` = timestamp when `WAKE_DETECTED` state is entered (from ESP32-S3 log).
2. Record `T_asr` = timestamp when ASR response is received.
3. Compute: `latency = T_asr - T_wake`

**Includes:**
- Pre-roll + command audio capture time
- Wi-Fi transmission time
- ASR processing time

**Test conditions to document:**
- Wi-Fi network type
- Network latency
- Command length
- ASR model used
- Server hardware

**Target:** Minimize.

**Status:** Pending end-to-end test.

---

## Host-side benchmarks (software only)

These can be measured without hardware:

### Feature extraction throughput

Measures the time to extract Log-Mel features for a 1-second audio window on the host machine.

```bash
python benchmarks/benchmark_audio_pipeline.py
```

### Model inference throughput (host)

Measures time to run one DS-CNN forward pass on the host CPU.

```bash
python benchmarks/benchmark_host.py
```

---

## Results

See [`benchmarks/RESULTS.md`](../benchmarks/RESULTS.md) for the results table.

---

## Recording conditions template

When hardware results become available, record:

```
Test date:
Hardware: ESP32-S3 [board model], [microphone model]
Firmware commit:
Firmware version:
Test environment:
  Room: [e.g., office, quiet room]
  Background noise level: [dB if measured, or qualitative]
  Distance: [cm from microphone]
  Volume: [quiet/normal/loud]
ASR server:
  Machine:
  ASR backend:
  Network type: [e.g., local Wi-Fi, 2.4 GHz]
Threshold: [value used]
Temporal confirmation: [N windows]
```

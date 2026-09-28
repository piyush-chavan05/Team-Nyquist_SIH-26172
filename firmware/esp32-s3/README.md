# ESP32-S3 Firmware

## Status

> **SCAFFOLDED — Hardware-dependent.** The firmware project structure is complete and designed as a real ESP-IDF project. Physical compilation requires ESP-IDF to be installed. Flashing and functional validation require the physical ESP32-S3 board and selected digital MEMS microphone.

## Building

```bash
# 1. Install ESP-IDF (v5.x recommended)
#    https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/

# 2. Set target
idf.py set-target esp32s3

# 3. Configure (set Wi-Fi credentials, server IP, etc.)
idf.py menuconfig

# 4. Build
idf.py build

# 5. Flash and monitor (requires physical board)
# idf.py flash monitor
```

## Directory structure

```
main/
├── main.c                    ← app_main entry
├── CMakeLists.txt
├── app/
│   ├── app_controller.c/h    ← top-level orchestrator
├── audio/
│   ├── audio_config.h        ← centralized constants (SYNC WITH Python!)
│   ├── audio_capture.c/h     ← I2S/PDM microphone abstraction
├── buffer/
│   ├── ring_buffer.c/h       ← fixed-size ring buffer + pre-roll
├── features/
│   ├── feature_extractor.c/h ← Log-Mel spectrogram (ESP-DSP)
├── kws/
│   ├── kws.c/h               ← DS-CNN inference interface
│   ├── kws_model.c/h         ← model loading stub
├── wake/
│   ├── wake_detector.c/h     ← threshold + confirmation + noise adapt
├── state/
│   ├── state_machine.c/h     ← LISTENING → COMMAND_CAPTURE → STREAMING
├── network/
│   ├── wifi.c/h              ← Wi-Fi STA
│   ├── audio_stream.c/h      ← HTTP command audio streaming
└── diagnostics/
    ├── diagnostics.c/h       ← runtime logging + heap reporting
```

## Hardware-dependent checklist

```
[ ] ESP32-S3 board selected
[ ] Digital MEMS microphone selected
[ ] Interface confirmed (PDM/I²S)
[ ] Pin assignments set in audio_capture.c
[ ] 16 kHz capture verified
[ ] Feature extraction validated vs Python reference
[ ] KWS model deployed (model.tflite in SPIFFS)
[ ] Model runtime integrated (TFLite Micro or ESP-DL)
[ ] Wake threshold tuned
[ ] Wi-Fi credentials set via menuconfig
[ ] ASR server IP set via menuconfig
[ ] End-to-end test passed
[ ] RAM measured
[ ] CPU measured
```

## Key design notes

- **audio_config.h** constants MUST match `ml/preprocessing/mel_features.py` exactly.
- **Wi-Fi credentials** are never in source — use `idf.py menuconfig`.
- **KWS model** is a stub until TFLite Micro or ESP-DL runtime is integrated.
- **audio_capture.c** pin numbers are placeholders — set after microphone selection.

# Audio Pipeline

## Pipeline overview

```
Digital MEMS Microphone
        │
        │ PDM or I²S (interface TBD)
        ▼
ESP32-S3 Audio Capture
        │
        │ 16 kHz · Mono · 16-bit PCM
        ▼
Ring Buffer (continuous write)
        │
        │ overlapping frames
        ▼
Frame Extraction
  - Frame size:   400 samples (25 ms at 16 kHz)
  - Hop size:     160 samples (10 ms at 16 kHz)
  - Overlap:      60% (240 samples)
        │
        ▼
Hann Window (applied per frame)
        │
        ▼
FFT (N = 512 points)
        │
        │ magnitude spectrum
        ▼
Mel Filterbank
  - Number of Mel bins: 40
  - Frequency range: 20 Hz – 8,000 Hz (Nyquist for 16 kHz)
        │
        ▼
Logarithm (log(x + 1e-6) to avoid log(0))
        │
        ▼
Log-Mel Feature Matrix
  - Shape: [time_steps × 40]
  - Covering approximately 1 second: ~98 frames
        │
        ▼
DS-CNN Input
```

---

## Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Sample rate | 16,000 Hz | Standard for speech / KWS |
| Channels | 1 (mono) | Single microphone; simplifies processing |
| Bit depth | 16-bit PCM | Balance of dynamic range and memory |
| Raw data rate | 32,000 bytes/sec | 16,000 × 2 bytes |
| Frame size | 400 samples (25 ms) | Standard STFT frame for speech |
| Hop size | 160 samples (10 ms) | 60% overlap; captures transitions |
| FFT size | 512 points | Next power of 2 above 400 |
| Mel bins | 40 | Compact representation; proven for KWS |
| Frequency range | 20 – 8,000 Hz | Human speech range |
| Feature window | ~1 second | Typical keyword duration |

---

## Frame math

```
Frame duration    = 400 / 16,000 = 25 ms
Hop duration      = 160 / 16,000 = 10 ms
Frames per second = 16,000 / 160 = 100 frames/sec
Frames in 1 sec   ≈ 98 frames (= (16000 - 400) / 160 + 1)
Feature shape     = [98, 40]
```

---

## Consistency between training and inference

The preprocessing parameters are centralized in `ml/preprocessing/mel_features.py` (Python/training) and `firmware/esp32-s3/main/audio/audio_config.h` (C/firmware). Both must use identical values to prevent train/inference mismatch.

Any change to parameters (frame size, hop size, Mel bins, FFT size) must be applied to **both** locations.

---

## Hann window

A Hann window is applied to each frame before FFT:

```python
w[n] = 0.5 * (1 - cos(2π·n / (N-1)))
```

This reduces spectral leakage at frame boundaries.

---

## Mel filterbank

The Mel scale approximates human auditory perception. The filterbank converts linear-frequency FFT bins to Mel-spaced triangular filters.

Mel frequency conversion:
```
mel(f) = 2595 × log10(1 + f/700)
f(mel) = 700 × (10^(mel/2595) - 1)
```

Filterbank matrix size: `[40, (FFT_SIZE/2 + 1)] = [40, 257]`

---

## Normalization

Log-Mel features may be globally normalized (mean/std) or per-utterance normalized depending on what produces better model performance. The decision must be consistent between training and inference.

Current implementation: per-feature global normalization (mean and std computed from training set, stored alongside model artifact).

---

## Implementation locations

| Component | Location |
|---|---|
| Python audio I/O | `ml/preprocessing/audio_io.py` |
| Python framing | `ml/preprocessing/framing.py` |
| Python Mel features | `ml/preprocessing/mel_features.py` |
| Python end-to-end extraction | `ml/preprocessing/extract_features.py` |
| C audio config (constants) | `firmware/esp32-s3/main/audio/audio_config.h` |
| C feature extractor | `firmware/esp32-s3/main/features/feature_extractor.c` |

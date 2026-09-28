# KWS Design

## Keyword Spotting (KWS) overview

KWS is the task of detecting a specific spoken keyword (the wake word) in a continuous audio stream. It is a classification problem: given a short audio window, classify it as "keyword", "unknown speech", or "silence/background".

---

## Wake word

The wake word is **configurable**. A placeholder (`hey_activator`) is used throughout the codebase.

The final wake word will be decided by the project owner and must be:
- Short (1–3 syllables recommended for reliability)
- Phonetically distinct from common words in the target environment
- Consistently pronounceable by target users

---

## Training data requirements

### Positive samples (keyword class)

Recordings of the wake word spoken by multiple speakers.

Variation required:
- Multiple speakers (different gender, age, accent)
- Different volumes (quiet, normal, loud)
- Different distances from microphone
- Different microphone positions
- Different rooms (different reverb characteristics)
- With and without background noise

Minimum recommended: 50–200+ utterances per class for a prototype. More is better.

### Negative samples (unknown class)

Speech that is **not** the wake word.

Must include:
- Ordinary conversation and commands
- Phonetically similar words and phrases
- Random vocabulary
- Silence
- Background audio (fan, traffic, music)

Negative samples should at minimum equal positive samples in count.

### Noise samples (silence/background class)

Pure background recordings without speech:
- Silent room
- Fan noise
- Office/traffic noise
- Music

---

## Feature representation — Log-Mel spectrogram

See [`audio-pipeline.md`](audio-pipeline.md) for full pipeline details.

Input to the DS-CNN:
- Shape: `[time_steps × 40]` (approximately `[98 × 40]` for 1 second)
- Values: log-Mel spectrogram coefficients
- Normalization: global mean/std from training set

Log-Mel is preferred over MFCC for this project because:
- Retains more spectral information
- More common in recent KWS literature
- Easily reproduced on embedded targets

---

## Model — DS-CNN

**Depthwise Separable Convolutional Neural Network**

### Architecture motivation

Depthwise separable convolutions factorize a standard convolution into:
1. A depthwise convolution (one filter per input channel)
2. A pointwise convolution (1×1 conv to combine channels)

This reduces computation by approximately a factor of `1/N_channels + 1/k²` relative to standard convolutions, making the model suitable for edge inference.

### Architecture (compact variant)

```
Input: [batch, time_steps, n_mels, 1]
  │
  ▼ Conv2D (32 filters, 3×3, BN, ReLU)
  ▼ DS Block 1: DepthwiseConv2D + Conv2D (64 filters, 1×1, BN, ReLU)
  ▼ DS Block 2: DepthwiseConv2D + Conv2D (64 filters, 1×1, BN, ReLU)
  ▼ DS Block 3: DepthwiseConv2D + Conv2D (128 filters, 1×1, BN, ReLU)
  ▼ DS Block 4: DepthwiseConv2D + Conv2D (128 filters, 1×1, BN, ReLU)
  ▼ Global Average Pooling
  ▼ Dropout(0.25)
  ▼ Dense(n_classes, softmax)
Output: [batch, n_classes]
```

All parameters are configurable in `ml/model/model_config.py`.

### Classes

| Class | Label | Description |
|---|---|---|
| 0 | keyword | The target wake word |
| 1 | unknown | Other speech |
| 2 | silence | Background / silence |

Number of classes is configurable.

### Reported model metrics

> **Not yet measured** — requires trained model with actual recordings.

The following will be reported after training:
- Total parameter count
- Model size (MB)
- Host inference time (ms per window)
- Training accuracy
- Validation accuracy
- Test accuracy
- Confusion matrix
- Per-class precision, recall, F1

Embedded metrics (inference time on ESP32-S3, RAM) are pending hardware validation.

---

## Wake detection logic

### Confidence threshold

The DS-CNN outputs a softmax probability for each class. The keyword class probability is the confidence score.

```
confidence = model_output[keyword_class]
```

If `confidence ≥ threshold`, the window is flagged as a potential wake event.

**Default threshold:** `0.80` (development value — not validated).
**Final threshold:** must be tuned experimentally on hardware.

### Temporal confirmation

A single high-confidence window is not sufficient to declare a wake event. Multiple consecutive windows must exceed the threshold:

```
confirmed_windows = 0
for each new window:
    if confidence ≥ threshold:
        confirmed_windows += 1
    else:
        confirmed_windows = 0  # or allow small gaps
    if confirmed_windows ≥ N_CONFIRM:
        → WAKE DETECTED
```

**Default:** `N_CONFIRM = 3` (configurable).

### Cooldown

After a wake event is triggered, a cooldown period prevents repeated triggers from the same utterance:

**Default cooldown:** 2 seconds (configurable).

### Gap tolerance

Up to `MAX_GAP` windows below threshold between confirmed windows may be tolerated (to handle brief dips). This is configurable and should be set cautiously.

**Default MAX_GAP:** 1 (configurable).

---

## Noise-adaptive detection

### Motivation

The optimal threshold depends on the noise environment:
- In a quiet room: a stricter (higher) threshold reduces false activations.
- In a noisy environment: a slightly lower threshold may be necessary to maintain sensitivity.

### Implementation

1. **Background energy estimation:** During LISTENING state (non-wake), compute the RMS energy of each audio frame.
2. **Smoothed noise estimate:** Apply exponential moving average (EMA):
   ```
   noise_estimate = alpha * frame_energy + (1 - alpha) * noise_estimate
   ```
   Default `alpha = 0.05` (slow adaptation — configurable).
3. **Noise level classification:** Map noise estimate to a discrete noise level (low / moderate / high).
4. **Threshold adjustment:** Apply a small offset to the base threshold:
   ```
   threshold = base_threshold + noise_offset[noise_level]
   threshold = clamp(threshold, MIN_THRESHOLD, MAX_THRESHOLD)
   ```
5. **Logging:** Log the selected threshold for diagnostics.

### Configuration

| Parameter | Default | Meaning |
|---|---|---|
| `base_threshold` | 0.80 | Starting threshold |
| `alpha` | 0.05 | EMA smoothing factor |
| `noise_offset_low` | +0.05 | Offset for quiet environment |
| `noise_offset_moderate` | 0.00 | No offset for moderate noise |
| `noise_offset_high` | -0.05 | Offset for noisy environment |
| `MIN_THRESHOLD` | 0.65 | Minimum allowed threshold |
| `MAX_THRESHOLD` | 0.95 | Maximum allowed threshold |

These values are configurable and must be tuned based on real-environment testing.

### What this is not

This is a **simple deterministic rule**, not a second neural network. The adaptation is bounded, logged, and does not allow the detector to become arbitrarily sensitive.

---

## False activation targets

- False activations: **minimize** (target: < measured/hour — pending field test)
- Missed detections: **minimize** (target: high true positive rate — pending evaluation)

Both metrics are in tension. The threshold and confirmation settings control this trade-off.

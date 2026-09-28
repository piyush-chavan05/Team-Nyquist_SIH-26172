# Dataset Documentation

## Overview

The KWS model requires a custom dataset of the chosen wake word. This document explains how to collect, organize, and use the dataset.

**Dataset status: ❌ Pending — no recordings collected yet.**

> Do not commit private voice recordings to this repository. Audio files belong in `ml/dataset/data/` which is in `.gitignore`.

---

## Directory convention

```
ml/dataset/data/
├── keyword/               ← positive samples (wake word)
│   ├── speaker_001/
│   │   ├── kw_001.wav
│   │   ├── kw_002.wav
│   │   └── ...
│   ├── speaker_002/
│   │   └── ...
│   └── ...
│
├── unknown/               ← negative samples (other speech)
│   ├── speaker_001/
│   │   └── ...
│   └── ...
│
└── silence/               ← background / silence samples
    ├── quiet_room/
    │   └── ...
    ├── fan_noise/
    │   └── ...
    └── ...
```

Subdirectories under `keyword/` and `unknown/` should be named by speaker ID to support speaker-level train/test splitting (prevents speaker leakage).

---

## Audio format requirements

| Property | Required value |
|---|---|
| Format | WAV (PCM) |
| Sample rate | 16,000 Hz |
| Channels | Mono (1 channel) |
| Bit depth | 16-bit |
| Duration | 0.5 – 2.0 seconds per clip |

Files not meeting these requirements will be flagged by `validate_dataset.py`. The preprocessing scripts will attempt sample rate conversion if needed.

---

## Positive samples — collection guide

Record the **wake word** being spoken.

**Variation to include:**

| Variation | Notes |
|---|---|
| Speakers | At least 3–5 different people for prototype |
| Gender | Mix if possible |
| Volume | Quiet, normal, and loud |
| Distance | 0.5 m, 1 m, 2 m from microphone |
| Microphone position | Front, side, behind a surface |
| Room | Different rooms / acoustic environments |
| Background | Quiet, with fan, with light background noise |
| Pronunciation | Allow natural variation |

**Recommended minimum for prototype:** 100–200 clips.

---

## Negative samples — collection guide

Record speech that is **not** the wake word.

Must include:

| Type | Examples |
|---|---|
| General conversation | Any topic |
| Similar-sounding words/phrases | Phonetically close to wake word |
| Random vocabulary | Common commands, numbers, names |
| Silence | Empty audio files |
| Background noise | Fan, traffic, office, music |

Negative samples should be at least as numerous as positive samples.

---

## Environmental variation

Where possible, collect recordings in:

- Quiet room (< 40 dB background)
- Room with fan noise (~ 50–60 dB)
- Room with traffic/background noise
- At multiple distances (0.5 m, 1 m, 2 m)
- At different speaking volumes (quiet, normal, loud)

---

## Recording procedure

1. Use any WAV recorder (smartphone, computer microphone, or target digital MEMS microphone if available).
2. Record individual clips of the wake word — one utterance per file.
3. Leave ~0.1 second of silence before and after the spoken word.
4. Save as 16 kHz mono 16-bit WAV.
5. Place files in the appropriate directory.

---

## Dataset validation

Run the validation script to check all files:

```bash
python ml/dataset/validate_dataset.py --data-dir ml/dataset/data/
```

This checks:
- File format (WAV)
- Sample rate
- Channel count
- Duration
- File corruption

---

## Dataset split

Run the split script to create train/validation/test partitions:

```bash
python ml/dataset/split_dataset.py \
    --data-dir ml/dataset/data/ \
    --output-dir ml/dataset/splits/ \
    --train 0.70 \
    --val 0.15 \
    --test 0.15 \
    --split-by speaker
```

`--split-by speaker` ensures no speaker appears in both training and test sets (prevents data leakage).

---

## Class balance

The `prepare_dataset.py` script reports class balance. If classes are highly imbalanced, consider:

- Collecting more data for underrepresented classes
- Using class weights during training
- Data augmentation (time stretching, pitch shift, additive noise)

---

## Privacy

Do not commit private voice recordings to this repository. The `data/` directory is in `.gitignore`.

If recordings are intended for public release, add them to a separate public data release with appropriate consent documentation.

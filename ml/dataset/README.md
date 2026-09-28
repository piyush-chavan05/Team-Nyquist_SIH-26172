# Dataset

This directory contains dataset preparation tooling.

## Audio data location

Audio files live in `ml/dataset/data/` (not committed — see `.gitignore`).

See [`docs/dataset.md`](../../docs/dataset.md) for collection instructions.

## Directory layout expected by tools

```
ml/dataset/data/
├── keyword/       ← wake word recordings
│   ├── speaker_001/
│   │   └── *.wav
│   └── ...
├── unknown/       ← other speech
└── silence/       ← background / silence
```

## Scripts

| Script | Purpose |
|---|---|
| `prepare_dataset.py` | Inspect dataset, report statistics |
| `validate_dataset.py` | Check format and sample rate of all files |
| `split_dataset.py` | Create train/val/test splits |

## Usage

```bash
# Inspect
python ml/dataset/prepare_dataset.py --data-dir ml/dataset/data/

# Validate all files
python ml/dataset/validate_dataset.py --data-dir ml/dataset/data/

# Split
python ml/dataset/split_dataset.py \
    --data-dir ml/dataset/data/ \
    --output-dir ml/dataset/splits/ \
    --train 0.70 --val 0.15 --test 0.15
```

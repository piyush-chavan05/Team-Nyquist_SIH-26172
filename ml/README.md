# ML Pipeline

This directory contains the complete host-side machine learning pipeline.

## Subdirectories

| Directory | Contents |
|---|---|
| `preprocessing/` | Audio I/O, framing, Log-Mel feature extraction |
| `dataset/` | Dataset inspection, validation, train/val/test splitting |
| `model/` | DS-CNN architecture, config, TFLite export |
| `training/` | Training loop, evaluation, metrics |
| `artifacts/` | Generated files (features, checkpoints, models) — mostly gitignored |

## Quick start

```bash
# 1. Set up environment
.\scripts\setup_python.ps1   # Windows
# or
bash scripts/setup_python.sh  # Linux/macOS

# 2. Collect recordings into ml/dataset/data/
#    See docs/dataset.md for instructions

# 3. Validate dataset
python -m ml.dataset.validate_dataset --data-dir ml/dataset/data/

# 4. Inspect dataset statistics
python -m ml.dataset.prepare_dataset --data-dir ml/dataset/data/

# 5. Split dataset (speaker-aware)
python -m ml.dataset.split_dataset \
    --data-dir ml/dataset/data/ \
    --output-dir ml/dataset/splits/

# 6. Extract Log-Mel features
python -m ml.preprocessing.extract_features \
    --data-dir ml/dataset/data/ \
    --output-dir ml/artifacts/features/

# 7. Train DS-CNN
python -m ml.training.train \
    --features-dir ml/artifacts/features/ \
    --output-dir ml/artifacts/

# 8. Evaluate
python -m ml.training.evaluate \
    --model ml/artifacts/model.pth \
    --features-dir ml/artifacts/features/

# 9. Export to TFLite
python -m ml.model.export \
    --model ml/artifacts/model.pth \
    --output-dir ml/artifacts/
```

## Requirements

See `requirements.txt` in this directory.

## Status

- Pipeline implemented: ✅
- Dataset collected: ❌ Pending recordings
- Trained model: ❌ Pending recordings
- TFLite export: ✅ Script ready (requires trained model)
- Embedded deployment: 🔶 Hardware-dependent

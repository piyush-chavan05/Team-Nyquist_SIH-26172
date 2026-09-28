# Model

This directory contains the DS-CNN model architecture, configuration, and export tooling.

## Files

| File | Purpose |
|---|---|
| `model_config.py` | All model hyperparameters in one place |
| `model.py` | DS-CNN architecture (PyTorch) |
| `export.py` | Export trained model to TFLite for ESP32-S3 |

## Architecture summary

```
Input: [batch, 1, n_time_steps=98, n_mels=40]
  │
  ├── Conv2D(32, 3×3) + BN + ReLU
  ├── DS Block: DW Conv(3×3) + PW Conv(64) + BN + ReLU  ×2
  ├── DS Block: DW Conv(3×3) + PW Conv(128) + BN + ReLU ×2
  ├── Global Average Pooling → [batch, 128]
  ├── Dropout(0.25)
  └── Linear(128 → 3)  →  [keyword, unknown, silence]
```

## Export path

```
PyTorch (.pth)
    → ONNX (.onnx)        [via torch.onnx.export]
    → TF SavedModel       [via onnx-tf]
    → TFLite (.tflite)    [via tf.lite.TFLiteConverter]
    → ESP32-S3            [via TFLite Micro or ESP-DL]
```

> **Embedded runtime (TFLite Micro vs ESP-DL) not yet decided.**
> Decision depends on library compatibility with selected ESP-IDF version.
> Both paths are documented in `docs/kws-design.md`.

## Artifacts

Trained model artifacts live in `ml/artifacts/` (not committed if large).

| Artifact | Description |
|---|---|
| `model.pth` | PyTorch checkpoint |
| `model.onnx` | ONNX intermediate |
| `model.tflite` | TFLite for deployment |
| `norm_stats.npz` | Feature normalization mean/std |
| `features/features.npy` | Extracted feature matrix |
| `features/labels.npy` | Labels array |

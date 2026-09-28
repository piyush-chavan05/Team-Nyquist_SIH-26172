"""
config.py — ASR server configuration.

All settings are read from environment variables.
Copy .env.example to .env and fill in values.
"""

from __future__ import annotations

import os

# Server bind address
HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
PORT: int = int(os.getenv("SERVER_PORT", "8080"))

# ASR backend: "vosk", "whisper", "faster_whisper", "stub"
ASR_BACKEND: str = os.getenv("ASR_BACKEND", "stub")

# Model path (backend-specific)
ASR_MODEL_PATH: str = os.getenv("ASR_MODEL_PATH", "")

# Audio validation
EXPECTED_SAMPLE_RATE: int = 16_000
EXPECTED_CHANNELS: int = 1
EXPECTED_BIT_DEPTH: int = 16
MAX_AUDIO_DURATION_S: float = 10.0

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

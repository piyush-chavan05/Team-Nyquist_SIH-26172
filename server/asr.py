"""
asr.py — ASR backend abstraction.

Supports multiple configurable backends:
  - stub: returns placeholder text (for development without a model)
  - vosk: Vosk offline ASR (recommended — open-source, runs locally)
  - whisper: OpenAI Whisper (heavier, requires GPU or CPU patience)
  - faster_whisper: CTranslate2-optimized Whisper

Select backend via ASR_BACKEND environment variable.
"""

from __future__ import annotations

import logging
import io
from typing import Optional

import numpy as np

from . import config

logger = logging.getLogger(__name__)


class ASRResult:
    def __init__(self, text: str, confidence: Optional[float] = None):
        self.text = text
        self.confidence = confidence


class ASRBackend:
    """Base class for ASR backends."""
    def recognize(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        raise NotImplementedError


class StubBackend(ASRBackend):
    """Placeholder backend for development without a real ASR model."""
    def recognize(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        logger.debug("StubBackend: returning placeholder result")
        return ASRResult(
            text="[stub: no ASR model loaded — set ASR_BACKEND and ASR_MODEL_PATH]",
            confidence=0.0,
        )


class VoskBackend(ASRBackend):
    """
    Vosk offline ASR backend.
    Install: pip install vosk
    Model: download from https://alphacephei.com/vosk/models
    Set ASR_MODEL_PATH to the extracted model directory.
    """
    def __init__(self, model_path: str):
        try:
            from vosk import Model, KaldiRecognizer
            import json as _json
            self._json = _json
            self._KaldiRecognizer = KaldiRecognizer
            self._model = Model(model_path)
            logger.info("Vosk model loaded from: %s", model_path)
        except ImportError as exc:
            raise ImportError("Install vosk: pip install vosk") from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to load Vosk model: {exc}") from exc

    def recognize(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        rec = self._KaldiRecognizer(self._model, sample_rate)
        # Vosk expects 16-bit PCM bytes
        pcm = (audio * 32767).astype(np.int16).tobytes()
        rec.AcceptWaveform(pcm)
        result = self._json.loads(rec.FinalResult())
        text = result.get("text", "").strip()
        confidence = result.get("confidence", None)
        return ASRResult(text=text, confidence=confidence)


class WhisperBackend(ASRBackend):
    """
    OpenAI Whisper backend.
    Install: pip install openai-whisper
    Set ASR_MODEL_PATH to model name (e.g., "base", "small").
    """
    def __init__(self, model_name: str = "base"):
        try:
            import whisper
            self._model = whisper.load_model(model_name)
            logger.info("Whisper model loaded: %s", model_name)
        except ImportError as exc:
            raise ImportError("Install whisper: pip install openai-whisper") from exc

    def recognize(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        result = self._model.transcribe(audio, language="en")
        text = result.get("text", "").strip()
        return ASRResult(text=text, confidence=None)


class FasterWhisperBackend(ASRBackend):
    """
    Faster-Whisper (CTranslate2) backend.
    Install: pip install faster-whisper
    """
    def __init__(self, model_name: str = "base"):
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(model_name, device="cpu", compute_type="int8")
            logger.info("Faster-Whisper model loaded: %s", model_name)
        except ImportError as exc:
            raise ImportError("Install faster-whisper: pip install faster-whisper") from exc

    def recognize(self, audio: np.ndarray, sample_rate: int) -> ASRResult:
        segments, _ = self._model.transcribe(audio, language="en")
        text = " ".join(seg.text for seg in segments).strip()
        return ASRResult(text=text, confidence=None)


def build_backend() -> ASRBackend:
    """Construct the configured ASR backend."""
    backend_name = config.ASR_BACKEND.lower()
    model_path = config.ASR_MODEL_PATH

    logger.info("ASR backend: %s", backend_name)

    if backend_name == "stub":
        return StubBackend()
    elif backend_name == "vosk":
        if not model_path:
            raise ValueError("ASR_MODEL_PATH must be set for Vosk backend")
        return VoskBackend(model_path)
    elif backend_name == "whisper":
        return WhisperBackend(model_path or "base")
    elif backend_name == "faster_whisper":
        return FasterWhisperBackend(model_path or "base")
    else:
        logger.warning("Unknown ASR backend '%s' — using stub", backend_name)
        return StubBackend()

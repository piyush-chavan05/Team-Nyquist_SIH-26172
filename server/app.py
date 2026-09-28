"""
app.py — Remote ASR server.

Receives command audio from ESP32-S3 over HTTP,
performs speech recognition, returns result as JSON.

Run:
    python server/app.py
    # or
    uvicorn server.app:app --host 0.0.0.0 --port 8080

Endpoints:
    POST /recognize   — Submit command audio, get recognized text
    GET  /health      — Health check
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from . import config
from .audio import validate_headers, pcm_bytes_to_float, validate_audio_data, AudioValidationError
from .asr import build_backend, ASRBackend
from .protocol import success_response, error_response

# ── Logging ──────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Global ASR backend (initialized at startup) ───────
_asr_backend: ASRBackend | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _asr_backend
    logger.info("Starting ASR server")
    logger.info("Backend: %s", config.ASR_BACKEND)
    logger.info("Model path: %s", config.ASR_MODEL_PATH or "(none)")
    _asr_backend = build_backend()
    yield
    logger.info("Shutting down ASR server")


app = FastAPI(
    title="Voice Activator ASR Server",
    description="Remote ASR server for Low Latency Voice Activator (SIH project)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "backend": config.ASR_BACKEND}


@app.post("/recognize")
async def recognize(request: Request):
    """
    Receive raw 16-bit PCM audio and return recognized text.

    Expected headers:
        Content-Type: application/octet-stream
        X-Sample-Rate: 16000
        X-Channels: 1
        X-Bit-Depth: 16
    """
    t_start = time.monotonic()

    # Validate headers
    try:
        validate_headers(dict(request.headers))
    except AudioValidationError as exc:
        logger.warning("Header validation failed: %s", exc)
        return JSONResponse(
            status_code=400,
            content=error_response("invalid_audio", str(exc)),
        )

    # Read body
    try:
        body = await request.body()
    except Exception as exc:
        logger.error("Failed to read request body: %s", exc)
        return JSONResponse(
            status_code=400,
            content=error_response("read_error", "Failed to read audio data"),
        )

    if not body:
        return JSONResponse(
            status_code=400,
            content=error_response("empty_audio", "No audio data received"),
        )

    # Decode PCM
    try:
        audio = pcm_bytes_to_float(body, bit_depth=16)
        validate_audio_data(audio, config.EXPECTED_SAMPLE_RATE)
    except AudioValidationError as exc:
        logger.warning("Audio validation failed: %s", exc)
        return JSONResponse(
            status_code=400,
            content=error_response("invalid_audio", str(exc)),
        )

    logger.info("Received audio: %.2f s (%d samples)", len(audio) / config.EXPECTED_SAMPLE_RATE, len(audio))

    # Run ASR
    try:
        result = _asr_backend.recognize(audio, config.EXPECTED_SAMPLE_RATE)
    except Exception as exc:
        logger.error("ASR failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content=error_response("asr_failed", f"ASR error: {exc}"),
        )

    duration_ms = int((time.monotonic() - t_start) * 1000)
    logger.info("ASR result: '%s' (%d ms)", result.text, duration_ms)

    return JSONResponse(
        content=success_response(
            text=result.text,
            confidence=result.confidence,
            duration_ms=duration_ms,
        )
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.app:app",
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower(),
    )

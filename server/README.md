# Remote ASR Server

## Overview

The ASR server receives command audio from the ESP32-S3 over Wi-Fi after wake word confirmation. It performs speech recognition and returns the recognized command text.

## Status

✅ **Scaffolded** — Runs independently on host. ASR backend is configurable. End-to-end with hardware pending.

## Quick start

```bash
cd server/
pip install -r requirements.txt
cp .env.example .env   # edit as needed
python -m server.app
# or
uvicorn server.app:app --host 0.0.0.0 --port 8080
```

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/recognize` | POST | Submit PCM audio, receive transcription |
| `/health` | GET | Server health check |

## ASR backends

| Backend | Config value | Install |
|---|---|---|
| Stub (no model) | `stub` | Built-in |
| Vosk (offline) | `vosk` | `pip install vosk` |
| OpenAI Whisper | `whisper` | `pip install openai-whisper` |
| Faster-Whisper | `faster_whisper` | `pip install faster-whisper` |

Set `ASR_BACKEND` in `.env` to select.

## Protocol

See [`docs/protocol.md`](../docs/protocol.md).

Audio format expected: 16 kHz · Mono · 16-bit PCM · raw bytes (no WAV header).

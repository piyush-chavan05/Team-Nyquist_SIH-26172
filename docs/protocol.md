# Communication Protocol

## Overview

After the wake word is confirmed, the ESP32-S3 streams command audio to the remote ASR server over Wi-Fi. This document defines the protocol.

**Protocol status:** HTTP streaming with binary framing is the current implementation. WebSocket may be evaluated as an alternative.

---

## Transport

- **Primary:** HTTP POST with chunked transfer encoding
- **Alternative under evaluation:** WebSocket (allows bidirectional streaming)

The server URL and port are configurable. Default: `http://<server-ip>:8080/recognize`

---

## Connection setup

1. ESP32-S3 connects to Wi-Fi AP (credentials configured at build time via `menuconfig`).
2. On wake confirmation, ESP32-S3 opens a TCP connection to the ASR server.
3. ESP32-S3 sends audio stream.
4. ESP32-S3 reads response.
5. Connection closes.

---

## Audio format

Audio sent to the server is:

| Property | Value |
|---|---|
| Format | Raw PCM (no WAV header in stream) |
| Sample rate | 16,000 Hz |
| Channels | Mono |
| Bit depth | 16-bit signed little-endian |

---

## Message framing (HTTP mode)

### Request

```
POST /recognize HTTP/1.1
Host: <server>:<port>
Content-Type: application/octet-stream
X-Sample-Rate: 16000
X-Channels: 1
X-Bit-Depth: 16
Transfer-Encoding: chunked

<raw PCM chunks...>
<empty chunk to signal end>
```

### Response

```json
{
  "status": "ok",
  "text": "turn on the light",
  "confidence": 0.87,
  "duration_ms": 1234
}
```

Error response:

```json
{
  "status": "error",
  "code": "invalid_audio",
  "message": "Expected 16000 Hz mono PCM"
}
```

---

## End-of-command signaling

End-of-command is determined by:

1. **Timeout (primary):** ESP32-S3 sends audio for a maximum duration (e.g., 5 seconds) then terminates the stream.
2. **Server-side endpoint detection (optional):** If the ASR backend supports it, the server may detect silence and return a response early.
3. **Silence detection (future):** A simple local VAD (Voice Activity Detector) may be added later if testing shows it is needed.

---

## Server response handling

The ESP32-S3 waits for the server response (JSON) after sending the audio stream.

On success: log the recognized command text, transition back to LISTENING.
On error or timeout: log the error, transition back to LISTENING.

---

## Error codes

| Code | Meaning |
|---|---|
| `invalid_audio` | Audio format does not match expected parameters |
| `asr_failed` | ASR backend returned no result |
| `timeout` | Server did not respond within configured timeout |
| `connection_failed` | TCP connection could not be established |

---

## Security considerations

- The protocol is plaintext HTTP in the current implementation. For production, HTTPS/TLS should be used.
- Wi-Fi credentials must not be committed to the repository. Use `menuconfig` secrets or a provisioning mechanism.
- No authentication is implemented in the current prototype. For production, token-based auth should be added.

---

## Configuration

All protocol parameters are configurable:

| Parameter | Default | Location |
|---|---|---|
| Server host | (set at build time) | `menuconfig` / `audio_config.h` |
| Server port | 8080 | `menuconfig` / `audio_config.h` |
| Stream timeout | 5000 ms | `audio_config.h` |
| Endpoint | `/recognize` | `audio_stream.h` |
| Max command duration | 5 seconds | `audio_config.h` |

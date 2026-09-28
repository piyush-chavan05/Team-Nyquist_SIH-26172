# System Architecture

## Overview

The system solves the problem of running voice activation on a constrained edge device without relying on the cloud for the wake-word decision.

**Core principle:** The wake-word decision is local. Only after the wake word is confirmed does the device transmit audio.

---

## Local vs. remote boundary

```
┌─────────────────────────────────────────────────────────┐
│  LOCAL / EDGE — ESP32-S3                                │
│                                                          │
│  Digital MEMS Microphone                                │
│        │                                                 │
│        ▼                                                 │
│  16 kHz · Mono · 16-bit PCM                             │
│        │                                                 │
│        ▼                                                 │
│  Ring Buffer (sliding window / pre-roll)                 │
│        │                                                 │
│        ▼                                                 │
│  Log-Mel Spectrogram Feature Extraction                  │
│        │                                                 │
│        ▼                                                 │
│  DS-CNN Keyword Spotting Inference                       │
│        │                                                 │
│        ▼                                                 │
│  Threshold + Temporal Confirmation                       │
│  Noise-Adaptive Adjustment                              │
│        │                                                 │
│        ▼                                                 │
│  Wake Word Confirmed                                     │
│        │                                                 │
│        ▼                                                 │
│  Command Capture (pre-roll + new audio)                 │
└──────────────────────┬──────────────────────────────────┘
                       │ Wi-Fi — only after wake
┌──────────────────────▼──────────────────────────────────┐
│  REMOTE — ASR Server                                    │
│                                                          │
│  Receive audio stream                                    │
│        │                                                 │
│        ▼                                                 │
│  Automatic Speech Recognition                            │
│        │                                                 │
│        ▼                                                 │
│  Return recognized command text                         │
└─────────────────────────────────────────────────────────┘
```

---

## Why wake detection is local

| Concern | Cloud wake detection | Local wake detection |
|---|---|---|
| Network required before wake | Yes | No |
| Audio continuously transmitted | Yes | No — only after wake |
| Latency added by network | Yes | Eliminated |
| Privacy | Audio leaves device immediately | Audio stays local until command |
| Offline operation | No | Wake detection works offline |
| Constrained hardware | Cloud offloads computation | Must run on ESP32-S3 |

The ESP32-S3 has sufficient processing for a compact DS-CNN model running on short Log-Mel windows. Cloud-based wake detection would negate the key advantages.

---

## Why ASR is remote

Running a full ASR model on an ESP32-S3 is not currently practical for general vocabulary recognition. The wake-word detection task is deliberately simplified: it is a binary/small-class classification problem, not a full speech recognition problem. Once the wake word is confirmed, the command recognition task (which requires a larger model and vocabulary) is delegated to the server.

---

## Data flow (detailed)

### Step 1: Continuous audio capture

The ESP32-S3 continuously reads audio from the digital MEMS microphone at 16 kHz, mono, 16-bit PCM. Audio is written into a ring buffer.

### Step 2: Sliding window feature extraction

Overlapping frames (25 ms frame, 10 ms hop) are extracted from the ring buffer. Each frame passes through a Hann window, FFT, Mel filterbank, and logarithm to produce a Log-Mel feature vector.

A sequence of feature vectors (covering approximately 1 second of audio) forms the input to the DS-CNN.

### Step 3: DS-CNN inference

The DS-CNN classifies the feature window as one of:
- keyword (wake word)
- unknown speech
- silence / background

The output is a softmax probability over these classes.

### Step 4: Threshold and temporal confirmation

The keyword confidence is compared to a configurable threshold. Multiple consecutive windows above the threshold (temporal confirmation) are required before wake is declared. A cooldown period prevents repeated triggers.

### Step 5: Noise-adaptive adjustment

Background energy is estimated during non-wake periods. The smoothed noise estimate adjusts the threshold within configured bounds. In low-noise environments the threshold may be raised (stricter); in high-noise environments it may be loosened within a safe floor. This is a simple deterministic rule, not a second neural network.

### Step 6: Wake confirmation and command capture

When the wake word is confirmed:
1. The ring buffer provides the pre-roll audio (audio that arrived before the trigger).
2. The state machine transitions to COMMAND_CAPTURE.
3. New audio is captured until end-of-command is detected (timeout or server-side endpoint detection).

### Step 7: Wi-Fi streaming

The captured audio (pre-roll + command) is streamed over Wi-Fi to the remote ASR server. The protocol is HTTP streaming or WebSocket (configurable).

### Step 8: ASR response

The server processes the audio, performs speech recognition, and returns the recognized text. The device transitions back to LISTENING.

---

## Ring buffer

The ring buffer serves two purposes:

1. **Continuous sliding window**: audio is read from the ring buffer in overlapping windows for KWS inference, without blocking the capture task.
2. **Pre-roll**: when wake is confirmed, audio from before the trigger moment is available. This prevents the start of the user's command from being lost during the transition from LISTENING to COMMAND_CAPTURE.

Ring buffer size is configurable. A duration of 1–2 seconds of audio is a reasonable starting point.

---

## State machine

```
LISTENING
    │
    │ N consecutive windows ≥ threshold, cooldown elapsed
    ▼
WAKE_DETECTED
    │
    ▼
COMMAND_CAPTURE
    │
    │ (simultaneously)
    ▼
STREAMING ──► end of command / timeout
    │
    ▼
LISTENING
```

Explicit states are preferred over scattered boolean flags.

---

## Network boundary

The network is only involved after wake confirmation. The communication protocol (HTTP streaming or WebSocket) is configurable. The server expects:

- 16 kHz mono 16-bit PCM audio
- A framing/header protocol to indicate start and end of command

See [`protocol.md`](protocol.md) for the protocol definition.

---

## Module dependency

```
main.c
  └── app_controller  ← orchestrates all modules
        ├── audio_capture    ← microphone → PCM
        ├── ring_buffer      ← pre-roll + sliding window
        ├── feature_extractor← PCM frames → Log-Mel
        ├── kws              ← DS-CNN inference
        ├── wake_detector    ← threshold + confirmation
        ├── state_machine    ← LISTENING → ... → LISTENING
        ├── network/wifi     ← Wi-Fi connection
        ├── network/audio_stream ← command streaming
        └── diagnostics      ← runtime logging
```

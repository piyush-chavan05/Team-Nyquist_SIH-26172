# AGENTS.md — Codex Agent Instructions

This file provides guidance for the Codex AI agent working on this repository.

## Project identity

**Low Latency and Efficient Voice Activator for Edge Devices**
Smart India Hackathon (SIH) entry.

## Core architectural principle

> The ESP32-S3 continuously performs **local** wake-word detection using a compact DS-CNN model.
> Only after the custom wake word is confirmed does the device stream command audio over Wi-Fi
> to a remote ASR (Automatic Speech Recognition) server.

Do not redesign this architecture.

## Authoritative specification

The full engineering specification is:

`Codex_Master_Build_Specification_SIH_Voice_Activator.md`

(located in the parent directory of this repository, or provided to the agent at task time)

Treat it as the ground truth. Do not contradict it.

## Honesty rules (enforced)

1. Never fabricate hardware measurements (RAM, CPU, latency, false activations).
2. Never claim end-to-end hardware validation without actual hardware.
3. Always distinguish: **Implemented** / **Scaffolded** / **Hardware-dependent** / **Planned**.
4. Never write `achieved`, `guaranteed`, `100%`, or real numbers in benchmark columns without real measurements.
5. Use `TBD` or `Pending hardware validation` where required.

## Fixed technical decisions (do not change without owner consent)

| Decision | Value |
|---|---|
| Edge hardware | ESP32-S3 |
| Microphone | Digital MEMS (PDM or I²S — interface TBD) |
| Firmware framework | ESP-IDF |
| Sample rate | 16 kHz mono 16-bit PCM |
| Feature representation | Log-Mel spectrogram |
| KWS model | DS-CNN (Depthwise Separable CNN) |
| Wake decision | Confidence threshold + temporal confirmation |
| Continuous listening | Overlapping sliding windows |
| Pre-roll | Ring buffer |
| Network protocol | HTTP streaming or WebSocket (configurable) |
| ASR server | Open-source/self-hosted (configurable) |

## Wake word

The wake word is **configurable** (placeholder: `hey_activator`).
Owner must supply the actual wake word and training recordings when available.

## Development stages

```
Stage 0 — Repository foundation       ← done when this file exists
Stage 1 — Host audio pipeline
Stage 2 — Dataset tooling + DS-CNN model
Stage 3 — ESP-IDF firmware foundation
Stage 4 — Embedded KWS integration
Stage 5 — Network + ASR server
Stage 6 — Integration
Stage 7 — Benchmark framework
Stage 8 — Final documentation pass
```

## What requires owner input

- GitHub repository URL / credentials
- Exact ESP32-S3 board model
- Exact digital MEMS microphone part
- Custom wake word (finalized)
- Training audio recordings (positive samples)
- Negative/background recordings
- Preferred ASR backend (Vosk / Whisper / other)
- Final hardware wiring / pin assignments

## Secrets policy

Never commit:
- `.env` (only `.env.example`)
- Wi-Fi credentials
- API keys
- SSH private keys
- Private voice recordings

## Status tracking

Update `docs/development-status.md` after every completed stage.
Update `benchmarks/RESULTS.md` only with real measured values.

## Code quality requirements

- Readable, modular, typed where appropriate.
- Configuration centralized (not scattered magic constants).
- Logging over print statements in production paths.
- Tests for all host-side components.

## Do not

- Introduce Raspberry Pi as primary target.
- Replace DS-CNN with a large model.
- Use cloud-first wake detection.
- Add proprietary voice SDKs.
- Invent benchmark results.
- Create fake commits.

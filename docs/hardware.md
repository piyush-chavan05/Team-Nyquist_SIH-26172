# Hardware Documentation

## Edge processor — ESP32-S3

### Why ESP32-S3?

| Feature | Relevance |
|---|---|
| Dual-core Xtensa LX7 @ up to 240 MHz | Sufficient throughput for DSP + inference |
| 512 KB on-chip SRAM | Enough for audio buffers + model runtime |
| Integrated Wi-Fi (2.4 GHz 802.11 b/g/n) | Command audio streaming without external module |
| Digital audio interfaces (I²S, PDM) | Direct connection to digital MEMS microphone |
| ESP-IDF support | Mature, well-documented firmware SDK |
| FreeRTOS | Precise task scheduling for audio + inference |
| Hardware accelerators | Potential DSP acceleration |
| Wide ecosystem | Devkits, documentation, community support |

> **Important:** The ESP32-S3 having 512 KB SRAM does **not** mean the project has satisfied the `<256 KB` RAM target. The target refers to the actual runtime footprint of the complete KWS application. This must be measured on hardware.

### Status

- ESP32-S3 is the confirmed target processor.
- **Exact development board not yet selected.** Common options include ESP32-S3-DevKitC-1, ESP32-S3-WROOM, Adafruit QT Py ESP32-S3, and others.
- Board selection affects available GPIO, flash size, and PCB layout.

---

## Microphone — Digital MEMS

### Why a digital MEMS microphone?

- Digital output (PDM or I²S) eliminates the need for an external ADC and analog amplifier chain.
- Better noise immunity than analog.
- Suitable for close-board mounting.
- Compatible with ESP32-S3 digital audio interfaces.

### Interface options

| Interface | Description | Notes |
|---|---|---|
| PDM (Pulse Density Modulation) | Single-bit oversampled stream | Requires PDM-to-PCM decimation |
| I²S (Inter-IC Sound) | Multi-bit standard digital audio | Direct PCM output from some MEMS mics |

The exact interface depends on the microphone selected. The firmware audio abstraction layer is designed to support either without rewriting the entire application.

### Status

- **Microphone not yet selected.**
- **Interface (PDM/I²S) not yet finalized.**
- Once the microphone is selected, the correct ESP-IDF driver will be implemented and the pin configuration will be documented.

### Common digital MEMS microphone examples (illustrative only)

| Part | Interface | Notes |
|---|---|---|
| INMP441 | I²S | Common, low cost |
| SPH0645LM4H | I²S | Adafruit-popularized |
| MP34DT01-M | PDM | STMicroelectronics |
| ICS-43434 | I²S | TDK InvenSense |

> Do not treat this list as a recommendation. The final selection must be made based on availability, supply chain, power requirements, and ESP32-S3 compatibility.

---

## Audio baseline

| Parameter | Value |
|---|---|
| Sample rate | 16,000 Hz |
| Channels | 1 (mono) |
| Bit depth | 16-bit PCM |
| Raw data rate | 32,000 bytes/second |

---

## Power considerations (high level)

- The ESP32-S3 is not a ultra-low-power device in active mode. The `<10% CPU` target refers to the fraction of CPU time used by KWS while the processor is running.
- If deep-sleep between wake windows is required, additional design work will be needed.
- For the initial prototype, active-mode continuous listening is the design target.
- Actual current draw has not been measured.

---

## Wiring requirements

> **Not yet defined.** Pin assignments depend on the selected ESP32-S3 board and microphone.

The following will need to be documented once hardware is selected:

- I²S or PDM clock pin (SCK / CLK)
- I²S word-select pin (WS / LRCLK) — if I²S
- I²S data pin (SD / DATA)
- PDM data pin — if PDM
- Power supply (typically 3.3 V or 1.8 V — check microphone datasheet)
- Ground

---

## What must be physically tested

1. Microphone connection and I²S/PDM initialization
2. 16 kHz mono PCM capture quality
3. Audio ring-buffer write/read without data loss
4. Embedded feature extraction output vs. Python reference
5. KWS model inference on ESP32-S3
6. RAM footprint of complete application
7. CPU utilization during continuous KWS loop
8. Inference time per window
9. Wi-Fi connection and audio streaming
10. End-to-end wake-to-ASR latency

None of these tests can be performed without physical hardware.

/**
 * audio_config.h — Centralized audio and system configuration.
 *
 * IMPORTANT: Keep these values in sync with ml/preprocessing/mel_features.py
 * to avoid training/inference mismatch.
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* ── Audio capture ─────────────────────────────────── */
#define AUDIO_SAMPLE_RATE_HZ        16000
#define AUDIO_CHANNELS              1        /* mono */
#define AUDIO_BITS_PER_SAMPLE       16       /* PCM 16-bit */
#define AUDIO_BYTES_PER_SAMPLE      (AUDIO_BITS_PER_SAMPLE / 8)
#define AUDIO_BYTES_PER_SEC         (AUDIO_SAMPLE_RATE_HZ * AUDIO_BYTES_PER_SAMPLE)

/* ── Framing ────────────────────────────────────────── */
#define FRAME_SIZE_SAMPLES          400      /* 25 ms at 16 kHz */
#define HOP_SIZE_SAMPLES            160      /* 10 ms at 16 kHz */
#define FRAME_SIZE_BYTES            (FRAME_SIZE_SAMPLES * AUDIO_BYTES_PER_SAMPLE)

/* ── Feature extraction ─────────────────────────────── */
#define FFT_SIZE                    512
#define N_MEL_BINS                  40
#define FMIN_HZ                     20.0f
#define FMAX_HZ                     8000.0f
#define LOG_OFFSET                  1e-6f

/* Feature window: ~1 second = 98 frames */
#define FEATURE_TIME_STEPS          98
#define FEATURE_VECTOR_SIZE         (FEATURE_TIME_STEPS * N_MEL_BINS)

/* ── Ring buffer ─────────────────────────────────────── */
/* 2 seconds of audio */
#define RING_BUFFER_DURATION_SEC    2
#define RING_BUFFER_SAMPLES         (AUDIO_SAMPLE_RATE_HZ * RING_BUFFER_DURATION_SEC)
#define RING_BUFFER_BYTES           (RING_BUFFER_SAMPLES * AUDIO_BYTES_PER_SAMPLE)

/* Pre-roll: 0.5 seconds of audio before wake trigger */
#define PREROLL_DURATION_SEC        0.5f
#define PREROLL_SAMPLES             (uint32_t)(AUDIO_SAMPLE_RATE_HZ * PREROLL_DURATION_SEC)

/* ── Wake detection ──────────────────────────────────── */
/* Base threshold — development value, must be tuned on hardware */
#define WAKE_BASE_THRESHOLD         0.80f
#define WAKE_N_CONFIRM              3        /* consecutive windows needed */
#define WAKE_MAX_GAP                1        /* allowed gap windows */
#define WAKE_COOLDOWN_WINDOWS       20       /* windows after trigger */

/* Noise adaptation */
#define NOISE_ALPHA                 0.05f
#define NOISE_OFFSET_LOW            0.05f
#define NOISE_OFFSET_MODERATE       0.00f
#define NOISE_OFFSET_HIGH          -0.05f
#define NOISE_LOW_THRESHOLD         0.01f
#define NOISE_HIGH_THRESHOLD        0.05f
#define WAKE_MIN_THRESHOLD          0.65f
#define WAKE_MAX_THRESHOLD          0.95f

/* ── Command capture ─────────────────────────────────── */
#define COMMAND_MAX_DURATION_SEC    5
#define COMMAND_MAX_SAMPLES         (AUDIO_SAMPLE_RATE_HZ * COMMAND_MAX_DURATION_SEC)
#define COMMAND_MAX_BYTES           (COMMAND_MAX_SAMPLES * AUDIO_BYTES_PER_SAMPLE)

/* ── Network / ASR ───────────────────────────────────── */
/* Configure Wi-Fi credentials via menuconfig (idf.py menuconfig) */
/* Server address configured at build time */
#define ASR_SERVER_PORT             8080
#define ASR_ENDPOINT                "/recognize"
#define ASR_STREAM_TIMEOUT_MS       10000

/* ── Task priorities ─────────────────────────────────── */
#define TASK_PRIORITY_AUDIO_CAPTURE  (configMAX_PRIORITIES - 1)
#define TASK_PRIORITY_KWS            (configMAX_PRIORITIES - 2)
#define TASK_PRIORITY_NETWORK        (configMAX_PRIORITIES - 3)

/* ── Task stack sizes (bytes) ────────────────────────── */
#define TASK_STACK_AUDIO_CAPTURE    4096
#define TASK_STACK_KWS              8192
#define TASK_STACK_NETWORK          8192

#ifdef __cplusplus
}
#endif

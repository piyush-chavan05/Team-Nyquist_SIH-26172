/**
 * app_controller.c — Top-level application orchestrator.
 *
 * Coordinates: audio capture → ring buffer → features → KWS →
 *              wake detection → state machine → command capture →
 *              streaming → ASR response.
 *
 * STATUS: SCAFFOLDED
 * Physical validation requires hardware integration.
 */

#include "app_controller.h"
#include "audio_config.h"
#include "audio_capture.h"
#include "ring_buffer.h"
#include "feature_extractor.h"
#include "kws.h"
#include "wake_detector.h"
#include "state_machine.h"
#include "wifi.h"
#include "audio_stream.h"
#include "diagnostics.h"

#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>

static const char *TAG = "app_controller";

/* ── Shared state ────────────────────────────────── */
static ring_buffer_t s_ring_buffer;

/* Feature accumulation buffer: [FEATURE_TIME_STEPS][N_MEL_BINS] */
static float s_feature_window[FEATURE_TIME_STEPS][N_MEL_BINS];
static uint32_t s_frame_idx = 0;

static wake_detector_t s_wake_detector;

/* Command audio buffer */
static int16_t *s_command_buf = NULL;
static uint32_t s_command_samples = 0;

/* ─────────────────────────────────────────────────── */

static float compute_frame_energy(const int16_t *samples, uint32_t n)
{
    float energy = 0.0f;
    for (uint32_t i = 0; i < n; i++) {
        float s = samples[i] / 32768.0f;
        energy += s * s;
    }
    return sqrtf(energy / n);
}

esp_err_t app_controller_init(void)
{
    ESP_LOGI(TAG, "Initializing voice activator");

    /* Ring buffer */
    esp_err_t ret = ring_buffer_init(&s_ring_buffer, RING_BUFFER_SAMPLES);
    if (ret != ESP_OK) return ret;

    /* Audio capture */
    ret = audio_capture_init();
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Audio capture init failed (hardware-dependent): %s",
                 esp_err_to_name(ret));
        /* Continue — firmware can be reviewed without hardware */
    }

    /* Feature extractor */
    ret = feature_extractor_init();
    if (ret != ESP_OK) return ret;

    /* KWS */
    ret = kws_init();
    if (ret != ESP_OK) return ret;

    /* Wake detector */
    wake_detector_config_t wd_cfg = wake_detector_default_config();
    wake_detector_init(&s_wake_detector, &wd_cfg);

    /* State machine */
    state_machine_init();

    /* Wi-Fi */
    ret = wifi_init_sta();
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Wi-Fi connection failed (hardware-dependent)");
    }

    /* Diagnostics */
    diagnostics_init();
    diagnostics_log_audio_init(AUDIO_SAMPLE_RATE_HZ, AUDIO_CHANNELS);

    /* Command buffer */
    s_command_buf = malloc(COMMAND_MAX_BYTES);
    if (s_command_buf == NULL) {
        ESP_LOGE(TAG, "Failed to allocate command buffer");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "App controller initialized");
    return ESP_OK;
}

void app_controller_run(void)
{
    static int16_t capture_buf[HOP_SIZE_SAMPLES];

    ESP_LOGI(TAG, "Starting main loop — state: LISTENING");

    while (1) {
        system_state_t state = state_machine_get();

        if (state == STATE_LISTENING || state == STATE_WAKE_DETECTED) {
            /* Read one hop of audio */
            int n_read = audio_capture_read(capture_buf, HOP_SIZE_SAMPLES, 100);
            if (n_read <= 0) {
                vTaskDelay(pdMS_TO_TICKS(1));
                continue;
            }

            /* Write to ring buffer */
            ring_buffer_write(&s_ring_buffer, capture_buf, n_read);

            /* Extract features for this frame */
            float frame_log_mel[N_MEL_BINS];
            feature_extractor_compute(capture_buf, frame_log_mel);

            /* Accumulate into feature window */
            memcpy(s_feature_window[s_frame_idx], frame_log_mel, sizeof(float) * N_MEL_BINS);
            s_frame_idx = (s_frame_idx + 1) % FEATURE_TIME_STEPS;

            /* Run KWS inference every FEATURE_TIME_STEPS frames */
            if (s_frame_idx == 0) {
                kws_result_t kws_result;
                kws_infer((const float *)s_feature_window, &kws_result);

                float energy = compute_frame_energy(capture_buf, n_read);
                diagnostics_log_kws_result(
                    kws_result.keyword_confidence,
                    s_wake_detector.current_threshold,
                    s_wake_detector.noise_estimate
                );

                bool wake = wake_detector_process(
                    &s_wake_detector,
                    kws_result.keyword_confidence,
                    energy
                );

                if (wake) {
                    diagnostics_log_wake_confirmed();
                    state_machine_transition(STATE_COMMAND_CAPTURE);
                }
            }

        } else if (state == STATE_COMMAND_CAPTURE) {
            diagnostics_log_command_start();
            s_command_samples = 0;

            /* Copy pre-roll from ring buffer */
            uint32_t preroll = ring_buffer_read_latest(
                &s_ring_buffer, s_command_buf, PREROLL_SAMPLES
            );
            s_command_samples = preroll;

            /* Capture command audio up to max duration */
            uint32_t remaining = COMMAND_MAX_SAMPLES - s_command_samples;
            int n_read = audio_capture_read(
                s_command_buf + s_command_samples, remaining, COMMAND_MAX_DURATION_SEC * 1000
            );
            if (n_read > 0) s_command_samples += n_read;

            diagnostics_log_command_end(s_command_samples * AUDIO_BYTES_PER_SAMPLE);
            state_machine_transition(STATE_STREAMING);

        } else if (state == STATE_STREAMING) {
            if (wifi_is_connected() && s_command_samples > 0) {
                char server_url[128];
                /* Server URL configured at build time via menuconfig */
                snprintf(server_url, sizeof(server_url),
                         "http://" CONFIG_ASR_SERVER_HOST ":%d" ASR_ENDPOINT,
                         ASR_SERVER_PORT);

                asr_result_t asr;
                audio_stream_send(s_command_buf, s_command_samples, server_url, &asr);

                if (asr.success && asr.recognized_text) {
                    diagnostics_log_asr_response(asr.recognized_text, asr.latency_ms);
                    free(asr.recognized_text);
                } else {
                    ESP_LOGW(TAG, "ASR failed or no result");
                }
            } else {
                ESP_LOGW(TAG, "Streaming skipped: Wi-Fi not connected");
            }

            state_machine_transition(STATE_LISTENING);
            s_command_samples = 0;
        }

        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

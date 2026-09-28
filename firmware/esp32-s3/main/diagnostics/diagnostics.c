/**
 * diagnostics.c — Runtime diagnostics implementation.
 */
#include "diagnostics.h"
#include "esp_log.h"
#include "esp_heap_caps.h"

static const char *TAG = "diagnostics";

void diagnostics_init(void)
{
    ESP_LOGI(TAG, "Diagnostics initialized");
    diagnostics_log_free_heap();
}

void diagnostics_log_audio_init(uint32_t sample_rate, uint8_t channels)
{
    ESP_LOGI(TAG, "Audio initialized: %lu Hz, %d channel(s)",
             (unsigned long)sample_rate, channels);
}

void diagnostics_log_kws_result(float confidence, float threshold, float noise)
{
    ESP_LOGD(TAG, "KWS: confidence=%.3f threshold=%.3f noise=%.4f",
             confidence, threshold, noise);
}

void diagnostics_log_wake_confirmed(void)
{
    ESP_LOGI(TAG, "=== WAKE CONFIRMED ===");
}

void diagnostics_log_command_start(void)
{
    ESP_LOGI(TAG, "Command capture started");
}

void diagnostics_log_command_end(uint32_t bytes_captured)
{
    ESP_LOGI(TAG, "Command ended: %lu bytes captured", (unsigned long)bytes_captured);
}

void diagnostics_log_asr_response(const char *text, uint32_t latency_ms)
{
    ESP_LOGI(TAG, "ASR response: \"%s\" (latency=%lu ms)", text, (unsigned long)latency_ms);
}

void diagnostics_log_free_heap(void)
{
    ESP_LOGI(TAG, "Free heap: %lu bytes (internal: %lu)",
             (unsigned long)esp_get_free_heap_size(),
             (unsigned long)heap_caps_get_free_size(MALLOC_CAP_INTERNAL));
}

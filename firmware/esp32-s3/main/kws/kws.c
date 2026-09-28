/**
 * kws.c — KWS inference implementation.
 *
 * STATUS: SCAFFOLDED / HARDWARE-DEPENDENT
 *
 * This file provides the model inference interface scaffolding.
 * The actual implementation requires:
 *   1. A trained DS-CNN model exported to TFLite format
 *   2. Model runtime: TFLite Micro OR ESP-DL (decision pending)
 *   3. Model file deployed to ESP32-S3 flash/SPIFFS
 *
 * The stub below logs the hardware-pending status and returns
 * placeholder zero output to allow the rest of the firmware to
 * compile and be reviewed.
 *
 * Do NOT claim KWS inference is functional until the model runtime
 * is integrated and validated on physical hardware.
 */

#include "kws.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "kws";

esp_err_t kws_init(void)
{
    ESP_LOGI(TAG, "KWS init");
    ESP_LOGW(TAG, "HARDWARE-DEPENDENT: Model runtime not yet integrated.");
    ESP_LOGW(TAG, "Requires: trained TFLite model + TFLite Micro or ESP-DL runtime.");
    ESP_LOGW(TAG, "See docs/kws-design.md and ml/model/export.py for export path.");
    return ESP_OK;  /* Stub returns OK to allow firmware compilation */
}

esp_err_t kws_infer(const float *features, kws_result_t *result)
{
    (void)features;

    /* Stub: return uniform zero confidence */
    memset(result->scores, 0, sizeof(result->scores));
    result->top_class          = KWS_CLASS_SILENCE;
    result->keyword_confidence = 0.0f;

    ESP_LOGW(TAG, "kws_infer: STUB — no model loaded. Returns zero confidence.");
    return ESP_OK;
}

void kws_deinit(void)
{
    ESP_LOGI(TAG, "KWS deinit");
}

/**
 * kws_model.c — Model loading stub.
 * STATUS: HARDWARE-DEPENDENT — requires TFLite or ESP-DL runtime.
 */
#include "kws_model.h"
#include "esp_log.h"

static const char *TAG = "kws_model";

esp_err_t kws_model_load(const char *model_path)
{
    ESP_LOGI(TAG, "kws_model_load: path=%s", model_path);
    ESP_LOGW(TAG, "STUB: Model loading not implemented. Requires TFLite Micro or ESP-DL.");
    return ESP_OK;
}

void kws_model_unload(void)
{
    ESP_LOGI(TAG, "kws_model_unload");
}

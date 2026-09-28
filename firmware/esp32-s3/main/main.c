/**
 * main.c — Application entry point.
 *
 * Initializes the voice activator and starts the main task.
 */

#include "app_controller.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "main";

void app_main(void)
{
    ESP_LOGI(TAG, "Low Latency Voice Activator — ESP32-S3");
    ESP_LOGI(TAG, "SIH Project: Team Nyquist");

    esp_err_t ret = app_controller_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Initialization failed: %s — halting", esp_err_to_name(ret));
        /* In production: deep sleep or error indication */
        while (1) { vTaskDelay(pdMS_TO_TICKS(1000)); }
    }

    app_controller_run();
    /* app_controller_run() runs indefinitely */
}

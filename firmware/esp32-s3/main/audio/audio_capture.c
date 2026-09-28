/**
 * audio_capture.c — Audio capture implementation.
 *
 * STATUS: SCAFFOLDED / HARDWARE-DEPENDENT
 *
 * This file provides the I2S driver scaffolding. The exact pin numbers,
 * I2S mode (standard/PDM), and clock configuration MUST be set based on
 * the selected ESP32-S3 board and digital MEMS microphone.
 *
 * Do NOT claim this module is physically validated until:
 *   - ESP32-S3 board is selected
 *   - Digital MEMS microphone is selected and wired
 *   - Audio capture is verified to produce correct 16 kHz mono PCM
 *
 * Pending hardware decisions:
 *   - Microphone part number
 *   - Interface: I2S standard or PDM
 *   - Pin assignments (CLK, WS/LRCK, DATA)
 *   - Voltage level (3.3 V or 1.8 V)
 */

#include "audio_capture.h"
#include "audio_config.h"

#include "driver/i2s_std.h"    /* ESP-IDF I2S standard driver */
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "audio_capture";

/* I2S channel handle — set during init */
static i2s_chan_handle_t s_rx_chan = NULL;

/* ─────────────────────────────────────────────────────────────────────
 * NOTE: Pin assignments below are PLACEHOLDERS.
 * Replace with actual values once microphone and board are selected.
 * ───────────────────────────────────────────────────────────────────── */
#define I2S_BCK_PIN     GPIO_NUM_NC   /* Bit clock — TBD */
#define I2S_WS_PIN      GPIO_NUM_NC   /* Word select (LRCLK) — TBD */
#define I2S_DATA_IN_PIN GPIO_NUM_NC   /* Data in from mic — TBD */

esp_err_t audio_capture_init(void)
{
    ESP_LOGI(TAG, "Initializing audio capture");
    ESP_LOGI(TAG, "Sample rate: %d Hz", AUDIO_SAMPLE_RATE_HZ);
    ESP_LOGI(TAG, "Channels: %d", AUDIO_CHANNELS);
    ESP_LOGI(TAG, "Bit depth: %d", AUDIO_BITS_PER_SAMPLE);

    /* ── I2S channel configuration ── */
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(
        I2S_NUM_AUTO, I2S_ROLE_MASTER
    );

    esp_err_t ret = i2s_new_channel(&chan_cfg, NULL, &s_rx_chan);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create I2S channel: %s", esp_err_to_name(ret));
        return ret;
    }

    /* ── Standard I2S mode (suitable for I2S MEMS mics like INMP441) ── */
    /* For PDM microphones, use i2s_pdm_rx_config_t instead.            */
    i2s_std_config_t std_cfg = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(AUDIO_SAMPLE_RATE_HZ),
        .slot_cfg = I2S_STD_MSB_SLOT_DEFAULT_CONFIG(
            I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO
        ),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = I2S_BCK_PIN,
            .ws   = I2S_WS_PIN,
            .dout = I2S_GPIO_UNUSED,
            .din  = I2S_DATA_IN_PIN,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv   = false,
            },
        },
    };

    ret = i2s_channel_init_std_mode(s_rx_chan, &std_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to init I2S std mode: %s", esp_err_to_name(ret));
        i2s_del_channel(s_rx_chan);
        s_rx_chan = NULL;
        return ret;
    }

    ret = i2s_channel_enable(s_rx_chan);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable I2S channel: %s", esp_err_to_name(ret));
        i2s_del_channel(s_rx_chan);
        s_rx_chan = NULL;
        return ret;
    }

    ESP_LOGI(TAG, "Audio capture initialized (PENDING: pin assignment verification)");
    return ESP_OK;
}

int audio_capture_read(int16_t *buf, uint32_t n_samples, uint32_t timeout_ms)
{
    if (s_rx_chan == NULL) {
        ESP_LOGE(TAG, "audio_capture_read: not initialized");
        return -1;
    }

    size_t bytes_to_read = n_samples * AUDIO_BYTES_PER_SAMPLE;
    size_t bytes_read = 0;

    esp_err_t ret = i2s_channel_read(
        s_rx_chan,
        (void *)buf,
        bytes_to_read,
        &bytes_read,
        pdMS_TO_TICKS(timeout_ms == 0 ? portMAX_DELAY : timeout_ms)
    );

    if (ret != ESP_OK && ret != ESP_ERR_TIMEOUT) {
        ESP_LOGE(TAG, "I2S read error: %s", esp_err_to_name(ret));
        return -1;
    }

    return (int)(bytes_read / AUDIO_BYTES_PER_SAMPLE);
}

void audio_capture_deinit(void)
{
    if (s_rx_chan != NULL) {
        i2s_channel_disable(s_rx_chan);
        i2s_del_channel(s_rx_chan);
        s_rx_chan = NULL;
        ESP_LOGI(TAG, "Audio capture deinitialized");
    }
}

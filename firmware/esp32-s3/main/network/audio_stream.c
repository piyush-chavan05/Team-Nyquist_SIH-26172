/**
 * audio_stream.c — HTTP streaming of command audio to ASR server.
 *
 * STATUS: SCAFFOLDED / HARDWARE-DEPENDENT
 * Requires: Wi-Fi connected, ASR server running, physical audio capture.
 */

#include "audio_stream.h"
#include "audio_config.h"
#include "esp_log.h"
#include "esp_http_client.h"
#include <string.h>
#include <stdlib.h>

static const char *TAG = "audio_stream";

esp_err_t audio_stream_send(const int16_t *audio, uint32_t n_samples,
                             const char *server_url, asr_result_t *result)
{
    result->recognized_text = NULL;
    result->latency_ms = 0;
    result->success = false;

    uint64_t t_start = esp_timer_get_time() / 1000;

    esp_http_client_config_t config = {
        .url            = server_url,
        .method         = HTTP_METHOD_POST,
        .timeout_ms     = ASR_STREAM_TIMEOUT_MS,
        .buffer_size    = 4096,
    };

    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (client == NULL) {
        ESP_LOGE(TAG, "Failed to init HTTP client");
        return ESP_FAIL;
    }

    esp_http_client_set_header(client, "Content-Type", "application/octet-stream");
    esp_http_client_set_header(client, "X-Sample-Rate", "16000");
    esp_http_client_set_header(client, "X-Channels",    "1");
    esp_http_client_set_header(client, "X-Bit-Depth",   "16");

    uint32_t payload_size = n_samples * AUDIO_BYTES_PER_SAMPLE;
    esp_http_client_set_post_field(client, (const char *)audio, payload_size);

    esp_err_t err = esp_http_client_perform(client);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "HTTP request failed: %s", esp_err_to_name(err));
        esp_http_client_cleanup(client);
        return err;
    }

    int status = esp_http_client_get_status_code(client);
    ESP_LOGI(TAG, "HTTP status: %d", status);

    if (status == 200) {
        int content_len = esp_http_client_get_content_length(client);
        if (content_len > 0 && content_len < 1024) {
            char *resp_buf = malloc(content_len + 1);
            if (resp_buf) {
                int read = esp_http_client_read(client, resp_buf, content_len);
                resp_buf[read > 0 ? read : 0] = '\0';
                /* Simple JSON text extraction — production code should use cJSON */
                result->recognized_text = resp_buf;
                result->success = true;
            }
        }
    }

    uint64_t t_end = esp_timer_get_time() / 1000;
    result->latency_ms = (uint32_t)(t_end - t_start);

    esp_http_client_cleanup(client);
    return ESP_OK;
}

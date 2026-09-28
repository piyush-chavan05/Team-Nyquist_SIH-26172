/**
 * audio_stream.h — Stream command audio to remote ASR server.
 */
#pragma once
#include <stdint.h>
#include "esp_err.h"
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char *recognized_text;   /* Heap-allocated — caller must free */
    uint32_t latency_ms;
    bool success;
} asr_result_t;

esp_err_t audio_stream_send(const int16_t *audio, uint32_t n_samples,
                             const char *server_url, asr_result_t *result);

#ifdef __cplusplus
}
#endif

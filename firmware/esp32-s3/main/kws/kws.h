/**
 * kws.h — KWS inference interface.
 *
 * Runs the DS-CNN model on a Log-Mel feature window and returns confidence.
 * STATUS: SCAFFOLDED — requires model runtime (TFLite Micro or ESP-DL)
 *         and a trained model file.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "audio_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/* KWS output classes */
typedef enum {
    KWS_CLASS_KEYWORD = 0,
    KWS_CLASS_UNKNOWN = 1,
    KWS_CLASS_SILENCE = 2,
    KWS_N_CLASSES     = 3,
} kws_class_t;

typedef struct {
    float      scores[KWS_N_CLASSES];   /* Softmax probabilities */
    kws_class_t top_class;              /* Argmax class */
    float       keyword_confidence;     /* scores[KWS_CLASS_KEYWORD] */
} kws_result_t;

/**
 * kws_init — Load model and initialize inference runtime.
 * @return ESP_OK on success.
 * NOTE: Requires model runtime and model file in flash/SPIFFS.
 */
esp_err_t kws_init(void);

/**
 * kws_infer — Run inference on a Log-Mel feature window.
 *
 * @param features  Input array of FEATURE_VECTOR_SIZE floats.
 * @param result    Output result struct.
 * @return ESP_OK on success.
 */
esp_err_t kws_infer(const float *features, kws_result_t *result);

/**
 * kws_deinit — Release KWS resources.
 */
void kws_deinit(void);

#ifdef __cplusplus
}
#endif

/**
 * feature_extractor.h — Log-Mel spectrogram feature extraction interface.
 *
 * STATUS: SCAFFOLDED — C implementation of feature pipeline.
 * Must be validated against Python reference output on hardware.
 */

#pragma once

#include <stdint.h>
#include "audio_config.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * feature_extractor_init — Initialize feature extraction (Mel filterbank).
 * @return ESP_OK on success.
 */
esp_err_t feature_extractor_init(void);

/**
 * feature_extractor_compute — Compute Log-Mel features from a frame.
 *
 * @param frame     Input frame (FRAME_SIZE_SAMPLES int16 samples).
 * @param log_mel   Output array (N_MEL_BINS float values).
 *
 * IMPORTANT: Parameters (FFT_SIZE, N_MEL_BINS, FMIN_HZ, FMAX_HZ)
 * must match ml/preprocessing/mel_features.py exactly.
 */
void feature_extractor_compute(const int16_t *frame, float *log_mel);

/**
 * feature_extractor_deinit — Release feature extraction resources.
 */
void feature_extractor_deinit(void);

#ifdef __cplusplus
}
#endif

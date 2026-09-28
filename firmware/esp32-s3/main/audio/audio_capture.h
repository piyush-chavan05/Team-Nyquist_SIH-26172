/**
 * audio_capture.h — Audio capture abstraction layer.
 *
 * Abstracts the microphone interface (I2S or PDM) behind a clean API.
 * The backend implementation is selected at compile time based on
 * the selected microphone and board.
 *
 * STATUS: SCAFFOLDED — requires physical microphone selection and
 *         ESP-IDF driver configuration before physical validation.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "audio_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * audio_capture_init — Initialize the audio capture subsystem.
 *
 * Configures the I2S or PDM peripheral for the selected microphone.
 * Must be called before audio_capture_read().
 *
 * @return ESP_OK on success, error code on failure.
 *
 * NOTE: Pin numbers and interface type (I2S/PDM) must be configured
 *       in audio_capture.c once the physical microphone is selected.
 */
esp_err_t audio_capture_init(void);

/**
 * audio_capture_read — Read a block of PCM samples from the microphone.
 *
 * Blocks until `n_samples` samples are available.
 *
 * @param buf       Output buffer (int16_t, AUDIO_SAMPLE_RATE_HZ compatible).
 * @param n_samples Number of samples to read.
 * @param timeout_ms Timeout in milliseconds (0 = wait indefinitely).
 *
 * @return Number of samples actually read, or -1 on error.
 */
int audio_capture_read(int16_t *buf, uint32_t n_samples, uint32_t timeout_ms);

/**
 * audio_capture_deinit — Release audio capture resources.
 */
void audio_capture_deinit(void);

#ifdef __cplusplus
}
#endif

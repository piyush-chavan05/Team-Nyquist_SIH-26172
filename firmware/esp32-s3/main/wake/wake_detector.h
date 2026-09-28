/**
 * wake_detector.h — Wake word detection logic.
 *
 * Implements: threshold + temporal confirmation + cooldown +
 *             noise-adaptive threshold adjustment.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "audio_config.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float    base_threshold;
    uint32_t n_confirm;
    uint32_t max_gap;
    uint32_t cooldown_windows;
    float    min_threshold;
    float    max_threshold;
    float    noise_alpha;
    float    noise_offset_low;
    float    noise_offset_moderate;
    float    noise_offset_high;
    float    noise_low_threshold;
    float    noise_high_threshold;
} wake_detector_config_t;

typedef struct {
    wake_detector_config_t cfg;
    uint32_t confirm_count;
    uint32_t gap_count;
    uint32_t cooldown_remaining;
    float    noise_estimate;
    float    current_threshold;
} wake_detector_t;

/**
 * wake_detector_default_config — Return default config from audio_config.h.
 */
wake_detector_config_t wake_detector_default_config(void);

/**
 * wake_detector_init — Initialize wake detector with given config.
 */
void wake_detector_init(wake_detector_t *wd, const wake_detector_config_t *cfg);

/**
 * wake_detector_process — Process one window confidence score.
 *
 * @param wd           Wake detector state.
 * @param confidence   KWS keyword confidence in [0, 1].
 * @param frame_energy RMS energy of the frame (for noise adaptation).
 *
 * @return true if wake word is confirmed.
 */
bool wake_detector_process(wake_detector_t *wd, float confidence, float frame_energy);

/**
 * wake_detector_reset — Reset confirm/gap/cooldown state.
 */
void wake_detector_reset(wake_detector_t *wd);

#ifdef __cplusplus
}
#endif

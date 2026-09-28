/**
 * wake_detector.c — Wake word detection implementation.
 */

#include "wake_detector.h"
#include "esp_log.h"
#include <math.h>

static const char *TAG = "wake_detector";

wake_detector_config_t wake_detector_default_config(void)
{
    wake_detector_config_t cfg = {
        .base_threshold       = WAKE_BASE_THRESHOLD,
        .n_confirm            = WAKE_N_CONFIRM,
        .max_gap              = WAKE_MAX_GAP,
        .cooldown_windows     = WAKE_COOLDOWN_WINDOWS,
        .min_threshold        = WAKE_MIN_THRESHOLD,
        .max_threshold        = WAKE_MAX_THRESHOLD,
        .noise_alpha          = NOISE_ALPHA,
        .noise_offset_low     = NOISE_OFFSET_LOW,
        .noise_offset_moderate= NOISE_OFFSET_MODERATE,
        .noise_offset_high    = NOISE_OFFSET_HIGH,
        .noise_low_threshold  = NOISE_LOW_THRESHOLD,
        .noise_high_threshold = NOISE_HIGH_THRESHOLD,
    };
    return cfg;
}

void wake_detector_init(wake_detector_t *wd, const wake_detector_config_t *cfg)
{
    wd->cfg               = *cfg;
    wd->confirm_count     = 0;
    wd->gap_count         = 0;
    wd->cooldown_remaining= 0;
    wd->noise_estimate    = 0.0f;
    wd->current_threshold = cfg->base_threshold;

    ESP_LOGI(TAG, "Wake detector initialized");
    ESP_LOGI(TAG, "  Base threshold:    %.2f", cfg->base_threshold);
    ESP_LOGI(TAG, "  Confirm windows:   %lu", (unsigned long)cfg->n_confirm);
    ESP_LOGI(TAG, "  Cooldown windows:  %lu", (unsigned long)cfg->cooldown_windows);
    ESP_LOGI(TAG, "  Threshold bounds:  [%.2f, %.2f]", cfg->min_threshold, cfg->max_threshold);
    ESP_LOGW(TAG, "  NOTE: Base threshold is a development default. Must be tuned on hardware.");
}

static void update_noise(wake_detector_t *wd, float frame_energy)
{
    wd->noise_estimate = wd->cfg.noise_alpha * frame_energy
                       + (1.0f - wd->cfg.noise_alpha) * wd->noise_estimate;

    float offset;
    if (wd->noise_estimate < wd->cfg.noise_low_threshold) {
        offset = wd->cfg.noise_offset_low;
    } else if (wd->noise_estimate > wd->cfg.noise_high_threshold) {
        offset = wd->cfg.noise_offset_high;
    } else {
        offset = wd->cfg.noise_offset_moderate;
    }

    float thr = wd->cfg.base_threshold + offset;
    if (thr < wd->cfg.min_threshold) thr = wd->cfg.min_threshold;
    if (thr > wd->cfg.max_threshold)  thr = wd->cfg.max_threshold;
    wd->current_threshold = thr;
}

bool wake_detector_process(wake_detector_t *wd, float confidence, float frame_energy)
{
    /* Cooldown period */
    if (wd->cooldown_remaining > 0) {
        wd->cooldown_remaining--;
        return false;
    }

    /* Update noise during non-confirming windows */
    if (wd->confirm_count == 0) {
        update_noise(wd, frame_energy);
    }

    if (confidence >= wd->current_threshold) {
        wd->confirm_count++;
        wd->gap_count = 0;
        ESP_LOGD(TAG, "Confirm: %lu/%lu  conf=%.3f  thr=%.3f",
                 (unsigned long)wd->confirm_count,
                 (unsigned long)wd->cfg.n_confirm,
                 confidence, wd->current_threshold);
    } else {
        if (wd->confirm_count > 0) {
            wd->gap_count++;
            if (wd->gap_count > wd->cfg.max_gap) {
                ESP_LOGD(TAG, "Gap exceeded — resetting confirm counter");
                wd->confirm_count = 0;
                wd->gap_count     = 0;
            }
        }
    }

    if (wd->confirm_count >= wd->cfg.n_confirm) {
        ESP_LOGI(TAG, "Wake confirmed! confidence=%.3f threshold=%.3f noise=%.4f",
                 confidence, wd->current_threshold, wd->noise_estimate);
        wd->confirm_count      = 0;
        wd->gap_count          = 0;
        wd->cooldown_remaining = wd->cfg.cooldown_windows;
        return true;
    }

    return false;
}

void wake_detector_reset(wake_detector_t *wd)
{
    wd->confirm_count      = 0;
    wd->gap_count          = 0;
    wd->cooldown_remaining = 0;
}

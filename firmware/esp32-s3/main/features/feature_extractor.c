/**
 * feature_extractor.c — Log-Mel spectrogram computation for ESP32-S3.
 *
 * STATUS: SCAFFOLDED
 *
 * This implementation uses esp-dsp for FFT computation when available.
 * The Mel filterbank is pre-computed at initialization.
 *
 * Validation required: output must match ml/preprocessing/mel_features.py
 * on identical input before using for KWS inference.
 *
 * Hardware-dependent: performance (execution time) must be measured
 * on ESP32-S3 to confirm it fits within one hop period (10 ms).
 */

#include "feature_extractor.h"
#include "audio_config.h"
#include <string.h>
#include <math.h>
#include "esp_log.h"
#include "esp_dsp.h"   /* ESP-DSP: FFT support — requires esp-dsp component */

static const char *TAG = "feature_extractor";

/* Pre-computed Mel filterbank: [N_MEL_BINS][FFT_SIZE/2+1] */
static float s_mel_filterbank[N_MEL_BINS][FFT_SIZE / 2 + 1];
static float s_hann_window[FRAME_SIZE_SAMPLES];
static bool  s_initialized = false;

/* Hann window: w[n] = 0.5 * (1 - cos(2*pi*n/(N-1))) */
static void build_hann_window(void)
{
    for (int n = 0; n < FRAME_SIZE_SAMPLES; n++) {
        s_hann_window[n] = 0.5f * (1.0f - cosf(2.0f * M_PI * n / (FRAME_SIZE_SAMPLES - 1)));
    }
}

/* Hz → Mel */
static float hz_to_mel(float f) { return 2595.0f * log10f(1.0f + f / 700.0f); }
/* Mel → Hz */
static float mel_to_hz(float m) { return 700.0f * (powf(10.0f, m / 2595.0f) - 1.0f); }

static void build_mel_filterbank(void)
{
    int n_freqs = FFT_SIZE / 2 + 1;
    float mel_min = hz_to_mel(FMIN_HZ);
    float mel_max = hz_to_mel(FMAX_HZ);

    float mel_points[N_MEL_BINS + 2];
    float hz_points[N_MEL_BINS + 2];

    for (int i = 0; i < N_MEL_BINS + 2; i++) {
        mel_points[i] = mel_min + (mel_max - mel_min) * i / (N_MEL_BINS + 1);
        hz_points[i]  = mel_to_hz(mel_points[i]);
    }

    memset(s_mel_filterbank, 0, sizeof(s_mel_filterbank));

    for (int m = 0; m < N_MEL_BINS; m++) {
        float f_left   = hz_points[m];
        float f_center = hz_points[m + 1];
        float f_right  = hz_points[m + 2];

        for (int k = 0; k < n_freqs; k++) {
            float f = (float)k * AUDIO_SAMPLE_RATE_HZ / FFT_SIZE;
            if (f >= f_left && f <= f_center) {
                s_mel_filterbank[m][k] = (f - f_left) / (f_center - f_left + 1e-12f);
            } else if (f > f_center && f <= f_right) {
                s_mel_filterbank[m][k] = (f_right - f) / (f_right - f_center + 1e-12f);
            }
        }
    }
}

esp_err_t feature_extractor_init(void)
{
    if (s_initialized) return ESP_OK;

    build_hann_window();
    build_mel_filterbank();

    /* Initialize ESP-DSP FFT */
    esp_err_t ret = dsps_fft2r_init_fc32(NULL, FFT_SIZE);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ESP-DSP FFT init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    s_initialized = true;
    ESP_LOGI(TAG, "Feature extractor initialized (FFT=%d, Mel=%d)", FFT_SIZE, N_MEL_BINS);
    ESP_LOGW(TAG, "PENDING: Validate output against Python reference on hardware");
    return ESP_OK;
}

void feature_extractor_compute(const int16_t *frame, float *log_mel)
{
    /* Temporary FFT buffer (real, imag interleaved for ESP-DSP) */
    static float fft_buf[FFT_SIZE * 2];

    /* Convert int16 → float, apply Hann window, zero-pad to FFT_SIZE */
    for (int i = 0; i < FRAME_SIZE_SAMPLES; i++) {
        fft_buf[2 * i]     = (frame[i] / 32768.0f) * s_hann_window[i];
        fft_buf[2 * i + 1] = 0.0f;
    }
    for (int i = FRAME_SIZE_SAMPLES; i < FFT_SIZE; i++) {
        fft_buf[2 * i]     = 0.0f;
        fft_buf[2 * i + 1] = 0.0f;
    }

    /* FFT */
    dsps_fft2r_fc32(fft_buf, FFT_SIZE);
    dsps_bit_rev_fc32(fft_buf, FFT_SIZE);

    /* Power spectrum */
    int n_freqs = FFT_SIZE / 2 + 1;
    static float power[FFT_SIZE / 2 + 1];
    for (int k = 0; k < n_freqs; k++) {
        float re = fft_buf[2 * k];
        float im = fft_buf[2 * k + 1];
        power[k] = re * re + im * im;
    }

    /* Mel filterbank + log */
    for (int m = 0; m < N_MEL_BINS; m++) {
        float energy = LOG_OFFSET;
        for (int k = 0; k < n_freqs; k++) {
            energy += s_mel_filterbank[m][k] * power[k];
        }
        log_mel[m] = log10f(energy);
    }
}

void feature_extractor_deinit(void)
{
    s_initialized = false;
}

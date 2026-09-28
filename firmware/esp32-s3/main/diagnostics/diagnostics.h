/**
 * diagnostics.h — Runtime diagnostics and performance logging.
 */
#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

void diagnostics_init(void);
void diagnostics_log_audio_init(uint32_t sample_rate, uint8_t channels);
void diagnostics_log_kws_result(float confidence, float threshold, float noise);
void diagnostics_log_wake_confirmed(void);
void diagnostics_log_command_start(void);
void diagnostics_log_command_end(uint32_t bytes_captured);
void diagnostics_log_asr_response(const char *text, uint32_t latency_ms);
void diagnostics_log_free_heap(void);

#ifdef __cplusplus
}
#endif

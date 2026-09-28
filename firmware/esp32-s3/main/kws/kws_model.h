/**
 * kws_model.h — Model loading and buffer management.
 */
#pragma once
#include "esp_err.h"
#ifdef __cplusplus
extern "C" {
#endif
esp_err_t kws_model_load(const char *model_path);
void kws_model_unload(void);
#ifdef __cplusplus
}
#endif

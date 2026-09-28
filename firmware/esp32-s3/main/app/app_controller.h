/**
 * app_controller.h — Top-level application orchestrator.
 */
#pragma once
#include "esp_err.h"
#ifdef __cplusplus
extern "C" {
#endif
esp_err_t app_controller_init(void);
void      app_controller_run(void);
#ifdef __cplusplus
}
#endif

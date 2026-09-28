/**
 * wifi.h — Wi-Fi connection management.
 * STATUS: SCAFFOLDED — requires credentials via menuconfig.
 */
#pragma once
#include "esp_err.h"
#ifdef __cplusplus
extern "C" {
#endif
esp_err_t wifi_init_sta(void);
bool wifi_is_connected(void);
void wifi_deinit(void);
#ifdef __cplusplus
}
#endif

/**
 * state_machine.c — System state machine implementation.
 */

#include "state_machine.h"
#include "esp_log.h"

static const char *TAG = "state_machine";
static system_state_t s_current_state = STATE_LISTENING;

void state_machine_init(void)
{
    s_current_state = STATE_LISTENING;
    ESP_LOGI(TAG, "State machine initialized: %s", state_machine_name(s_current_state));
}

system_state_t state_machine_get(void)
{
    return s_current_state;
}

void state_machine_transition(system_state_t new_state)
{
    if (new_state == s_current_state) return;

    ESP_LOGI(TAG, "State: %s -> %s",
             state_machine_name(s_current_state),
             state_machine_name(new_state));
    s_current_state = new_state;
}

const char *state_machine_name(system_state_t state)
{
    switch (state) {
        case STATE_LISTENING:       return "LISTENING";
        case STATE_WAKE_DETECTED:   return "WAKE_DETECTED";
        case STATE_COMMAND_CAPTURE: return "COMMAND_CAPTURE";
        case STATE_STREAMING:       return "STREAMING";
        default:                    return "UNKNOWN";
    }
}

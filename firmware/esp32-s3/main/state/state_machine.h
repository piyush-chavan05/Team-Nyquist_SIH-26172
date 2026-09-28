/**
 * state_machine.h — System state machine.
 *
 * States: LISTENING → WAKE_DETECTED → COMMAND_CAPTURE → STREAMING → LISTENING
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    STATE_LISTENING       = 0,
    STATE_WAKE_DETECTED   = 1,
    STATE_COMMAND_CAPTURE = 2,
    STATE_STREAMING       = 3,
} system_state_t;

/**
 * state_machine_init — Initialize state machine to LISTENING.
 */
void state_machine_init(void);

/**
 * state_machine_get — Return current state.
 */
system_state_t state_machine_get(void);

/**
 * state_machine_transition — Transition to a new state.
 * Logs the transition. Ignores invalid transitions.
 */
void state_machine_transition(system_state_t new_state);

/**
 * state_machine_name — Return human-readable state name.
 */
const char *state_machine_name(system_state_t state);

#ifdef __cplusplus
}
#endif

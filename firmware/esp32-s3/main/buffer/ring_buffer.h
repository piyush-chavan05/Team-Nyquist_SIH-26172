/**
 * ring_buffer.h — Fixed-size ring buffer for audio samples.
 *
 * Thread-safe for single-producer / single-consumer usage via critical sections.
 * Designed for continuous audio capture with pre-roll support.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int16_t  *buf;          /* Sample buffer (heap-allocated) */
    uint32_t  capacity;     /* Total samples capacity */
    uint32_t  write_pos;    /* Next write position */
    uint32_t  count;        /* Number of valid samples */
} ring_buffer_t;

/**
 * ring_buffer_init — Allocate and initialize a ring buffer.
 * @param rb       Ring buffer handle.
 * @param capacity Capacity in samples.
 * @return ESP_OK on success.
 */
esp_err_t ring_buffer_init(ring_buffer_t *rb, uint32_t capacity);

/**
 * ring_buffer_write — Write samples into the ring buffer.
 * Overwrites oldest samples when full.
 * @param rb       Ring buffer handle.
 * @param samples  Input sample array.
 * @param n        Number of samples to write.
 */
void ring_buffer_write(ring_buffer_t *rb, const int16_t *samples, uint32_t n);

/**
 * ring_buffer_read_latest — Read the N most recent samples.
 * Returns samples in chronological order.
 * @param rb  Ring buffer handle.
 * @param out Output array (must be at least n_samples long).
 * @param n   Number of samples to read (clamped to rb->count).
 * @return    Actual number of samples copied.
 */
uint32_t ring_buffer_read_latest(const ring_buffer_t *rb, int16_t *out, uint32_t n);

/**
 * ring_buffer_clear — Reset the ring buffer to empty state.
 */
void ring_buffer_clear(ring_buffer_t *rb);

/**
 * ring_buffer_free — Free the ring buffer memory.
 */
void ring_buffer_free(ring_buffer_t *rb);

#ifdef __cplusplus
}
#endif

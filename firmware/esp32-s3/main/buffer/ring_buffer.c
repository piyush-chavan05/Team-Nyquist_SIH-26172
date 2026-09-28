/**
 * ring_buffer.c — Fixed-size ring buffer implementation.
 *
 * Single-producer / single-consumer design.
 * write and read_latest are not simultaneously thread-safe without
 * external locking; the app_controller acquires a mutex before calling.
 */

#include "ring_buffer.h"
#include <string.h>
#include "esp_heap_caps.h"
#include "esp_log.h"

static const char *TAG = "ring_buffer";

esp_err_t ring_buffer_init(ring_buffer_t *rb, uint32_t capacity)
{
    if (rb == NULL || capacity == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    rb->buf = (int16_t *)heap_caps_malloc(
        capacity * sizeof(int16_t), MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT
    );
    if (rb->buf == NULL) {
        ESP_LOGE(TAG, "Failed to allocate ring buffer (%lu samples)", (unsigned long)capacity);
        return ESP_ERR_NO_MEM;
    }

    rb->capacity  = capacity;
    rb->write_pos = 0;
    rb->count     = 0;

    ESP_LOGI(TAG, "Ring buffer: %lu samples (%lu bytes)",
             (unsigned long)capacity,
             (unsigned long)(capacity * sizeof(int16_t)));
    return ESP_OK;
}

void ring_buffer_write(ring_buffer_t *rb, const int16_t *samples, uint32_t n)
{
    if (rb == NULL || samples == NULL || n == 0) return;

    for (uint32_t i = 0; i < n; i++) {
        rb->buf[rb->write_pos] = samples[i];
        rb->write_pos = (rb->write_pos + 1) % rb->capacity;
    }
    if (rb->count + n <= rb->capacity) {
        rb->count += n;
    } else {
        rb->count = rb->capacity;
    }
}

uint32_t ring_buffer_read_latest(const ring_buffer_t *rb, int16_t *out, uint32_t n)
{
    if (rb == NULL || out == NULL) return 0;

    uint32_t available = rb->count < n ? rb->count : n;
    if (available == 0) return 0;

    /* Start position: write_pos - available (mod capacity) */
    uint32_t start = (rb->write_pos + rb->capacity - available) % rb->capacity;
    uint32_t end   = rb->write_pos;

    if (start < end) {
        memcpy(out, rb->buf + start, available * sizeof(int16_t));
    } else {
        /* Wraparound: copy tail then head */
        uint32_t tail_len = rb->capacity - start;
        memcpy(out, rb->buf + start, tail_len * sizeof(int16_t));
        memcpy(out + tail_len, rb->buf, end * sizeof(int16_t));
    }

    return available;
}

void ring_buffer_clear(ring_buffer_t *rb)
{
    if (rb == NULL) return;
    rb->write_pos = 0;
    rb->count     = 0;
}

void ring_buffer_free(ring_buffer_t *rb)
{
    if (rb == NULL) return;
    if (rb->buf != NULL) {
        heap_caps_free(rb->buf);
        rb->buf = NULL;
    }
    rb->capacity  = 0;
    rb->write_pos = 0;
    rb->count     = 0;
}

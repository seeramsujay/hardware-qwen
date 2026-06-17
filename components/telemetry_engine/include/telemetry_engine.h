#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

// Packed binary structure for low-overhead edge telemetry (exactly 20 bytes)
typedef struct __attribute__((packed)) {
    uint64_t timestamp;      // Microseconds since boot
    float temperature;       // Temperature in °C
    float humidity;          // Humidity in %
    uint8_t relay_state;     // Compressor status (0 = OFF, 1 = ON)
    uint8_t flags;           // Bitmask flags: bit 0: is_simulated, bit 1: thermal_breach_alert
    uint8_t reserved;        // Padding/reserved byte
    uint8_t checksum;        // Additive checksum of the first 19 bytes
} cryo_telemetry_packet_t;

// Standard application representation
typedef struct {
    float temperature;
    float humidity;
    bool is_simulated;
    bool thermal_breach_alert;
    uint8_t relay_state;
    uint64_t timestamp;
} telemetry_data_t;

/**
 * @brief Initialize the telemetry engine mutex and state store.
 * @return ESP_OK on success.
 */
esp_err_t telemetry_engine_init(void);

/**
 * @brief Set the latest telemetry sensor readings (thread-safe).
 * @param[in] temp Latest temperature.
 * @param[in] hum Latest humidity.
 * @param[in] is_simulated True if reading is from simulated sensor.
 * @return ESP_OK on success.
 */
esp_err_t telemetry_engine_update_sensor(float temp, float hum, bool is_simulated);

/**
 * @brief Set the latest compressor relay status (thread-safe).
 * @param[in] state 1 for ON, 0 for OFF.
 * @return ESP_OK on success.
 */
esp_err_t telemetry_engine_update_relay(uint8_t state);

/**
 * @brief Set thermal breach alert status (thread-safe).
 * @param[in] alert True if thermal breach occurred.
 * @return ESP_OK on success.
 */
esp_err_t telemetry_engine_set_alert(bool alert);

/**
 * @brief Fetch the current state store (thread-safe).
 * @param[out] out_data Target structure to copy the state to.
 * @return ESP_OK on success.
 */
esp_err_t telemetry_engine_get_data(telemetry_data_t *out_data);

/**
 * @brief Safely locks the FreeRTOS Mutex, copies a clean binary snapshot of local data to out_buffer.
 * @param[out] out_buffer Target buffer to copy the serialized packet to.
 * @param[in] buffer_len Length of the target buffer (must be at least 20 bytes).
 * @return ESP_OK on success, error code otherwise.
 */
esp_err_t get_cryo_telemetry_snapshot(uint8_t *out_buffer, size_t buffer_len);

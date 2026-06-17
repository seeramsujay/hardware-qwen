#pragma once

#include "esp_err.h"
#include "hal/gpio_types.h"
#include "driver/i2c_master.h"

// Default I2C configuration for ESP32-S3
#define BME280_I2C_SDA_PIN    GPIO_NUM_1
#define BME280_I2C_SCL_PIN    GPIO_NUM_2
#define BME280_I2C_PORT       I2C_NUM_0
#define BME280_I2C_ADDR       0x76

// BME280 Register addresses
#define BME280_REG_CALIB_00   0x88
#define BME280_REG_ID         0xD0
#define BME280_REG_RESET      0xE0
#define BME280_REG_CALIB_26   0xE1
#define BME280_REG_CTRL_HUM   0xF2
#define BME280_REG_STATUS     0xF3
#define BME280_REG_CTRL_MEAS  0xF4
#define BME280_REG_CONFIG     0xF5
#define BME280_REG_DATA       0xF7

// Structure to hold calibration coefficients
typedef struct {
    uint16_t dig_T1;
    int16_t  dig_T2;
    int16_t  dig_T3;
    uint8_t  dig_H1;
    int16_t  dig_H2;
    uint8_t  dig_H3;
    int16_t  dig_H4;
    int16_t  dig_H5;
    int8_t   dig_H6;
    int32_t  t_fine; // Calculated fine temperature for humidity compensation
} bme280_calib_data_t;

// Telemetry output structure
typedef struct {
    float temperature;  // °C
    float humidity;     // %
    bool is_simulated;  // True if physical sensor was not found and mock is running
} bme280_data_t;

/**
 * @brief Initialize the BME280 I2C master configuration and probe the sensor.
 *        If the sensor is not physically present, it falls back to a simulated sensor.
 * @return ESP_OK on success (either physical or simulated fallback initialized), error code otherwise.
 */
esp_err_t bme280_init(void);

/**
 * @brief Read temperature and humidity. Falls back to realistic physical model simulation if in mock mode.
 * @param[out] data Pointer to structure where telemetry will be saved.
 * @return ESP_OK on success.
 */
esp_err_t bme280_read_data(bme280_data_t *data);

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "bme280_driver.h"

static const char *TAG = "BME280_DRIVER";

#define BME280_I2C_TIMEOUT_MS   1000
#define COMPRESSOR_RELAY_GPIO   GPIO_NUM_10

static i2c_master_bus_handle_t s_i2c_bus_handle = NULL;
static i2c_master_dev_handle_t s_bme280_dev = NULL;
static bme280_calib_data_t s_calib;
static bool s_is_simulated = false;

// Mock temperature & humidity model variables
static float s_sim_temp = 22.0f;      // Starting temperature in °C
static float s_sim_humidity = 55.0f;  // Starting humidity in %

static esp_err_t bme280_write_reg(uint8_t reg, uint8_t value) {
    if (s_is_simulated || s_bme280_dev == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    uint8_t write_buf[2] = {reg, value};
    return i2c_master_transmit(s_bme280_dev, write_buf, 2, BME280_I2C_TIMEOUT_MS);
}

static esp_err_t bme280_read_regs(uint8_t reg, uint8_t *data, size_t len) {
    if (s_is_simulated || s_bme280_dev == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    return i2c_master_transmit_receive(s_bme280_dev, &reg, 1, data, len, BME280_I2C_TIMEOUT_MS);
}

static esp_err_t read_calibration_data(void) {
    uint8_t calib_00_25[26];
    esp_err_t err = bme280_read_regs(BME280_REG_CALIB_00, calib_00_25, 26);
    if (err != ESP_OK) return err;

    s_calib.dig_T1 = (calib_00_25[1] << 8) | calib_00_25[0];
    s_calib.dig_T2 = (int16_t)((calib_00_25[3] << 8) | calib_00_25[2]);
    s_calib.dig_T3 = (int16_t)((calib_00_25[5] << 8) | calib_00_25[4]);
    s_calib.dig_H1 = calib_00_25[25];

    uint8_t calib_e1_e7[7];
    err = bme280_read_regs(BME280_REG_CALIB_26, calib_e1_e7, 7);
    if (err != ESP_OK) return err;

    s_calib.dig_H2 = (int16_t)((calib_e1_e7[1] << 8) | calib_e1_e7[0]);
    s_calib.dig_H3 = calib_e1_e7[2];
    s_calib.dig_H4 = (int16_t)((calib_e1_e7[3] << 4) | (calib_e1_e7[4] & 0x0F));
    s_calib.dig_H5 = (int16_t)((calib_e1_e7[5] << 4) | ((calib_e1_e7[4] & 0xF0) >> 4));
    s_calib.dig_H6 = (int8_t)calib_e1_e7[6];

    ESP_LOGI(TAG, "Calibration data read successfully. T1=%d, T2=%d, T3=%d, H1=%d, H2=%d", 
             s_calib.dig_T1, s_calib.dig_T2, s_calib.dig_T3, s_calib.dig_H1, s_calib.dig_H2);
    return ESP_OK;
}

static float bme280_compensate_temp(int32_t adc_T) {
    float var1, var2, T;
    var1 = (((float)adc_T) / 16384.0f - ((float)s_calib.dig_T1) / 1024.0f) * ((float)s_calib.dig_T2);
    var2 = ((((float)adc_T) / 131072.0f - ((float)s_calib.dig_T1) / 8192.0f) *
            (((float)adc_T) / 131072.0f - ((float)s_calib.dig_T1) / 8192.0f)) * ((float)s_calib.dig_T3);
    s_calib.t_fine = (int32_t)(var1 + var2);
    T = (var1 + var2) / 5120.0f;
    return T;
}

static float bme280_compensate_humidity(int32_t adc_H) {
    float var_H;
    var_H = (((float)s_calib.t_fine) - 76800.0f);
    var_H = (adc_H - (((float)s_calib.dig_H4) * 64.0f + ((float)s_calib.dig_H5) / 16384.0f * var_H)) *
            (((float)s_calib.dig_H2) / 65536.0f * (1.0f + ((float)s_calib.dig_H6) / 67108864.0f * var_H *
                                                 (1.0f + ((float)s_calib.dig_H3) / 67108864.0f * var_H)));
    var_H = var_H * (1.0f - ((float)s_calib.dig_H1) * var_H / 524288.0f);
    if (var_H > 100.0f) {
        var_H = 100.0f;
    } else if (var_H < 0.0f) {
        var_H = 0.0f;
    }
    return var_H;
}

esp_err_t bme280_init(void) {
    // 1. Initialize I2C Master Bus
    i2c_master_bus_config_t bus_config = {
        .i2c_port = BME280_I2C_PORT,
        .sda_io_num = BME280_I2C_SDA_PIN,
        .scl_io_num = BME280_I2C_SCL_PIN,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .flags.enable_internal_pullup = true,
    };
    
    esp_err_t err = i2c_new_master_bus(&bus_config, &s_i2c_bus_handle);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to create I2C bus: %s. Falling back to simulation mode.", esp_err_to_name(err));
        s_is_simulated = true;
        return ESP_OK;
    }
    
    // 2. Add BME280 device to the bus
    i2c_device_config_t dev_config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BME280_I2C_ADDR,
        .scl_speed_hz = 100000, // 100 kHz
    };
    
    err = i2c_master_bus_add_device(s_i2c_bus_handle, &dev_config, &s_bme280_dev);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to add BME280 to I2C bus: %s. Falling back to simulation mode.", esp_err_to_name(err));
        s_is_simulated = true;
        return ESP_OK;
    }
    
    // 3. Probe the sensor (Read ID register)
    uint8_t chip_id = 0;
    err = bme280_read_regs(BME280_REG_ID, &chip_id, 1);
    if (err != ESP_OK || chip_id != 0x60) {
        ESP_LOGW(TAG, "BME280 chip ID signature check failed (got 0x%02X, expected 0x60). Sourcing simulation.", chip_id);
        s_is_simulated = true;
        return ESP_OK;
    }
    
    ESP_LOGI(TAG, "Physical BME280 detected successfully (Chip ID: 0x60). Initializing hardware parameters.");
    
    // 4. Reset Sensor
    err = bme280_write_reg(BME280_REG_RESET, 0xB6);
    if (err != ESP_OK) return err;
    vTaskDelay(pdMS_TO_TICKS(40)); // wait for reset to finish
    
    // Read calibration data
    err = read_calibration_data();
    if (err != ESP_OK) return err;
    
    // Configure sensor: ctrl_hum first, then ctrl_meas
    // ctrl_hum = 0x01 (Humidity oversampling x1)
    err = bme280_write_reg(BME280_REG_CTRL_HUM, 0x01);
    if (err != ESP_OK) return err;
    
    // ctrl_meas = 0x23 (Temp oversampling x1, Pressure disabled, Mode Normal)
    err = bme280_write_reg(BME280_REG_CTRL_MEAS, 0x23);
    if (err != ESP_OK) return err;
    
    s_is_simulated = false;
    return ESP_OK;
}

esp_err_t bme280_read_data(bme280_data_t *data) {
    if (data == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    
    if (s_is_simulated) {
        // Fetch current compressor relay pin state (configured as output)
        int cooling_active = gpio_get_level(COMPRESSOR_RELAY_GPIO);
        
        // Sim physics model (Tuned for PID stability Kp=3.0, Ki=0.05, Kd=1.5):
        if (cooling_active) {
            // Temperature decreases towards cold chamber target
            s_sim_temp -= 0.25f;
            if (s_sim_temp < -20.0f) s_sim_temp = -20.0f;
            
            // Humidity decreases slightly due to condensation
            s_sim_humidity -= 0.12f;
            if (s_sim_humidity < 35.0f) s_sim_humidity = 35.0f;
        } else {
            // Temperature rises toward ambient cargo truck temperature
            s_sim_temp += 0.10f;
            if (s_sim_temp > 24.0f) s_sim_temp = 24.0f;
            
            // Humidity rises slowly toward ambient
            s_sim_humidity += 0.08f;
            if (s_sim_humidity > 60.0f) s_sim_humidity = 60.0f;
        }
        
        data->temperature = s_sim_temp;
        data->humidity = s_sim_humidity;
        data->is_simulated = true;
        return ESP_OK;
    }
    
    // Otherwise, query physical I2C registers
    // Read 5 bytes: Temp MSB, LSB, XLSB, Hum MSB, LSB starting from 0xFA
    uint8_t raw_data[5];
    esp_err_t err = bme280_read_regs(0xFA, raw_data, 5);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to read raw sensor registers. Reverting to fallback.");
        return err;
    }
    
    // Reconstruct raw ADC values
    int32_t adc_T = (raw_data[0] << 12) | (raw_data[1] << 4) | (raw_data[2] >> 4);
    int32_t adc_H = (raw_data[3] << 8) | raw_data[4];
    
    // Compensate
    data->temperature = bme280_compensate_temp(adc_T);
    data->humidity = bme280_compensate_humidity(adc_H);
    data->is_simulated = false;
    
    return ESP_OK;
}

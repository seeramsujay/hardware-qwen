#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "bme280_driver.h"
#include "telemetry_engine.h"

static const char *TAG = "MAIN_APP";

#define COMPRESSOR_RELAY_GPIO   GPIO_NUM_10
#define DEFAULT_SETPOINT        4.0f // 4.0 °C default target

// PID Tuning constants
#define PID_KP                  3.0f
#define PID_KI                  0.05f
#define PID_KD                  1.5f

static float s_setpoint = DEFAULT_SETPOINT;

// PID Task running on Core 1
void pid_control_task(void *pvParameters) {
    bme280_data_t sensor_data;
    float integral = 0.0f;
    float prev_error = 0.0f;
    const float dt = 1.0f; // Task run rate in seconds
    
    ESP_LOGI(TAG, "PID Control Task started on Core %d. Target Setpoint: %.2f °C", 
             xPortGetCoreID(), s_setpoint);
    
    while (1) {
        // Read BME280 data
        if (bme280_read_data(&sensor_data) == ESP_OK) {
            // Update telemetry data store with newest values
            telemetry_engine_update_sensor(sensor_data.temperature, sensor_data.humidity, sensor_data.is_simulated);
            
            // Calculate PID output
            // For cooling, error is positive when we are too warm (temperature > setpoint)
            float error = sensor_data.temperature - s_setpoint;
            
            // Integral term with windup protection
            integral += error * dt;
            if (integral > 10.0f) integral = 10.0f;
            else if (integral < -10.0f) integral = -10.0f;
            
            // Derivative term
            float derivative = (error - prev_error) / dt;
            prev_error = error;
            
            float control_output = (PID_KP * error) + (PID_KI * integral) + (PID_KD * derivative);
            
            // Actuate Relay based on PID control value with hysteresis
            uint8_t next_relay_state = 0;
            if (control_output > 0.5f) {
                next_relay_state = 1; // Turn compressor ON
            } else if (control_output < 0.1f) {
                next_relay_state = 0; // Turn compressor OFF
            } else {
                // Hysteresis band: keep current state
                next_relay_state = gpio_get_level(COMPRESSOR_RELAY_GPIO);
            }
            
            gpio_set_level(COMPRESSOR_RELAY_GPIO, next_relay_state);
            telemetry_engine_update_relay(next_relay_state);
            
            // Handle Thermal Breach Alerts (Threshold: 8.0 °C for biologics/vaccines)
            if (sensor_data.temperature > 8.0f) {
                telemetry_engine_set_alert(true);
                ESP_LOGW("THERMAL_MONITOR", "WARNING: Temperature breach! Current: %.2f °C (Limit: 8.00 °C)", 
                         sensor_data.temperature);
            } else {
                telemetry_engine_set_alert(false);
            }
            
            ESP_LOGD("PID_LOOP", "Temp: %.2f, Error: %.2f, Integral: %.2f, Out: %.2f, Relay: %d",
                     sensor_data.temperature, error, integral, control_output, next_relay_state);
        } else {
            ESP_LOGE("PID_LOOP", "BME280 read failed.");
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// Telemetry Reporting Task running on Core 0
void telemetry_reporting_task(void *pvParameters) {
    uint8_t packet_buf[20];
    telemetry_data_t data;
    
    ESP_LOGI(TAG, "Telemetry Reporting Task started on Core %d", xPortGetCoreID());
    
    while (1) {
        // 1. Log Human-Readable Plain Telemetry
        if (telemetry_engine_get_data(&data) == ESP_OK) {
            ESP_LOGI("TELEMETRY", "Local State: Time: %lld us | Temp: %.2f °C | Hum: %.2f%% | Compressor: %s | Alert: %s | Mode: %s",
                     data.timestamp, data.temperature, data.humidity,
                     data.relay_state ? "RUNNING" : "STANDBY",
                     data.thermal_breach_alert ? "CRITICAL BREACH" : "NOMINAL",
                     data.is_simulated ? "SIMULATION" : "HARDWARE");
        }
        
        // 2. Log Serialized Low-Overhead Binary Packet (20 Bytes)
        if (get_cryo_telemetry_snapshot(packet_buf, sizeof(packet_buf)) == ESP_OK) {
            char hex_buf[64] = {0};
            int offset = 0;
            for (size_t i = 0; i < sizeof(packet_buf); i++) {
                offset += snprintf(hex_buf + offset, sizeof(hex_buf) - offset, "%02X ", packet_buf[i]);
            }
            
            // Checksum verification
            uint8_t computed_sum = 0;
            for (size_t i = 0; i < 19; i++) {
                computed_sum += packet_buf[i];
            }
            
            ESP_LOGI("SERIALIZATION", "Binary Frame (Size: %d B) | Checksum: Computed=0x%02X, Packet=0x%02X | Hex: %s",
                     (int)sizeof(packet_buf), computed_sum, packet_buf[19], hex_buf);
        }
        
        vTaskDelay(pdMS_TO_TICKS(4000)); // Publish/Report rate: 4 seconds
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "Bootstrapping CryoKrypton Core firmware application...");
    
    // 1. Initialize NVS (Non-Volatile Storage)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // 2. Fetch target temperature setpoint from NVS
    nvs_handle_t nvs_storage;
    ret = nvs_open("storage", NVS_READWRITE, &nvs_storage);
    if (ret == ESP_OK) {
        int32_t stored_val = 0;
        ret = nvs_get_i32(nvs_storage, "setpoint", &stored_val);
        if (ret == ESP_OK) {
            s_setpoint = (float)stored_val / 100.0f;
            ESP_LOGI(TAG, "Fetched temperature setpoint from NVS: %.2f °C", s_setpoint);
        } else if (ret == ESP_ERR_NVS_NOT_FOUND) {
            s_setpoint = -18.0f; // Force safe compliance limit
            ESP_LOGW(TAG, "WARNING: Target setpoint NOT FOUND in NVS! Forcing safe default compliance threshold of %.2f °C", s_setpoint);
            // Write standard default if not set
            nvs_set_i32(nvs_storage, "setpoint", (int32_t)(s_setpoint * 100.0f));
            nvs_commit(nvs_storage);
        } else {
            ESP_LOGE(TAG, "Error fetching setpoint from NVS (%s). Using default: %.2f °C", 
                     esp_err_to_name(ret), s_setpoint);
        }
        nvs_close(nvs_storage);
    } else {
        ESP_LOGE(TAG, "Error opening NVS storage namespace (%s). Using default: %.2f °C", 
                 esp_err_to_name(ret), s_setpoint);
    }
    
    // 3. Initialize Compressor Relay GPIO Pin
    gpio_config_t relay_cfg = {
        .pin_bit_mask = (1ULL << COMPRESSOR_RELAY_GPIO),
        .mode = GPIO_MODE_INPUT_OUTPUT, // Readback functionality required for simulator modeling
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&relay_cfg));
    gpio_set_level(COMPRESSOR_RELAY_GPIO, 0); // Initialize relay to OFF
    
    // 4. Initialize Telemetry Engine
    ESP_ERROR_CHECK(telemetry_engine_init());
    
    // 5. Initialize BME280 Driver
    ESP_ERROR_CHECK(bme280_init());
    
    // 6. Spawn PID Loop control task on Core 1 (APP_CPU)
    // Runs at high priority to ensure refrigeration control is never starved by network tasks
    xTaskCreatePinnedToCore(
        pid_control_task,
        "PID_Control_Task",
        4096,
        NULL,
        configMAX_PRIORITIES - 1, // High priority
        NULL,
        1 // Core 1 (APP_CPU)
    );
    
    // 7. Spawn Telemetry Reporting Task on Core 0 (PRO_CPU)
    xTaskCreatePinnedToCore(
        telemetry_reporting_task,
        "Telemetry_Reporting",
        4096,
        NULL,
        tskIDLE_PRIORITY + 2, // Low-medium priority
        NULL,
        0 // Core 0 (PRO_CPU)
    );
    
    ESP_LOGI(TAG, "Bootstrapping complete. Tasks dispatched to FreeRTOS scheduler.");
}

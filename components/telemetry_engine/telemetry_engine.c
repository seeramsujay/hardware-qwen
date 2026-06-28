#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "telemetry_engine.h"
#include "security_engine.h"
#include "mbedtls/sha256.h"
#include "mbedtls/version.h"

static SemaphoreHandle_t s_telemetry_mutex = NULL;
static telemetry_data_t s_current_data;

esp_err_t telemetry_engine_init(void) {
    if (s_telemetry_mutex != NULL) {
        return ESP_OK; // Already initialized
    }
    
    s_telemetry_mutex = xSemaphoreCreateMutex();
    if (s_telemetry_mutex == NULL) {
        return ESP_ERR_NO_MEM;
    }
    
    s_current_data.temperature = 22.0f;
    s_current_data.humidity = 55.0f;
    s_current_data.is_simulated = true;
    s_current_data.thermal_breach_alert = false;
    s_current_data.relay_state = 0;
    s_current_data.timestamp = 0;
    
    return ESP_OK;
}

esp_err_t telemetry_engine_update_sensor(float temp, float hum, bool is_simulated) {
    if (s_telemetry_mutex == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    if (xSemaphoreTake(s_telemetry_mutex, portMAX_DELAY) == pdTRUE) {
        s_current_data.temperature = temp;
        s_current_data.humidity = hum;
        s_current_data.is_simulated = is_simulated;
        s_current_data.timestamp = esp_timer_get_time();
        xSemaphoreGive(s_telemetry_mutex);
        return ESP_OK;
    }
    return ESP_ERR_TIMEOUT;
}

esp_err_t telemetry_engine_update_relay(uint8_t state) {
    if (s_telemetry_mutex == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    if (xSemaphoreTake(s_telemetry_mutex, portMAX_DELAY) == pdTRUE) {
        s_current_data.relay_state = state;
        s_current_data.timestamp = esp_timer_get_time();
        xSemaphoreGive(s_telemetry_mutex);
        return ESP_OK;
    }
    return ESP_ERR_TIMEOUT;
}

esp_err_t telemetry_engine_set_alert(bool alert) {
    if (s_telemetry_mutex == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    if (xSemaphoreTake(s_telemetry_mutex, portMAX_DELAY) == pdTRUE) {
        s_current_data.thermal_breach_alert = alert;
        s_current_data.timestamp = esp_timer_get_time();
        xSemaphoreGive(s_telemetry_mutex);
        return ESP_OK;
    }
    return ESP_ERR_TIMEOUT;
}

esp_err_t telemetry_engine_get_data(telemetry_data_t *out_data) {
    if (s_telemetry_mutex == NULL || out_data == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    if (xSemaphoreTake(s_telemetry_mutex, portMAX_DELAY) == pdTRUE) {
        *out_data = s_current_data;
        xSemaphoreGive(s_telemetry_mutex);
        return ESP_OK;
    }
    return ESP_ERR_TIMEOUT;
}

esp_err_t get_cryo_telemetry_snapshot(uint8_t *out_buffer, size_t buffer_len) {
    if (s_telemetry_mutex == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    if (out_buffer == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (buffer_len < sizeof(cryo_telemetry_packet_t)) {
        return ESP_ERR_INVALID_SIZE;
    }
    
    if (xSemaphoreTake(s_telemetry_mutex, portMAX_DELAY) == pdTRUE) {
        cryo_telemetry_packet_t packet;
        packet.timestamp = s_current_data.timestamp;
        packet.temperature = s_current_data.temperature;
        packet.humidity = s_current_data.humidity;
        packet.relay_state = s_current_data.relay_state;
        
        // Assemble flags byte
        uint8_t flags = 0;
        if (s_current_data.is_simulated) {
            flags |= (1 << 0);
        }
        if (s_current_data.thermal_breach_alert) {
            flags |= (1 << 1);
        }
        packet.flags = flags;
        packet.reserved = 0x00; // Zero padding
        
        // Compute checksum of the first 19 bytes (0 to 18)
        uint8_t sum = 0;
        uint8_t *ptr = (uint8_t *)&packet;
        for (size_t i = 0; i < 19; i++) {
            sum += ptr[i];
        }
        packet.checksum = sum;
        
        // Copy to target buffer
        memcpy(out_buffer, &packet, sizeof(cryo_telemetry_packet_t));
        
        xSemaphoreGive(s_telemetry_mutex);
        return ESP_OK;
    }
    return ESP_ERR_TIMEOUT;
}

esp_err_t get_signed_telemetry_snapshot(uint8_t *out_buffer, size_t buffer_len) {
    if (out_buffer == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (buffer_len < sizeof(signed_telemetry_packet_t)) {
        return ESP_ERR_INVALID_SIZE;
    }

    signed_telemetry_packet_t signed_pkt;
    
    // 1. Get the unsigned telemetry snapshot (thread-safe, handles mutex internally)
    esp_err_t err = get_cryo_telemetry_snapshot((uint8_t *)&signed_pkt.telemetry, sizeof(signed_pkt.telemetry));
    if (err != ESP_OK) {
        return err;
    }

    // 2. Compute SHA-256 digest of the 20-byte telemetry packet
    uint8_t hash[32];
    mbedtls_sha256_context ctx;
    mbedtls_sha256_init(&ctx);
    
#if MBEDTLS_VERSION_NUMBER >= 0x03000000
    mbedtls_sha256_starts(&ctx, 0);
    mbedtls_sha256_update(&ctx, (const unsigned char *)&signed_pkt.telemetry, sizeof(signed_pkt.telemetry));
    mbedtls_sha256_finish(&ctx, hash);
#else
    mbedtls_sha256_starts_ret(&ctx, 0);
    mbedtls_sha256_update_ret(&ctx, (const unsigned char *)&signed_pkt.telemetry, sizeof(signed_pkt.telemetry));
    mbedtls_sha256_finish_ret(&ctx, hash);
#endif
    mbedtls_sha256_free(&ctx);

    // 3. Sign the 32-byte hash using the security engine
    size_t sig_len = 0;
    err = security_engine_sign_hash(hash, signed_pkt.signature, &sig_len);
    if (err != ESP_OK) {
        return err;
    }

    if (sig_len != 256) {
        return ESP_ERR_INVALID_STATE;
    }

    // 4. Copy the completed signed packet to output buffer
    memcpy(out_buffer, &signed_pkt, sizeof(signed_telemetry_packet_t));
    return ESP_OK;
}


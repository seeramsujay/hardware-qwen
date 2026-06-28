#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

// RSA-2048 signature size is exactly 256 bytes (2048 bits)
#define RSA_SIG_SIZE_BYTES 256

/**
 * @brief Initialize the security engine.
 *        Attempts to verify if hardware Digital Signature (DS) keys are provisioned in NVS/flash.
 *        If not, initializes a software-based RSA fallback for simulation/prototyping.
 * @return ESP_OK on success.
 */
esp_err_t security_engine_init(void);

/**
 * @brief Cryptographically sign a 32-byte message hash (SHA-256 digest) using
 *        either the hardware DS peripheral or the software fallback.
 * 
 * @param[in] hash 32-byte SHA-256 digest buffer.
 * @param[out] sig_out Buffer of at least 256 bytes to store the resulting RSA signature.
 * @param[out] sig_len Pointer to store the actual size of the generated signature.
 * @return ESP_OK on success, or an appropriate error code.
 */
esp_err_t security_engine_sign_hash(const uint8_t *hash, uint8_t *sig_out, size_t *sig_len);

/**
 * @brief Retrieve the public key (PEM format) to export to the cloud or other components.
 * 
 * @param[out] key_out Buffer to copy the PEM public key string to.
 * @param[in,out] key_len Input: capacity of key_out buffer. Output: actual string length copied.
 * @return ESP_OK on success, or ESP_ERR_INVALID_SIZE if the buffer is too small.
 */
esp_err_t security_engine_get_public_key(char *key_out, size_t *key_len);

/**
 * @brief Helper function to check if the security engine is currently running in simulated/software-fallback mode.
 * @return true if using software simulation, false if using physical hardware DS peripheral.
 */
bool security_engine_is_simulated(void);

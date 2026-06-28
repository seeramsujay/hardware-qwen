idf_component_register(SRCS "security_engine.c"
                      INCLUDE_DIRS "include"
                      REQUIRES mbedtls esp_hw_support nvs_flash)

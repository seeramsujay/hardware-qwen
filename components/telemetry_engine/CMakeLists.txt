idf_component_register(SRCS "telemetry_engine.c"
                       INCLUDE_DIRS "include"
                       REQUIRES esp_timer mbedtls security_engine)


Roadmap: CryoKrypton

Legend
DONE | ACTIVE | BLOCKED | COLAB | LOCAL | RISK

Phases

Phase 1 — Firmware & Simulation Foundation [DONE]
Goal: Establish edge simulation models and basic sensor polling fallback.
Depends: None

[x] Set up ESP-IDF project scaffold — CMakeLists.txt and sdkconfig configured.
[x] Provision Identity (Software Fallback Mode) — RSA key pair generated and integrated into firmware simulation, bypassing irreversible eFuse HMAC operations.
[x] Interface BME280 sensor — I2C driver implemented with software thermal simulation fallback (-20°C lower limit).
[x] Implement PID Control Loop — Core thermal logic pinned to Core 1 (APP_CPU) with NVS setpoint persistence and relay hysteresis.

Phase 2 — Secure Telemetry [DONE]
Goal: Cryptographically signed data frames and security engine.
Depends: Phase 1

[x] Implement Software RSA Security Engine — Mbed TLS RSA-2048 signing fallback implemented in C firmware.
[x] Write Binary Compressor and Signer — 20-byte packed telemetry struct with checksum and 256-byte signature framing.
[x] [COLAB] Validate Telemetry Signatures — `verify_signature.py` self-test passing.

Phase 3 — Edge Vision & Media [SIMULATED]
Goal: Simulated image chunking and transport.
Depends: Phase 2

[x] Implement MQTT Chunking Simulation — 32KB slice simulation with JSON chunk reassembly demonstrated in `cloud_backend.py`.

Phase 4 — Agentic AI Logic [DONE]
Goal: Simulated Qwen3.7-Plus orchestration for compliance auditing and rerouting.
Depends: Phase 3

[x] Prototype Agent Prompts — Simulated Qwen3.7-Plus reasoning loop implemented in `cloud_backend.py`.
[x] Implement Orchestration Layer — Simulated ingress -> Reassembler -> Signature Gate -> AI reasoning.
[x] End-to-End Validation — Verified across 3 operational scenarios (Normal, Anomaly/Spoilage, Security Spoofing).

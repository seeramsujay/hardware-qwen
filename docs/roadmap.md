Roadmap: ESP32 Cold-Chain Compliance Agent

Legend
DONE | ACTIVE | BLOCKED | COLAB | LOCAL | RISK

Phases

Phase 1 — Hardware Foundation [LOCAL]
Goal: Establish secure edge identity and basic sensor polling.
Depends: None

[ ] Set up ESP-IDF environment on MacBook Air — Ensure `esptool` and `espefuse` are in path.
[ ] Provision eFuse Keys — Burn NIST P-256 private key to BLOCK_KEY0. Constraint: Irreversible. Skill: Cryptographic Provisioning.
[ ] Interface BME280 sensor — Validate I2C connectivity and raw telemetry acquisition.
[ ] Implement PID Control Loop — Core thermal logic; must run on Core 1 (APP_CPU) to avoid network starvation. Risk: CPU starvation.

Phase 2 — Secure Telemetry [LOCAL|COLAB]
Goal: Cryptographically signed data ingress to Alibaba Cloud.
Depends: Phase 1

[ ] Implement Hardware SHA-256 + ECDSA — Utilize Mbed TLS hardware hooks for sub-10ms signing.
[ ] Configure Alibaba MQTT Broker — Set up ApsaraMQ with MQTT 5.0.
[ ] Write JSON Signer — Package sensor data + image UUID + timestamp into signed JWS/JSON.
[ ] [COLAB] Validate Telemetry Ingress — Script to monitor MQTT topic and verify signatures using public key. Colab: Yes — python verification script.

Phase 3 — Edge Vision & Media [LOCAL]
Goal: Memory-resilient image capture and chunked transmission.
Depends: Phase 2

[ ] Initialize ESP32-CAM — Set `grab_mode` to `CAMERA_GRAB_LATEST` and `fb_count` in PSRAM.
[ ] Implement MQTT Chunking — 32KB slices with binary headers. Skill: Resilient MQTT Media Transfer. Constraint: internal heap limits.
[ ] Implement Backpressure logic — Wait for PUBACK before next chunk. Risk: Heap fragmentation.
[ ] Develop Cloud Reassembler — Alibaba Function Compute to buffer chunks in Redis and upload to OSS.

Phase 4 — Agentic AI Logic [COLAB|LOCAL]
Goal: Deploy Qwen3.7-Plus for compliance auditing and rerouting.
Depends: Phase 3

[ ] [COLAB] Prototype Agent Prompts — Test thermodynamic decay reasoning with Qwen3.7-Plus. Colab: Yes — API testing notebook. Skill: Multimodal Agent Orchestration.
[ ] Implement Orchestration Layer — Connect MQTT trigger -> Cloud Reassembler -> DashScope API.
[ ] Integrate Logistics API — Tool-calling for rerouting logic based on `time_to_spoilage`.
[ ] End-to-End Validation — Simulated thermal breach and visual audit verification. Risk: Bill shock from token usage.

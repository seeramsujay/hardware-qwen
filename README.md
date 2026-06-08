# ESP32 Cold-Chain Compliance Agent

**Zero-trust edge auditing for high-value biologicals using hardware-backed cryptography and Qwen3.7-Plus.**

The global pharmaceutical supply chain relies on fragile, cloud-dependent sensors that are trivial to forge. This project turns the ESP32-CAM into an autonomous, cryptographically secure compliance agent capable of locally signing audit trails and orchestrating complex logistics interventions via multimodal AI.

## Install

Requires [ESP-IDF v5.2+](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/) and an Alibaba Cloud account.

```bash
# Clone and install dependencies
git clone https://github.com/suzaykid/hardware-qwen.git
cd hardware-qwen
idf.py set-target esp32s3
idf.py menuconfig # Configure MQTT and DashScope credentials
```

## Usage

1. **Provision Identity**: Burn the ECDSA key to eFuse (Permanent).
   ```bash
   espefuse.py burn_key BLOCK_KEY0 private_key.pem ECDSA_KEY
   ```
2. **Flash Firmware**:
   ```bash
   idf.py build flash monitor
   ```
3. **Deploy Orchestrator**: Deploy the reassembler to Alibaba Cloud Function Compute.

## How It Works

The system utilizes a dual-layer "Signed-Edge, Reasoned-Cloud" architecture:

- **Edge (ESP32-CAM)**: Maintains a high-priority PID loop for thermal control. It captures images and sensor data, signs them using the hardware `ECDSA_DS` peripheral, and transmits them via a 32KB chunked MQTT protocol.
- **Cloud (Qwen3.7-Plus)**: Reassembles chunks, verifies signatures, and analyzes the multimodal payload. It runs localized thermodynamic decay models to predict "Time to Spoilage" and autonomously triggers rerouting via tool-calling.

```mermaid
graph TD
    A[ESP32: BME280 + Camera] -->|Hardware ECDSA| B(MQTT Chunking)
    B -->|Jitter Resilience| C[Alibaba Cloud Broker]
    C --> D[Function Compute: Reassembler]
    D --> E[Qwen3.7-Plus Agent]
    E -->|Tool Calling| F[Logistics API: Rerouting]
```

## Status

**Alpha**: Core eFuse provisioning and chunked MQTT transmission are implemented. PID logic and Qwen API integration are in active prototyping.

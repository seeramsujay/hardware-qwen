# CryoKrypton

**Zero-trust edge auditing for high-value biologicals using hardware-backed cryptography and Qwen3.7-Plus.**

The global pharmaceutical supply chain relies on fragile, cloud-dependent sensors that are trivial to forge. CryoKrypton turns the ESP32-S3-CAM (or ESP32-S3 equipped with a camera module) into an autonomous, cryptographically secure compliance agent capable of locally signing audit trails and orchestrating complex logistics interventions via multimodal AI.

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

1. **Provision Identity**: 
   * **Development Mode (Option A - Software Fallback)**: No eFuse operations required. The firmware automatically uses the software-embedded testing RSA key pair.
   * **Production Hardware Mode**: Burn the HMAC key to eFuse (Permanent) to wrap the private key for the Digital Signature (DS) peripheral:
     ```bash
     espefuse.py -p $PORT burn_key BLOCK_KEY0 hmac_key.bin HMAC_DS
     python3 -m esp_secure_cert.make_secure_cert_image --private-key private_key.pem --secure-cert-type ds --priv-key-len 2048 --hmac-key-file hmac_key.bin --output-file secure_cert_partition.bin
     esptool.py -p $PORT write_flash 0xd0000 secure_cert_partition.bin
     ```
2. **Flash Firmware**:
   ```bash
   idf.py build flash monitor
   ```
3. **Deploy Orchestrator**: Deploy the reassembler to Alibaba Cloud Function Compute to reassemble visual chunks and unpack the binary telemetry.

## How It Works

The system utilizes a dual-layer "Signed-Edge, Reasoned-Cloud" architecture:

- **Edge (ESP32-S3-CAM)**: Maintains a high-priority PID loop for thermal control. It captures images and sensor data, compresses the local sensor frames into space-efficient binary payloads or minimal arrays, signs them using the hardware Digital Signature (DS) peripheral, and transmits them via a 32KB chunked MQTT protocol.
- **Cloud (Qwen3.7-Plus)**: Reassembles chunks, verifies signatures, and unpacks the binary sensor payloads into structured JSON within the Function Compute reassembler prior to hitting the Qwen API. It runs localized thermodynamic decay models to predict "Time to Spoilage" and autonomously triggers rerouting via tool-calling.

```mermaid
graph TD
    A[ESP32-S3: BME280 + Camera] -->|Binary Compression & DS Sign| B(MQTT Chunking)
    B -->|Jitter Resilience| C[Alibaba Cloud Broker]
    C --> D[Function Compute: Reassembler & Unpacker]
    D --> E[Qwen3.7-Plus Agent]
    E -->|Tool Calling| F[Logistics API: Rerouting]
```

## Status

**Alpha**: Core eFuse provisioning and chunked MQTT transmission are implemented. PID logic and Qwen API integration are in active prototyping.

# Async Team Work-Split Roadmap

This document outlines the asynchronous work-split for a team of 5 people to build the **ESP32-S3 Cold-Chain Compliance Agent**. The team consists of **4 highly technical engineers** and **1 QA/Compliance coordinator** (focused on processes, FDA validation, and coordination).

---

```mermaid
graph TD
    subgraph Edge Layer (ESP32-S3)
        R1[Role 1: Firmware & Control] -->|Telemetry Structs / PID Loop| R3[Role 3: Media & Transport]
        R2[Role 2: Cryptographic Security] -->|DS Signing APIs / Key Wrappers| R3
    end
    subgraph Cloud Layer (Alibaba Cloud)
        R3 -->|Binary MQTT Chunks| R4[Role 4: Cloud & AI Orchestration]
    end
    subgraph Validation & Process
        R5[Role 5: Compliance & QA] -.->|FDA 21 CFR Part 11 Mapping & Testing| R1
        R5 -.->|Compliance Audit Gates| R2
        R5 -.->|System Verification Plan| R3
        R5 -.->|AI System Prompts / Test Vectors| R4
    end
```

---

## Role 1: Firmware & Local Control Loop Engineer (Edge Core)
*Highly Technical*

This role focuses on building the hardware foundation, reading sensors, and ensuring stable thermal control at the edge.

### Key Responsibilities
1. Configure the core ESP-IDF environment for ESP32-S3.
2. Initialize BME280 sensor via I2C and pull raw telemetry.
3. Write a high-priority, thread-safe thermal PID control loop.
4. Separate the application/PID loop from network tasks using FreeRTOS.

### Task Breakdown
- **Task 1.1**: Set up the ESP-IDF project structure targeting `esp32s3` with standard NVS, PSRAM, and FreeRTOS support.
- **Task 1.2**: Write the I2C driver interface for the BME280 temperature and humidity sensor.
- **Task 1.3**: Implement the PID control algorithm to actuate refrigerator compressor relays based on temperature readings.
- **Task 1.4**: Pin the PID loop to Core 1 (`APP_CPU`) using `xTaskCreatePinnedToCore` to prevent network/modem operations on Core 0 from stalling refrigeration logic.

### Interface Boundaries
* **Inputs**: Target temperature setpoint configuration from memory/NVS.
* **Outputs**: Raw sensor telemetry data structure (`float temp`, `float humidity`, `uint64_t timestamp`) exposed via a thread-safe getter, and relay GPIO states.

---

## Role 2: Cryptographic Security & Identity Provisioning Engineer (Edge Security)
*Highly Technical*

This role handles secure identity provisioning, hardware key wrapping, and out-of-visibility signature generation.

### Key Responsibilities
1. Develop the security provisioning workflow for the ESP32-S3.
2. Write scripts to generate and wrap ECDSA keys using eFuse HMAC blocks.
3. Implement hardware-accelerated SHA-256 and Digital Signature (DS) drivers.
4. Integrate DS peripheral operations into the Mbed TLS stack.

### Task Breakdown
- **Task 2.1**: Write `espefuse.py` and `espsecure.py` command scripts to burn a 256-bit HMAC key into `BLOCK_KEY0` and generate the encrypted private key wrapper.
- **Task 2.2**: Write the firmware module to register and load the wrapped key context from flash.
- **Task 2.3**: Interface with the ESP32-S3's hardware SHA engine to digest telemetry frames and images.
- **Task 2.4**: Create a secure signature utility API (`esp_ds_sign_hash`) that uses the DS peripheral to generate NIST P-256 signatures in sub-10ms.

### Interface Boundaries
* **Inputs**: Plain text message hash (32-byte SHA-256 digest) and the stored wrapped private key dataset.
* **Outputs**: DER-encoded 64-to-73 byte ECDSA cryptographic signature.

---

## Role 3: Media & Telemetry Transport Engineer (Edge Network)
*Highly Technical*

This role manages high-bandwidth data packaging, binary serialization, and network-resilient transmissions.

### Key Responsibilities
1. Initialize the ESP32-S3 camera driver and configure frame buffers in PSRAM.
2. Implement binary serialization (e.g. MessagePack) to compress sensor telemetry.
3. Design and implement the 32KB chunked MQTT transmission protocol.
4. Integrate backpressure limits to prevent out-of-memory (OOM) network crashes.

### Task Breakdown
- **Task 3.1**: Initialize the camera driver (`esp_camera`) in PSRAM, setting `grab_mode` to `CAMERA_GRAB_LATEST`.
- **Task 3.2**: Write a serialization component to compress the raw sensor telemetry from Role 1 into a compact binary struct or minimal array.
- **Task 3.3**: Write the MQTT 5.0 client wrapper utilizing native ESP-IDF `esp_mqtt` to manage topics and QoS 1 publishes.
- **Task 3.4**: Implement the chunking mechanism that prefixes a binary/BSON header (image UUID, chunk index, payload size) onto 32KB image chunks and serializes/publishes them sequentially. Manage backpressure by blocking until `PUBACK` is received if the outbox exceeds 128KB.

### Interface Boundaries
* **Inputs**: Camera frame buffer pointers, raw sensor telemetry data, and the signing API from Role 2.
* **Outputs**: Stream of 32KB MQTT payloads containing signed, compressed binary data and image chunks.

---

## Role 4: Cloud Ingress, Reassembly, & AI Orchestration Engineer (Cloud Core)
*Highly Technical*

This role builds the cloud reassembly logic, verifies edge signatures, and wires up the Qwen3.7-Plus agentic workflows.

### Key Responsibilities
1. Configure the Alibaba Cloud ApsaraMQ MQTT Broker.
2. Develop the reassembly and signature verification serverless function.
3. Unpack and deserialize the binary telemetry back into structured JSON.
4. Orchestrate Qwen3.7-Plus DashScope API agent calls and tool triggers.

### Task Breakdown
- **Task 4.1**: Configure ApsaraMQ and route MQTT message topics to Alibaba Cloud Function Compute.
- **Task 4.2**: Write the Function Compute reassembler script to cache chunks in Redis, verify they match the edge ECDSA signature, and upload the final image to Alibaba OSS.
- **Task 4.3**: Implement the binary telemetry deserializer inside Function Compute to unpack MessagePack/binary formats back to structured JSON.
- **Task 4.4**: Format and pass the verified image URL and JSON telemetry payload to Qwen3.7-Plus DashScope API. Define tool structures for logistics APIs (e.g., shipment rerouting triggers).

### Interface Boundaries
* **Inputs**: 32KB chunked MQTT payloads.
* **Outputs**: Verified OSS image URL, deserialized JSON telemetry, and outbound API calls to Qwen / Logistics endpoints.

---

## Role 5: Compliance, QA, & System Integration Coordinator (Less Technical / Process)
*Process, QA, and Verification Focused*

This role coordinates validation, documents FDA compliance mapping, handles system-level testing, enforces quality gates, and leads the team's hackathon management, presentation, and demo video preparation.

### Key Responsibilities
1. Map architectural components against FDA Title 21 CFR Part 11 requirements.
2. Design and coordinate the integration test plan.
3. Manage test vectors and run compliance audit tests.
4. Coordinate asynchronous code/artifact reviews and maintain project documentation.
5. Create the project presentation slides, organize the demo video recording, manage general hackathon deliverables (e.g., submission portal details, team profiles, Q&A prep), and oversee the final packaging.

### Task Breakdown
- **Task 5.1**: Map out the formal trace matrix linking code files (e.g. eFuse keys, DS peripherals) to FDA 21 CFR Part 11 regulations.
- **Task 5.2**: Establish a testing suite of mock environmental conditions (e.g. thermal breaches, connection drop simulations) and manage standard test payloads.
- **Task 5.3**: Author the system verification plan, documenting end-to-end telemetry paths and testing criteria for signature validity.
- **Task 5.4**: Orchestrate validation gates between the roles. Review Role 4's prompt templates and Role 2's key wrapping protocols, and aggregate output artifacts into a cohesive validation document.
- **Task 5.5**: Design and compile the final team presentation deck, coordinate the collection of screen recordings/demos from Roles 1-4, and edit/produce the final video walkthrough.
- **Task 5.6**: Manage hackathon logistics, including writing the Devpost/submission summary, configuring the public GitHub repository page, and prepping the team for judge Q&A sessions.

### Interface Boundaries
* **Inputs**: Pull requests, API outputs, and logs from Roles 1, 2, 3, and 4, plus screen capture contributions.
* **Outputs**: System verification report, compliance trace matrix, user manual, team presentation deck, project demo video, hackathon submission portal write-up, and overall quality sign-off.

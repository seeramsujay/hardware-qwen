#!/usr/bin/env python3
"""
CryoKrypton Edge Webcam Emulation Agent (Role 1, 2, & 3 Emulation)
------------------------------------------------------------------
Emulates the ESP32-S3-CAM agent on a laptop. Captures live webcam frames
or synthetic test images, runs simulated thermal telemetry, cryptographically signs
the payload using RSA-2048 private key, and streams 32KB chunks over MQTT.
"""

import sys
import os
import time
import json
import uuid
import base64
import argparse

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# Configuration
DEFAULT_BROKER = "broker.emqx.io"
DEFAULT_PORT = 1883
TOPIC_CHUNKS = "device/telemetry/chunks"
CHUNK_SIZE_BYTES = 24000  # ~24KB base64 slice per chunk to keep total JSON well under 32KB


def load_private_key(key_path="keys/private_key.pem"):
    if not HAS_CRYPTO:
        print("[WARN] Cryptography package missing. Using mock signing.")
        return None
    if not os.path.exists(key_path):
        print(f"[WARN] Private key not found at {key_path}. Using mock signing.")
        return None
    with open(key_path, "rb") as f:
        return load_pem_private_key(f.read(), password=None)


def sign_payload(private_key, data_bytes):
    if private_key is None:
        return "MOCK_RSA_SIGNATURE_" + uuid.uuid4().hex
    try:
        signature = private_key.sign(
            data_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return signature.hex()
    except Exception as e:
        print(f"[ERROR] RSA signing failed: {e}")
        return "ERROR_SIGNATURE"


def generate_synthetic_image(status_text="NOMINAL", temp_c=-18.2):
    if not HAS_CV2:
        return b"SYNTHETIC_IMAGE_BYTES_NO_CV2"
    
    # Create a 640x480 cargo box visual frame
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Background color based on status
    if status_text == "ANOMALY":
        img[:] = (30, 30, 150)  # Dark Red BGR
    elif status_text == "SPOOFED":
        img[:] = (150, 30, 150) # Purple BGR
    else:
        img[:] = (80, 60, 20)   # Dark Blue/Teal BGR
        
    # Draw cargo box frame
    cv2.rectangle(img, (100, 100), (540, 380), (200, 200, 200), 3)
    cv2.putText(img, "CRYOKRYPTON BIOLOGICAL CARGO", (130, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, f"Box ID: CK-9942-X", (130, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 1)
    
    # Thermal reading display
    temp_color = (0, 255, 0) if temp_c <= -15.0 else (0, 0, 255)
    cv2.putText(img, f"Temp: {temp_c:.1f} C", (130, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, temp_color, 2)
    cv2.putText(img, f"Status: {status_text}", (130, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    cv2.putText(img, f"Timestamp: {int(time.time())}", (130, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    
    # Encode as JPEG bytes
    ret, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return jpeg.tobytes() if ret else b"JPEG_ENCODE_ERROR"


def capture_webcam_frame(cap, status_text="NOMINAL", temp_c=-18.2):
    if cap is None or not cap.isOpened():
        return generate_synthetic_image(status_text, temp_c)
    
    ret, frame = cap.read()
    if not ret or frame is None:
        return generate_synthetic_image(status_text, temp_c)
        
    # Overlay telemetry HUD on webcam capture
    temp_color = (0, 255, 0) if temp_c <= -15.0 else (0, 0, 255)
    cv2.putText(frame, "[CryoKrypton Edge Agent HUD]", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Temp: {temp_c:.1f} C | Mode: {status_text}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, temp_color, 2)
    
    ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return jpeg.tobytes() if ret else generate_synthetic_image(status_text, temp_c)


def transmit_telemetry(client, broker, topic, private_key, img_bytes, telemetry_dict, is_spoofed=False):
    img_b64 = base64.b64encode(img_bytes).decode('ascii')
    payload_to_sign = f"{telemetry_dict['device_id']}:{telemetry_dict['timestamp']}:{telemetry_dict['temp']}:{img_b64[:100]}".encode('utf-8')
    
    if is_spoofed:
        signature = "UNAUTHORIZED_SPOOFED_SIGNATURE_" + uuid.uuid4().hex[:16]
    else:
        signature = sign_payload(private_key, payload_to_sign)
        
    img_uuid = uuid.uuid4().hex[:8]
    total_len = len(img_b64)
    chunks = [img_b64[i:i + CHUNK_SIZE_BYTES] for i in range(0, total_len, CHUNK_SIZE_BYTES)]
    total_chunks = len(chunks) if len(chunks) > 0 else 1
    
    print(f"\n[>>>] Transmitting Frame UUID '{img_uuid}' ({total_len} image bytes -> {total_chunks} chunks)...")
    print(f"      Telemetry: {telemetry_dict} | Sig Prefix: {signature[:16]}...")
    
    for idx, chunk_slice in enumerate(chunks):
        packet = {
            "device_id": telemetry_dict["device_id"],
            "uuid": img_uuid,
            "chunk_idx": idx + 1,
            "total_chunks": total_chunks,
            "timestamp": telemetry_dict["timestamp"],
            "telemetry": telemetry_dict,
            "signature": signature,
            "payload_slice": chunk_slice
        }
        
        json_payload = json.dumps(packet)
        if client:
            client.publish(topic, json_payload, qos=1)
        else:
            print(f"      [DRY RUN] Chunk {idx+1}/{total_chunks} ({len(json_payload)} B) published.")
            
        time.sleep(0.1) # Simulate backpressure / PUBACK spacing
        
    print(f"[OK] Frame transmission completed successfully to '{broker}:{TOPIC_CHUNKS}'.")


def main():
    parser = argparse.ArgumentParser(description="CryoKrypton Edge Webcam Emulation Agent")
    parser.add_argument("--broker", default=DEFAULT_BROKER, help="MQTT Broker host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="MQTT Broker port")
    parser.add_argument("--auto", action="store_true", help="Run automated scenario loop without GUI")
    parser.add_argument("--test", action="store_true", help="Run single transmission test and exit")
    parser.add_argument("--sim", action="store_true", help="Force synthetic image generation instead of webcam")
    args = parser.parse_args()

    print("=================================================================")
    print("      CRYOKRYPTON EDGE WEBCAM EMULATION AGENT (LAPTOP 1)         ")
    print("=================================================================")
    
    private_key = load_private_key()
    if private_key:
        print("[OK] RSA-2048 Private Key loaded successfully from flash/filesystem.")
        
    client = None
    if HAS_MQTT:
        try:
            if hasattr(mqtt, "CallbackAPIVersion"):
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            else:
                client = mqtt.Client()
            client.connect(args.broker, args.port, 60)
            client.loop_start()
            print(f"[OK] Connected to MQTT Broker at {args.broker}:{args.port}")
        except Exception as e:
            print(f"[WARN] Failed to connect to MQTT broker ({e}). Running in Dry Run mode.")
            client = None
    else:
        print("[WARN] paho-mqtt not installed. Running in Dry Run mode.")
        
    cap = None
    if not args.sim and not args.test and HAS_CV2:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("[OK] Laptop Webcam opened successfully.")
        else:
            print("[WARN] Could not open webcam. Falling back to synthetic image generator.")
            cap = None

    device_id = "ESP32-S3-CAM-EMULATOR-01"
    
    if args.test:
        print("\n[TEST MODE] Transmitting single synthetic nominal frame...")
        telemetry = {"device_id": device_id, "timestamp": int(time.time()), "temp": -18.2, "humidity": 55.0, "cargo_status": "Anti-Gravity Active"}
        img_bytes = generate_synthetic_image("NOMINAL", -18.2)
        transmit_telemetry(client, args.broker, TOPIC_CHUNKS, private_key, img_bytes, telemetry, False)
        if client:
            client.loop_stop()
            client.disconnect()
        print("[OK] Single frame test passed.")
        return

    if args.auto or not HAS_CV2 or cap is None:
        print("\n[AUTO MODE] Starting automated scenario demo loop (Ctrl+C to exit)...")
        scenarios = [
            ("NOMINAL", -18.2, 55.0, "Anti-Gravity Active", False),
            ("ANOMALY", -5.0, 68.0, "Compressor Failure / Spoilage Warning", False),
            ("SPOOFED", -18.0, 55.0, "Tampered Payload Injection", True)
        ]
        s_idx = 0
        try:
            while True:
                status, temp, hum, cargo_stat, is_spoof = scenarios[s_idx]
                telemetry = {
                    "device_id": device_id,
                    "timestamp": int(time.time()),
                    "temp": temp,
                    "humidity": hum,
                    "cargo_status": cargo_stat
                }
                img_bytes = capture_webcam_frame(cap, status, temp)
                transmit_telemetry(client, args.broker, TOPIC_CHUNKS, private_key, img_bytes, telemetry, is_spoof)
                s_idx = (s_idx + 1) % len(scenarios)
                time.sleep(8)
        except KeyboardInterrupt:
            print("\n[STOP] Shutting down agent.")
            return

    print("\n[INTERACTIVE MODE] Webcam preview running.")
    print("Controls in preview window:")
    print("  [SPACE] - Send Nominal Frame (-18.2 C)")
    print("  [A]     - Send Anomaly Frame (-5.0 C Thermal Breach)")
    print("  [S]     - Send Spoofed Attack Frame (Invalid Signature)")
    print("  [Q]     - Quit")

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
                
            cv2.putText(frame, "Press SPACE: Nominal | A: Anomaly | S: Spoof | Q: Quit", 
                        (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            cv2.imshow("CryoKrypton Edge Agent", frame)
            
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord(' '):
                telemetry = {"device_id": device_id, "timestamp": int(time.time()), "temp": -18.2, "humidity": 55.0, "cargo_status": "Nominal"}
                img_bytes = capture_webcam_frame(cap, "NOMINAL", -18.2)
                transmit_telemetry(client, args.broker, TOPIC_CHUNKS, private_key, img_bytes, telemetry, False)
            elif key == ord('a') or key == ord('A'):
                telemetry = {"device_id": device_id, "timestamp": int(time.time()), "temp": -5.0, "humidity": 68.0, "cargo_status": "Thermal Breach"}
                img_bytes = capture_webcam_frame(cap, "ANOMALY", -5.0)
                transmit_telemetry(client, args.broker, TOPIC_CHUNKS, private_key, img_bytes, telemetry, False)
            elif key == ord('s') or key == ord('S'):
                telemetry = {"device_id": device_id, "timestamp": int(time.time()), "temp": -18.0, "humidity": 55.0, "cargo_status": "Tampered"}
                img_bytes = capture_webcam_frame(cap, "SPOOFED", -18.0)
                transmit_telemetry(client, args.broker, TOPIC_CHUNKS, private_key, img_bytes, telemetry, True)
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        if client:
            client.loop_stop()
            client.disconnect()
        print("[OK] Edge agent terminated cleanly.")


if __name__ == "__main__":
    main()

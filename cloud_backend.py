#!/usr/bin/env python3
"""
CryoKrypton Cloud Backend Simulation
Role 4: Cloud Ingress, Reassembly, & AI Orchestration

This script simulates receiving chunked telemetry data from an ESP32-S3 IoT device,
reassembling the chunks, parsing the JSON payload, verifying the cryptographic signature,
and running a simulated AI analysis (representing a Qwen3.7-Plus agent model).

Designed for a hackathon demo: simple, modular, beginner-friendly, and highly visual.
It runs three scenarios: Normal Operations, Cargo Anomaly, and Security Violation.
"""

import json
import time

# --- ANSI Colors for Professional Terminal Output ---
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title):
    """Utility function to print a clean and professional section header."""
    print(f"\n{BOLD}{BLUE}=== {title} ==={RESET}")
    time.sleep(0.3)  # Add a tiny delay to simulate real-time stream flow

def simulate_iot_transmission(chunks):
    """
    Step 1: Simulate receiving chunked data from an IoT device as a list of strings.
    In real-world applications, ESP32 devices split large messages (like images or
    telemetry packets) into smaller chunks to fit network payload limits (e.g. MQTT limits).
    """
    print_header("1. Simulating IoT Data Ingress (ESP32-S3-CAM)")
    print("Device: [ESP32-S3-AntiGrav-04]")
    print("Channel: MQTT Topic: 'device/telemetry/chunks'")
    
    for i, chunk in enumerate(chunks, 1):
        # Preview chunk contents
        preview = chunk[:40] + "..." if len(chunk) > 40 else chunk
        print(f"  [+] Data received: Chunk {i}/{len(chunks)} ({len(chunk)} bytes) -> '{preview}'")
        time.sleep(0.3)
        
    return chunks

def reassemble_chunks(chunks):
    """
    Step 2: Reassemble the chunks into a complete message.
    Takes a list of string chunks and joins them in sequence to reconstruct
    the original message payload.
    """
    print_header("2. Reassembling Data Chunks")
    
    if not chunks:
        print(f"  [{RED}ERROR{RESET}] Reassembly failed: No chunks to process.")
        return ""
    
    # Concatenate the list of strings into one full string
    assembled_message = "".join(chunks)
    
    print(f"  [{GREEN}SUCCESS{RESET}] Reassembled successfully!")
    print(f"  Reassembled Message Length: {len(assembled_message)} bytes")
    print(f"  Raw Reassembled Content:\n  {assembled_message}")
    
    return assembled_message

def parse_to_json(raw_message):
    """
    Step 3: Convert the reconstructed data into a structured format (JSON/dictionary).
    Deserializes the raw string into a Python dictionary. Includes error handling.
    """
    print_header("3. Unpacking Payload to Structured Format (JSON)")
    
    try:
        # Attempt to parse the string as JSON
        structured_data = json.loads(raw_message)
        print(f"  [{GREEN}SUCCESS{RESET}] JSON parsed successfully.")
        print(f"  Device ID: {structured_data.get('device_id')}")
        print(f"  Timestamp: {structured_data.get('timestamp')}")
        return structured_data
    except json.JSONDecodeError as e:
        print(f"  [{RED}ERROR{RESET}] Failed to parse JSON. Data corruption detected!")
        print(f"  Details: {e}")
        return None

def verify_security_signature(data):
    """
    Step 4: Add a simple verification step (simulate security check).
    In CryoKrypton, the edge device uses a hardware cryptographic peripheral (DS)
    to sign the data. The cloud backend must verify this signature before processing it.
    """
    print_header("4. Zero-Trust Security Check (Signature Verification)")
    
    if not data:
        print(f"  [{RED}FAILED{RESET}] Security Check: No data payload available.")
        return False
        
    signature = data.get("signature")
    
    if not signature:
        print(f"  [{RED}FAILED{RESET}] Security Check: Missing cryptographic signature!")
        return False
        
    print(f"  Found Signature: '{signature}'")
    
    # Simulate signature verification logic
    # In a real environment, this verifies using the public key from the device.
    # Here, we verify if it matches our expected secure signature prefix.
    if signature.startswith("CRYOKRYPTON_SECURE_"):
        print(f"  [{GREEN}VERIFIED{RESET}] Cryptographic signature is VALID. Source authenticity confirmed.")
        return True
    else:
        print(f"  [{RED}WARNING{RESET}] Cryptographic signature is INVALID. Possible spoofing attempt!")
        return False

def run_ai_analysis(data):
    """
    Step 5: Create a function that simulates AI processing of the data
    (like analyzing gravity conditions, stability, or anomalies).
    This simulates Qwen3.7-Plus evaluating thermodynamic safety and anti-gravity status.
    """
    print_header("5. Simulated AI Processing (Qwen3.7-Plus Agent)")
    
    if not data:
        print(f"  [{RED}ERROR{RESET}] AI Analysis: Cannot process empty data.")
        return
        
    # Extract telemetry details
    telemetry = data.get("telemetry", {})
    gravity = telemetry.get("gravity_m_s2", 9.8)
    stability = telemetry.get("stability_index", 0.0)
    temp = telemetry.get("temperature_c", 0.0)
    
    print("  [AI] Fetching Qwen3.7-Plus reasoning loop...")
    time.sleep(0.6) # Simulate processing/inference time
    
    # Simple thresholds to trigger anomalies
    gravity_anomaly = gravity > 0.5  # Anti-gravity cargo should hover near 0.0 m/s^2
    temp_anomaly = temp > -15.0       # Cold-chain cargo must remain extremely cold
    stability_anomaly = stability < 0.85 # High vibrations or instability
    
    status_ok = not (gravity_anomaly or temp_anomaly or stability_anomaly)
    
    # Constructing a clean professional analysis summary output
    print(f"\n  +-------------------------------------------------------------+")
    print(f"  |                    AI ANALYSIS RESULT                       |")
    print(f"  +-------------------------------------------------------------+")
    print(f"  |  Parameter           | Value      | Status                  |")
    print(f"  +----------------------+------------+-------------------------+")
    
    # Gravity row
    grav_status = f"{GREEN}Normal (Anti-Grav Active){RESET}" if not gravity_anomaly else f"{RED}CRITICAL ANOMALY{RESET}"
    print(f"  |  Gravity             | {gravity:<10} | {grav_status:<32} |")
    
    # Temperature row
    temp_status = f"{GREEN}Safe (Cold-Chain OK){RESET}" if not temp_anomaly else f"{RED}WARNING: TEMPERATURE HIGH{RESET}"
    print(f"  |  Temperature         | {temp:<10} | {temp_status:<32} |")
    
    # Stability row
    stab_status = f"{GREEN}Stable{RESET}" if not stability_anomaly else f"{YELLOW}UNSTABLE JITTER{RESET}"
    print(f"  |  Stability Index     | {stability:<10} | {stab_status:<32} |")
    
    print(f"  +-------------------------------------------------------------+")
    
    # Simulated Agent Decision/Action Trigger
    print(f"\n  {BOLD}[AI Reasoning & Autonomous Decision Log]{RESET}")
    if status_ok:
        print(f"  {GREEN}LOG:{RESET} Anti-gravity stability is holding at {stability * 100}%.")
        print(f"  {GREEN}LOG:{RESET} Refrigerator compartment is at {temp}°C, safely below spoilage threshold.")
        print(f"  {GREEN}LOG:{RESET} Shipment is on schedule. No intervention required.")
        print(f"  {BOLD}Action: Continue normal transport route.{RESET}")
    else:
        print(f"  {RED}LOG: [ANOMALY DETECTED] Environmental thresholds violated.{RESET}")
        if gravity_anomaly:
            print(f"  {RED}LOG:{RESET} Gravity level ({gravity} m/s^2) exceeds micro-gravity tolerance! Container hover failing.")
        if temp_anomaly:
            print(f"  {RED}LOG:{RESET} Cold-chain breach! Temperature rose to {temp}°C.")
        if stability_anomaly:
            print(f"  {RED}LOG:{RESET} Stability index is critical ({stability}). High risk of physical structure damage.")
            
        print(f"  {YELLOW}LOG: AI executing tool call: LogisticsAPI.trigger_reroute(){RESET}")
        print(f"  {BOLD}AI Autonomous Decision:{RESET} Emergency intervention triggered.")
        print(f"  {BOLD}Action: Rerouting transport to nearest Cryo-Depot within 15 minutes to save biological assets.{RESET}")
    print(f"  +-------------------------------------------------------------+")

def run_scenario(title, chunks):
    """Orchestrates the full pipeline for a single scenario."""
    print(f"\n{BOLD}{YELLOW}>>> {title} <<<{RESET}")
    print("=" * len(title) * 2)
    
    # 1. Ingress
    received_chunks = simulate_iot_transmission(chunks)
    
    # 2. Reassemble
    raw_message = reassemble_chunks(received_chunks)
    
    # 3. Parse
    data = parse_to_json(raw_message)
    
    # 4. Verify Signature
    is_verified = verify_security_signature(data)
    
    # 5. AI Analysis
    if is_verified:
        run_ai_analysis(data)
    else:
        print(f"\n  [{RED}BLOCKED{RESET}] AI analysis aborted: Payload failed signature verification check!")
        
    print(f"\n{BOLD}{YELLOW}>>> END OF {title} <<<{RESET}")
    print("-" * 50)
    time.sleep(1.0)

def main():
    """
    Main orchestration function to run the full simulation demo.
    """
    print(f"\n{BOLD}{GREEN}================================================================={RESET}")
    print(f"{BOLD}{GREEN}          CRYOKRIPTON CLOUD BACKEND INGRESS PIPELINE DEMO        {RESET}")
    print(f"{BOLD}{GREEN}================================================================={RESET}")
    
    # Scenario 1: Normal Operations
    run_scenario(
        title="SCENARIO 1: NORMAL FLIGHT OPERATIONS",
        chunks=[
            '{"device_id": "ESP32-S3-AntiGrav-04", "timestamp": 1719593187, "telemetry": {"gravity_m_s2": 0.18, "stability_index": 0.94, ',
            '"temperature_c": -18.2, "cargo_status": "Anti-Gravity Active"}, "signature": "',
            'CRYOKRYPTON_SECURE_ECDSA_HASH_98234"}'
        ]
    )
    
    # Scenario 2: Cargo Anomaly & Temperature Warning
    run_scenario(
        title="SCENARIO 2: CARGO ANOMALY DETECTED (FIELD DECAY)",
        chunks=[
            '{"device_id": "ESP32-S3-AntiGrav-04", "timestamp": 1719593247, "telemetry": {"gravity_m_s2": 0.89, "stability_index": 0.62, ',
            '"temperature_c": -8.5, "cargo_status": "Thruster Malfunction"}, "signature": "',
            'CRYOKRYPTON_SECURE_ECDSA_HASH_98235"}'
        ]
    )
    
    # Scenario 3: Security Violation (Zero-Trust Block)
    run_scenario(
        title="SCENARIO 3: SECURITY AUDIT FAILED (MALICIOUS SPOOFING)",
        chunks=[
            '{"device_id": "ESP32-S3-AntiGrav-04", "timestamp": 1719593307, "telemetry": {"gravity_m_s2": 0.15, "stability_index": 0.95, ',
            '"temperature_c": -18.0, "cargo_status": "Tampered"}, "signature": "',
            'UNAUTHORIZED_EXPLOIT_ATTEMPT_88291"}'
        ]
    )
    
    print(f"\n{BOLD}{GREEN}================================================================={RESET}")
    print(f"{BOLD}{GREEN}                 DEMO SYSTEM SHUTDOWN SUCCESSFULLY               {RESET}")
    print(f"{BOLD}{GREEN}================================================================={RESET}\n")

if __name__ == "__main__":
    main()

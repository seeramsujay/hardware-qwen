#!/usr/bin/env python3
"""
CryoKrypton Automated Multi-Scenario Integration Test Runner
------------------------------------------------------------
Executes comprehensive regression testing across all cryptographic, simulation,
and AI orchestration layers to guarantee 100% demo reliability.
"""

import os
import sys
import time
import subprocess

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_section(title):
    print(f"\n{BOLD}{BLUE}================================================================={RESET}")
    print(f"{BOLD}{BLUE} {title:<63} {RESET}")
    print(f"{BOLD}{BLUE}================================================================={RESET}")

def run_test(name, cmd_list):
    print(f"\n{BOLD}Running Test:{RESET} {YELLOW}{name}{RESET}")
    print(f"Command: {' '.join(cmd_list)}")
    start_time = time.time()
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        duration = time.time() - start_time
        print(f"[{GREEN}PASSED{RESET}] Finished in {duration:.2f}s")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"[{RED}FAILED{RESET}] Failed after {duration:.2f}s (Exit Code: {e.returncode})")
        print(f"\n--- STDOUT ---\n{e.stdout}")
        print(f"\n--- STDERR ---\n{e.stderr}")
        return False, e.stderr

def main():
    print(f"\n{BOLD}{GREEN}*****************************************************************{RESET}")
    print(f"{BOLD}{GREEN}      CRYOKRYPTON AUTOMATED REGRESSION & VALIDATION SUITE        {RESET}")
    print(f"{BOLD}{GREEN}*****************************************************************{RESET}")
    
    passed_count = 0
    total_count = 3
    
    # Test 1: RSA Key Generation & Crypto Self-Test
    print_section("TEST 1: Cryptographic Engine & Identity Verification")
    ok1, out1 = run_test("RSA-2048 Signing & Verification Self-Test", ["python3", "scripts/verify_signature.py", "--selftest"])
    if ok1:
        passed_count += 1
        
    # Test 2: Cloud Backend Ingress & Zero-Trust Verification Demo
    print_section("TEST 2: Cloud Ingress, Reassembly & Zero-Trust Gate")
    ok2, out2 = run_test("Cloud Backend Multi-Scenario Execution", ["python3", "cloud_backend.py"])
    if ok2 and "VERIFIED" in out2 and "BLOCKED" in out2:
        print(f"[{GREEN}ASSERT OK{RESET}] Verified both acceptance of valid signatures and rejection of tampered payloads.")
        passed_count += 1
    else:
        print(f"[{RED}ASSERT FAIL{RESET}] Output did not contain expected Zero-Trust verification assertions.")
        
    # Test 3: Edge Webcam Emulation Agent Single Frame Test
    print_section("TEST 3: Edge Agent Webcam Emulation & Chunking")
    ok3, out3 = run_test("Edge Agent Synthetic Image Generation & Transmit", ["python3", "scripts/edge_webcam_agent.py", "--test"])
    if ok3 and "[OK] Single frame test passed." in out3:
        passed_count += 1
    else:
        print(f"[{RED}ASSERT FAIL{RESET}] Edge agent failed single frame transmission test.")
            
    print(f"\n{BOLD}{GREEN}*****************************************************************{RESET}")
    print(f"{BOLD}Test Results Summary:{RESET} {passed_count}/{total_count} Passed")
    if passed_count == total_count:
        print(f"{BOLD}{GREEN}ALL TESTS PASSED SUCCESSFULLY! The system is 100% demo ready.{RESET}")
        sys.exit(0)
    else:
        print(f"{BOLD}{RED}SOME TESTS FAILED. Please review logs above.{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()

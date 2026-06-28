#!/usr/bin/env python3
import sys
import subprocess
import os

def check_pip_package(package_name):
    try:
        __import__(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False

def install_package(package_name):
    print(f"Installing {package_name}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("=== CryoKrypton RSA Key Wrapping Utility (Role 2) ===")
    
    # 1. Check for esp-secure-cert-tool
    tool_name = "esp-secure-cert-tool"
    if not check_pip_package(tool_name):
        print(f"'{tool_name}' is not installed.")
        success = install_package(tool_name)
        if not success:
            print("Failed to install esp-secure-cert-tool. Please run: pip install esp-secure-cert-tool")
            sys.exit(1)
            
    print("esp-secure-cert-tool is ready.")
    
    # 2. Check for keys
    private_key = "keys/private_key.pem"
    if not os.path.exists(private_key):
        print(f"Error: Private key not found at '{private_key}'.")
        print("Please run 'generate_keys.py' first to create the keypair.")
        sys.exit(1)
        
    print("\nHow to provision the ESP32-S3 Digital Signature (DS) key:")
    print("=========================================================")
    print("The DS peripheral requires that the private key be encrypted (wrapped)")
    # We explain the manual steps the user should take
    print("with an HMAC key burned into eFuse BLOCK_KEY0. esp-secure-cert-tool handles this:")
    print("\n1. To configure the device and generate the secure cert partition image:")
    print("   Run the following command (substitute your ESP32-S3 serial port, e.g. /dev/ttyUSB0):")
    print("   python3 -m esp_secure_cert.configure_esp_secure_cert --port /dev/ttyUSB0 \\")
    print("       --private-key keys/private_key.pem \\")
    print("       --key-purpose HMAC_DS \\")
    print("       --secure-cert-type ds \\")
    print("       --priv-key-len 2048")
    
    print("\n2. What this command does:")
    print("   a. Generates a random 256-bit HMAC key (or uses one provided).")
    print("   b. Calculates the RSA parameters (Modulus, Exponent, Montgomery parameters R and M').")
    print("   c. Encrypts (wraps) the RSA private key parameters with the HMAC key.")
    print("   d. Burns the HMAC key to eFuse BLOCK_KEY0 (making it read-protected).")
    print("   e. Creates a 'secure_cert.bin' partition image and flashes it to the device.")
    print("\n3. If you want to perform this process step-by-step offline (without a connected device):")
    print("   python3 -m esp_secure_cert.make_secure_cert_image --private-key keys/private_key.pem \\")
    print("       --secure-cert-type ds \\")
    print("       --priv-key-len 2048 \\")
    print("       --hmac-key-file keys/hmac_key.bin \\")
    print("       --output-file keys/secure_cert_partition.bin")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    print("=== CryoKrypton RSA Key Generation Tool ===")
    
    # Check if openssl is installed
    try:
        subprocess.run(["openssl", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: 'openssl' command-line tool is not found. Please install openssl.")
        sys.exit(1)
        
    os.makedirs("keys", exist_ok=True)
    
    private_key_path = "keys/private_key.pem"
    public_key_path = "keys/public_key.pem"
    
    # 1. Generate RSA Private Key (2048-bit)
    print("Generating 2048-bit RSA private key...")
    subprocess.run([
        "openssl", "genpkey", 
        "-algorithm", "RSA", 
        "-out", private_key_path, 
        "-pkeyopt", "rsa_keygen_bits:2048"
    ], check=True)
    
    # 2. Extract Public Key in PEM format
    print("Extracting public key...")
    subprocess.run([
        "openssl", "rsa", 
        "-pubout", 
        "-in", private_key_path, 
        "-out", public_key_path
    ], check=True)
    
    print("\nKeys generated successfully!")
    print(f"  Private Key: {os.path.abspath(private_key_path)}")
    print(f"  Public Key:  {os.path.abspath(public_key_path)}")
    print("\nNote: For the ESP32-S3 DS peripheral, the private key will need to be wrapped.")
    print("Use the 'wrap_key.py' script to generate the wrapped payload.")

if __name__ == "__main__":
    main()

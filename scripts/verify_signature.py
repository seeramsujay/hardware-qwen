#!/usr/bin/env python3
import sys
import os

def check_dependencies():
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        return True
    except ImportError:
        print("Installing 'cryptography' library required for signature verification...")
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "cryptography"], check=True)
            return True
        except Exception as e:
            print(f"Failed to automatically install cryptography: {e}")
            print("Please run: pip install cryptography")
            return False

def main():
    if not check_dependencies():
        sys.exit(1)
        
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    print("=== CryoKrypton RSA Signature Verification Utility (Role 2) ===")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        run_self_test()
        sys.exit(0)

    if len(sys.argv) < 4:
        print("\nUsage:")
        print("  python3 verify_signature.py <public_key_pem> <data_file_or_hash_hex> <signature_file>")
        print("\nOr to run a self-test with generated keys:")
        print("  python3 verify_signature.py --selftest")
        sys.exit(1)

    pub_key_path = sys.argv[1]
    data_path = sys.argv[2]
    sig_path = sys.argv[3]

    if not os.path.exists(pub_key_path):
        print(f"Error: Public key file not found at {pub_key_path}")
        sys.exit(1)
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        sys.exit(1)
    if not os.path.exists(sig_path):
        print(f"Error: Signature file not found at {sig_path}")
        sys.exit(1)

    # 1. Load Public Key
    with open(pub_key_path, "rb") as f:
        pub_key_data = f.read()
    try:
        public_key = load_pem_public_key(pub_key_data)
    except Exception as e:
        print(f"Error parsing public key: {e}")
        sys.exit(1)

    # 2. Load Data/Digest
    with open(data_path, "rb") as f:
        data_bytes = f.read()

    # Determine if input is a raw 32-byte hash or files
    is_hash = False
    if len(data_bytes) == 32:
        is_hash = True
        print("Detected 32-byte raw binary input (treating as SHA-256 digest).")
    elif len(data_bytes) == 64:
        try:
            # Check if it is a hex representation of a 32-byte hash
            hex_str = data_bytes.decode('utf-8').strip()
            if len(hex_str) == 64:
                data_bytes = bytes.fromhex(hex_str)
                is_hash = True
                print("Detected 64-character hex input. Unpacked to 32-byte digest.")
        except Exception:
            pass

    # 3. Load Signature
    with open(sig_path, "rb") as f:
        signature = f.read()
        
    if len(signature) != 256:
        print(f"Warning: RSA-2048 signature must be exactly 256 bytes. Found: {len(signature)} bytes.")

    # 4. Verify
    try:
        if is_hash:
            # Verify raw pre-computed hash
            public_key.verify(
                signature,
                data_bytes,
                padding.PKCS1v15(),
                utils_Prehashed(hashes.SHA256())
            )
        else:
            # Hash data and verify
            public_key.verify(
                signature,
                data_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        print("\n✅ SIGNATURE VERIFICATION SUCCESSFUL!")
        print("The signature is cryptographically valid and matches the key and telemetry data.")
    except Exception as e:
        print(f"\n❌ SIGNATURE VERIFICATION FAILED: {e}")
        sys.exit(1)

# Helper wrapper for prehashed inputs
class utils_Prehashed:
    def __init__(self, algorithm):
        self._algorithm = algorithm
    @property
    def digest_size(self):
        return self._algorithm.digest_size

def run_self_test():
    print("Running Self Test...")
    private_key_path = "keys/private_key.pem"
    public_key_path = "keys/public_key.pem"
    
    if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
        print("Generating test keys first...")
        import subprocess
        subprocess.run([sys.executable, "scripts/generate_keys.py"], check=True)

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

    # 1. Load keys
    with open(private_key_path, "rb") as f:
        priv_key = load_pem_private_key(f.read(), password=None)
    with open(public_key_path, "rb") as f:
        pub_key = load_pem_public_key(f.read())

    # 2. Create message and sign
    message = b"CryoKrypton Test Telemetry payload content"
    signature = priv_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    # 3. Verify signature
    try:
        pub_key.verify(
            signature,
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        print("Self-test SUCCESS: Key generation, signing, and verification are working locally.")
    except Exception as e:
        print(f"Self-test FAILED: {e}")

if __name__ == "__main__":
    main()

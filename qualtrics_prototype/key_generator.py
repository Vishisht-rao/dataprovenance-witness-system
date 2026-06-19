from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def main():
    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key()

    sk_bytes = sk.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pk_bytes = pk.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    with open("witness_sk.ed25519", "wb") as f:
        f.write(sk_bytes)
    print("Wrote secret key to witness_sk.ed25519")

    with open("witness_pk.ed25519", "wb") as f:
        f.write(pk_bytes)    
    print("Wrote public key to witness_pk.ed25519")

if __name__ == "__main__":
    main()

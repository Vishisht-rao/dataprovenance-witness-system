'''
This contains functions to hash, sign, and verify.
'''

import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def load_sk(path="witness_sk.ed25519") -> Ed25519PrivateKey:
    with open(path, "rb") as f:
        raw = f.read()
    return Ed25519PrivateKey.from_private_bytes(raw)

def load_pk(path="witness_pk.ed25519") -> Ed25519PublicKey:
    with open(path, "rb") as f:
        raw = f.read()
    return Ed25519PublicKey.from_public_bytes(raw)

def sign_hexhash(sk: Ed25519PrivateKey, hexhash: str) -> str:
    sig = sk.sign(bytes.fromhex(hexhash))
    return sig.hex()

def verify_hexhash(pk: Ed25519PublicKey, hexhash: str, sig_hex: str) -> bool:
    try:
        pk.verify(bytes.fromhex(sig_hex), bytes.fromhex(hexhash))
        return True
    except Exception:
        return False
    
def sign_data(sk, data: bytes):
    h = sha256_bytes(data)
    sig_hex = sign_hexhash(sk, h)
    return h, sig_hex

def verify_data(pk, data: bytes, sig_hex: str) -> bool:
    h = sha256_bytes(data)
    return verify_hexhash(pk, h, sig_hex)

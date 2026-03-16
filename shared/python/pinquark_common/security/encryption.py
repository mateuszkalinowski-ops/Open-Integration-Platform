"""AES-256-GCM encryption for credentials and tokens stored in the database."""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key(key_b64: str) -> bytes:
    try:
        key = base64.urlsafe_b64decode(key_b64)
    except Exception:
        key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("Encryption key must be exactly 32 bytes (256 bits)")
    return key


def encrypt_value(plaintext: str, key_b64: str) -> str:
    """Encrypt a plaintext string using AES-256-GCM.

    Returns urlsafe-base64-encoded nonce+ciphertext.
    """
    key = _get_key(key_b64)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_value(encrypted_b64: str, key_b64: str) -> str:
    """Decrypt a urlsafe-base64-encoded AES-256-GCM encrypted value.

    Expects the format: urlsafe_base64(nonce[12] + ciphertext).
    Accepts both standard and urlsafe base64 for backward compatibility.
    """
    key = _get_key(key_b64)
    try:
        raw = base64.urlsafe_b64decode(encrypted_b64)
    except Exception:
        raw = base64.b64decode(encrypted_b64)
    nonce = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")

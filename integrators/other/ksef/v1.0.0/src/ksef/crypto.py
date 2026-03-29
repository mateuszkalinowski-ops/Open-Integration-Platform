"""KSeF cryptographic operations — AES-256-CBC encryption and RSA-OAEP key wrapping.

KSeF 2.0 requires:
- Invoice encryption: AES-256-CBC with PKCS#7 padding
- Key wrapping: RSA-OAEP with SHA-256 and MGF1
- Token encryption (for ksef-token auth): RSA-OAEP with SHA-256
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os

from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_der_x509_certificate

logger = logging.getLogger(__name__)

AES_KEY_SIZE = 32  # 256 bits
AES_BLOCK_SIZE = 16  # 128 bits (CBC)


def generate_aes_key() -> bytes:
    """Generate a random AES-256 key."""
    return os.urandom(AES_KEY_SIZE)


def generate_iv() -> bytes:
    """Generate a random initialization vector for AES-CBC."""
    return os.urandom(AES_BLOCK_SIZE)


def encrypt_aes_cbc(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    """Encrypt data using AES-256-CBC with PKCS#7 padding."""
    padder = padding.PKCS7(AES_BLOCK_SIZE * 8).padder()
    padded = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def decrypt_aes_cbc(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt data using AES-256-CBC and remove PKCS#7 padding."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(AES_BLOCK_SIZE * 8).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def encrypt_invoice(invoice_xml: bytes, key: bytes) -> tuple[bytes, bytes]:
    """Encrypt an invoice XML using AES-256-CBC.

    Returns (iv + ciphertext, iv) — the IV is prepended to the ciphertext
    as required by KSeF.
    """
    iv = generate_iv()
    ciphertext = encrypt_aes_cbc(invoice_xml, key, iv)
    return iv + ciphertext, iv


def wrap_key_rsa_oaep(aes_key: bytes, public_key: RSAPublicKey) -> bytes:
    """Encrypt (wrap) an AES key using RSA-OAEP with SHA-256/MGF1."""
    return public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def encrypt_token_rsa_oaep(token_payload: str, public_key: RSAPublicKey) -> bytes:
    """Encrypt a KSeF token string (token|timestamp) using RSA-OAEP SHA-256.

    Used for ksef-token authentication method.
    """
    return public_key.encrypt(
        token_payload.encode("utf-8"),
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash and return as hex string."""
    return hashlib.sha256(data).hexdigest()


def sha256_base64(data: bytes) -> str:
    """Compute SHA-256 hash and return as base64 string."""
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


def parse_public_key_from_der_b64(certificate_b64: str) -> RSAPublicKey:
    """Parse RSA public key from a base64-encoded DER certificate."""
    cert_bytes = base64.b64decode(certificate_b64)
    cert = load_der_x509_certificate(cert_bytes)
    public_key = cert.public_key()
    if not isinstance(public_key, RSAPublicKey):
        raise ValueError("Certificate does not contain an RSA public key")
    return public_key


def parse_public_key_from_pem(pem_data: str) -> RSAPublicKey:
    """Parse RSA public key from PEM-encoded certificate or key."""
    pem_bytes = pem_data.encode("utf-8")
    try:
        from cryptography.x509 import load_pem_x509_certificate

        cert = load_pem_x509_certificate(pem_bytes)
        public_key = cert.public_key()
    except (ValueError, TypeError):
        public_key = serialization.load_pem_public_key(pem_bytes)

    if not isinstance(public_key, RSAPublicKey):
        raise ValueError("Data does not contain an RSA public key")
    return public_key

"""Tests for KSeF cryptographic operations."""

import base64
import os

from src.ksef.crypto import (
    decrypt_aes_cbc,
    encrypt_aes_cbc,
    encrypt_invoice,
    generate_aes_key,
    generate_iv,
    sha256_base64,
    sha256_hash,
)


class TestAESKeyGeneration:
    def test_generate_aes_key_length(self) -> None:
        key = generate_aes_key()
        assert len(key) == 32  # AES-256

    def test_generate_aes_key_randomness(self) -> None:
        key1 = generate_aes_key()
        key2 = generate_aes_key()
        assert key1 != key2

    def test_generate_iv_length(self) -> None:
        iv = generate_iv()
        assert len(iv) == 16  # AES block size


class TestAESEncryption:
    def test_encrypt_decrypt_roundtrip(self) -> None:
        key = generate_aes_key()
        iv = generate_iv()
        plaintext = b"Test invoice XML content"

        ciphertext = encrypt_aes_cbc(plaintext, key, iv)
        decrypted = decrypt_aes_cbc(ciphertext, key, iv)

        assert decrypted == plaintext

    def test_encrypt_decrypt_large_data(self) -> None:
        key = generate_aes_key()
        iv = generate_iv()
        plaintext = os.urandom(10000)

        ciphertext = encrypt_aes_cbc(plaintext, key, iv)
        decrypted = decrypt_aes_cbc(ciphertext, key, iv)

        assert decrypted == plaintext

    def test_ciphertext_differs_from_plaintext(self) -> None:
        key = generate_aes_key()
        iv = generate_iv()
        plaintext = b"Some sensitive data"

        ciphertext = encrypt_aes_cbc(plaintext, key, iv)
        assert ciphertext != plaintext

    def test_ciphertext_length_is_block_aligned(self) -> None:
        key = generate_aes_key()
        iv = generate_iv()
        plaintext = b"Hello"  # 5 bytes

        ciphertext = encrypt_aes_cbc(plaintext, key, iv)
        assert len(ciphertext) % 16 == 0

    def test_different_keys_produce_different_ciphertext(self) -> None:
        key1 = generate_aes_key()
        key2 = generate_aes_key()
        iv = generate_iv()
        plaintext = b"Same message"

        ct1 = encrypt_aes_cbc(plaintext, key1, iv)
        ct2 = encrypt_aes_cbc(plaintext, key2, iv)
        assert ct1 != ct2


class TestEncryptInvoice:
    def test_encrypt_invoice_returns_iv_prepended(self) -> None:
        key = generate_aes_key()
        invoice = b'<?xml version="1.0"?><Faktura/>'

        encrypted, iv = encrypt_invoice(invoice, key)

        assert encrypted[:16] == iv
        assert len(encrypted) > 16

    def test_encrypt_invoice_can_be_decrypted(self) -> None:
        key = generate_aes_key()
        invoice = b'<?xml version="1.0"?><Faktura><Naglowek/></Faktura>'

        encrypted, iv = encrypt_invoice(invoice, key)

        ciphertext = encrypted[16:]
        decrypted = decrypt_aes_cbc(ciphertext, key, iv)
        assert decrypted == invoice


class TestHashing:
    def test_sha256_hash_consistency(self) -> None:
        data = b"test data"
        hash1 = sha256_hash(data)
        hash2 = sha256_hash(data)
        assert hash1 == hash2

    def test_sha256_hash_format(self) -> None:
        h = sha256_hash(b"test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_sha256_base64_format(self) -> None:
        b64 = sha256_base64(b"test")
        decoded = base64.b64decode(b64)
        assert len(decoded) == 32

    def test_different_data_produces_different_hash(self) -> None:
        h1 = sha256_hash(b"data1")
        h2 = sha256_hash(b"data2")
        assert h1 != h2

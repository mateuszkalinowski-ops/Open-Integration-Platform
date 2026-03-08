"""Credential decryption — mirrors platform/core/credential_vault.py."""

import base64
import logging
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import Credential

logger = logging.getLogger(__name__)

_NONCE_SIZE = 12


class CredentialVault:
    def __init__(self) -> None:
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY must be set")
        raw_key = base64.urlsafe_b64decode(settings.encryption_key.encode())
        if len(raw_key) != 32:
            raise ValueError("ENCRYPTION_KEY must be a base64-encoded 32-byte key")
        self._aesgcm = AESGCM(raw_key)

    def _decrypt(self, ciphertext: str) -> str:
        raw = base64.urlsafe_b64decode(ciphertext.encode())
        nonce = raw[:_NONCE_SIZE]
        ct = raw[_NONCE_SIZE:]
        return self._aesgcm.decrypt(nonce, ct, None).decode()

    async def retrieve_all(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
    ) -> dict[str, str]:
        result = await db.execute(
            select(Credential).where(
                Credential.tenant_id == tenant_id,
                Credential.connector_name == connector_name,
                Credential.credential_name == credential_name,
            )
        )
        creds = result.scalars().all()
        decrypted: dict[str, str] = {}
        for c in creds:
            try:
                decrypted[c.credential_key] = self._decrypt(c.encrypted_value)
            except Exception as exc:
                logger.warning("Failed to decrypt credential for %s: %s", connector_name, type(exc).__name__)
        return decrypted

    async def list_credential_names(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
    ) -> list[str]:
        result = await db.execute(
            select(Credential.credential_name)
            .where(
                Credential.tenant_id == tenant_id,
                Credential.connector_name == connector_name,
            )
            .distinct()
        )
        return list(result.scalars().all())

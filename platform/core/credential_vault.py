"""Credential Vault -- encrypted credential storage per tenant.

Uses AES-256-GCM (authenticated encryption). Each credential value is
encrypted before storing in the database and decrypted only in memory.

Storage format: base64(nonce_12bytes || ciphertext || tag_16bytes)
"""

import base64
import os
import secrets
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import Credential, CredentialToken

_NONCE_SIZE = 12
_TOKEN_PREFIX = "ctok_"


def _generate_credential_token() -> str:
    return f"{_TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


class CredentialVault:
    def __init__(self) -> None:
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY must be set")
        raw_key = base64.urlsafe_b64decode(settings.encryption_key.encode())
        if len(raw_key) != 32:
            raise ValueError("ENCRYPTION_KEY must be a base64-encoded 32-byte key for AES-256-GCM")
        self._aesgcm = AESGCM(raw_key)

    def _encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(_NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def _decrypt(self, ciphertext: str) -> str:
        try:
            raw = base64.urlsafe_b64decode(ciphertext.encode())
            nonce = raw[:_NONCE_SIZE]
            ct = raw[_NONCE_SIZE:]
            return self._aesgcm.decrypt(nonce, ct, None).decode()
        except Exception as exc:
            raise ValueError("Failed to decrypt credential — key mismatch or corrupted data") from exc

    async def store(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_key: str,
        credential_value: str,
        credential_name: str = "default",
    ) -> Credential:
        encrypted = self._encrypt(credential_value)

        existing = await db.execute(
            select(Credential).where(
                Credential.tenant_id == tenant_id,
                Credential.connector_name == connector_name,
                Credential.credential_name == credential_name,
                Credential.credential_key == credential_key,
            )
        )
        cred = existing.scalar_one_or_none()

        if cred:
            cred.encrypted_value = encrypted
        else:
            cred = Credential(
                tenant_id=tenant_id,
                connector_name=connector_name,
                credential_name=credential_name,
                credential_key=credential_key,
                encrypted_value=encrypted,
            )
            db.add(cred)

        await db.flush()
        return cred

    async def retrieve(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_key: str,
        credential_name: str = "default",
    ) -> str | None:
        result = await db.execute(
            select(Credential).where(
                Credential.tenant_id == tenant_id,
                Credential.connector_name == connector_name,
                Credential.credential_name == credential_name,
                Credential.credential_key == credential_key,
            )
        )
        cred = result.scalar_one_or_none()
        if cred is None:
            return None
        return self._decrypt(cred.encrypted_value)

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
        return {c.credential_key: self._decrypt(c.encrypted_value) for c in creds}

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
            .order_by(Credential.credential_name)
        )
        return list(result.scalars().all())

    async def delete(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_key: str | None = None,
        credential_name: str | None = None,
    ) -> int:
        query = select(Credential).where(
            Credential.tenant_id == tenant_id,
            Credential.connector_name == connector_name,
        )
        if credential_name:
            query = query.where(Credential.credential_name == credential_name)
        if credential_key:
            query = query.where(Credential.credential_key == credential_key)

        result = await db.execute(query)
        creds = result.scalars().all()
        for c in creds:
            await db.delete(c)
        await db.flush()
        return len(creds)

    async def get_or_create_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
    ) -> CredentialToken:
        result = await db.execute(
            select(CredentialToken).where(
                CredentialToken.tenant_id == tenant_id,
                CredentialToken.connector_name == connector_name,
                CredentialToken.credential_name == credential_name,
            )
        )
        token_row = result.scalar_one_or_none()
        if token_row:
            return token_row

        token_row = CredentialToken(
            tenant_id=tenant_id,
            connector_name=connector_name,
            credential_name=credential_name,
            token=_generate_credential_token(),
        )
        db.add(token_row)
        await db.flush()
        return token_row

    async def regenerate_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
    ) -> CredentialToken:
        result = await db.execute(
            select(CredentialToken).where(
                CredentialToken.tenant_id == tenant_id,
                CredentialToken.connector_name == connector_name,
                CredentialToken.credential_name == credential_name,
            )
        )
        token_row = result.scalar_one_or_none()
        if token_row:
            token_row.token = _generate_credential_token()
            await db.flush()
            return token_row
        return await self.get_or_create_token(db, tenant_id, connector_name, credential_name)

    async def resolve_token(
        self,
        db: AsyncSession,
        token: str,
    ) -> dict[str, str] | None:
        """Resolve an opaque credential token to the actual credentials."""
        result = await db.execute(
            select(CredentialToken).where(
                CredentialToken.token == token,
                CredentialToken.is_active.is_(True),
            )
        )
        token_row = result.scalar_one_or_none()
        if not token_row:
            return None
        return await self.retrieve_all(
            db, token_row.tenant_id, token_row.connector_name,
            credential_name=token_row.credential_name,
        )

    async def get_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
    ) -> str | None:
        result = await db.execute(
            select(CredentialToken.token).where(
                CredentialToken.tenant_id == tenant_id,
                CredentialToken.connector_name == connector_name,
                CredentialToken.credential_name == credential_name,
            )
        )
        return result.scalar_one_or_none()

    async def delete_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str | None = None,
    ) -> int:
        query = select(CredentialToken).where(
            CredentialToken.tenant_id == tenant_id,
            CredentialToken.connector_name == connector_name,
        )
        if credential_name:
            query = query.where(CredentialToken.credential_name == credential_name)
        result = await db.execute(query)
        tokens = result.scalars().all()
        for t in tokens:
            await db.delete(t)
        await db.flush()
        return len(tokens)

    async def rename_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        old_credential_name: str,
        new_credential_name: str,
    ) -> None:
        result = await db.execute(
            select(CredentialToken).where(
                CredentialToken.tenant_id == tenant_id,
                CredentialToken.connector_name == connector_name,
                CredentialToken.credential_name == old_credential_name,
            )
        )
        token_row = result.scalar_one_or_none()
        if token_row:
            token_row.credential_name = new_credential_name
            await db.flush()

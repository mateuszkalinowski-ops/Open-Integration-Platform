"""OAuth2 lifecycle manager — token storage, exchange, and retrieval.

Handles the full OAuth2 authorization code flow: generates authorization URLs,
exchanges codes for tokens, stores encrypted tokens in the database, and
provides token retrieval with automatic refresh awareness.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from string import Formatter

import httpx
import structlog
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.credential_vault import CredentialVault
from db.models import OAuthToken

logger = structlog.get_logger(__name__)

_PKCE_REDIS_PREFIX = "oauth2:pkce:"
_STATE_REDIS_PREFIX = "oauth2:state:"
_PKCE_TTL = 600  # 10 minutes — authorization flow should complete within this
_STATE_TTL = 600


class OAuth2Manager:
    """Manages OAuth2 token lifecycle for connector integrations."""

    def __init__(self, vault: CredentialVault, redis_getter: Any = None) -> None:
        self._vault = vault
        self._redis_getter = redis_getter

    async def generate_authorization_url(
        self,
        oauth2_config: dict[str, Any],
        tenant_id: uuid.UUID,
        connector_name: str,
        callback_url: str,
        credential_name: str = "default",
    ) -> dict[str, str]:
        """Build the provider authorization URL with PKCE if configured."""
        resolved_config = self.resolve_oauth2_config(oauth2_config)
        authorization_url = resolved_config["authorization_url"]
        client_id = resolved_config.get("client_id", "")
        scopes = resolved_config.get("scopes", [])

        if not self._redis_getter:
            raise RuntimeError("OAuth2 state storage requires Redis to be configured")

        state = f"{tenant_id}:{connector_name}:{credential_name}:{secrets.token_urlsafe(32)}"

        params: dict[str, str] = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": callback_url,
            "state": state,
        }
        if scopes:
            params["scope"] = " ".join(scopes)

        if resolved_config.get("pkce"):
            import hashlib
            import base64

            code_verifier = secrets.token_urlsafe(64)
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).rstrip(b"=").decode()
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

            redis = await self._redis_getter()
            await redis.set(f"{_PKCE_REDIS_PREFIX}{state}", code_verifier, ex=_PKCE_TTL)

        redis = await self._redis_getter()
        await redis.set(f"{_STATE_REDIS_PREFIX}{state}", "1", ex=_STATE_TTL)

        url = f"{authorization_url}?{urlencode(params)}"
        return {"url": url, "state": state}

    async def validate_and_consume_state(self, state: str) -> bool:
        """Verify that *state* was issued by generate_authorization_url and consume it (one-time use).

        Returns ``True`` if the state was valid.
        """
        if not self._redis_getter:
            raise RuntimeError("OAuth2 state validation requires Redis to be configured")
        redis = await self._redis_getter()
        key = f"{_STATE_REDIS_PREFIX}{state}"
        val = await redis.get(key)
        if val:
            await redis.delete(key)
            return True
        return False

    async def retrieve_code_verifier(self, state: str) -> str | None:
        """Retrieve and delete a PKCE code_verifier stored during authorization."""
        if not self._redis_getter:
            return None
        redis = await self._redis_getter()
        key = f"{_PKCE_REDIS_PREFIX}{state}"
        verifier = await redis.get(key)
        if verifier:
            await redis.delete(key)
        return verifier

    async def exchange_code(
        self,
        db: AsyncSession,
        oauth2_config: dict[str, Any],
        tenant_id: uuid.UUID,
        connector_name: str,
        code: str,
        callback_url: str,
        credential_name: str = "default",
        code_verifier: str | None = None,
    ) -> OAuthToken:
        """Exchange an authorization code for access/refresh tokens."""
        resolved_config = self.resolve_oauth2_config(oauth2_config)
        token_url = resolved_config["token_url"]
        client_id = resolved_config.get("client_id", "")
        client_secret = resolved_config.get("client_secret", "")

        body: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": callback_url,
            "client_id": client_id,
        }
        if client_secret:
            body["client_secret"] = client_secret
        if code_verifier:
            body["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.post(token_url, data=body)
            resp.raise_for_status()
            token_data = resp.json()

        return await self._store_token(
            db, tenant_id, connector_name, credential_name, connector_name, token_data,
        )

    async def refresh_token(
        self,
        db: AsyncSession,
        oauth_token: OAuthToken,
        oauth2_config: dict[str, Any],
    ) -> OAuthToken:
        """Refresh an existing OAuth2 token using the refresh_token grant."""
        refresh_token = self._vault._decrypt(oauth_token.refresh_token_encrypted or "")
        if not refresh_token:
            oauth_token.status = "error"
            oauth_token.last_error = "No refresh token available"
            await db.flush()
            raise ValueError("No refresh token available for refresh")

        resolved_config = self.resolve_oauth2_config(oauth2_config)
        token_url = resolved_config["token_url"]
        client_id = resolved_config.get("client_id", "")
        client_secret = resolved_config.get("client_secret", "")

        body: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }
        if client_secret:
            body["client_secret"] = client_secret

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.post(token_url, data=body)

        if resp.status_code >= 400:
            oauth_token.status = "error"
            oauth_token.last_error = f"Refresh failed: HTTP {resp.status_code}"
            await db.flush()
            logger.warning(
                "oauth2_refresh_failed",
                connector=oauth_token.connector_name,
                tenant_id=str(oauth_token.tenant_id),
                status=resp.status_code,
            )
            raise httpx.HTTPStatusError(
                f"Token refresh failed with {resp.status_code}",
                request=resp.request,
                response=resp,
            )

        token_data = resp.json()
        return await self._update_token(db, oauth_token, token_data)

    async def get_valid_access_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
    ) -> str | None:
        """Retrieve a valid, non-expired access token, or ``None``."""
        token = await self._get_token(db, tenant_id, connector_name, credential_name)
        if token is None:
            return None
        if token.status not in ("active",):
            return None
        if token.expires_at is not None and token.expires_at <= datetime.now(timezone.utc):
            return None
        return self._vault._decrypt(token.access_token_encrypted)

    async def get_or_refresh_access_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
        oauth2_config: dict[str, Any] | None = None,
    ) -> str | None:
        """Return a valid access token, attempting an inline refresh if expired.

        When *oauth2_config* is provided and the token has a refresh_token,
        an expired-but-active token is refreshed synchronously so the caller
        always gets a usable bearer token (or ``None`` if refresh fails).
        """
        token = await self._get_token(db, tenant_id, connector_name, credential_name)
        if token is None:
            return None
        if token.status not in ("active",):
            return None

        now = datetime.now(timezone.utc)
        expired = token.expires_at is not None and token.expires_at <= now
        if not expired:
            return self._vault._decrypt(token.access_token_encrypted)

        if oauth2_config and token.refresh_token_encrypted:
            try:
                refreshed = await self.refresh_token(db, token, oauth2_config)
                return self._vault._decrypt(refreshed.access_token_encrypted)
            except Exception:
                logger.warning(
                    "oauth2_inline_refresh_failed",
                    connector=connector_name,
                    tenant_id=str(tenant_id),
                )
                token.status = "expired"
                await db.flush()
                return None

        token.status = "expired"
        await db.flush()
        return None

    async def get_tokens_expiring_soon(
        self,
        db: AsyncSession,
        within_seconds: int = 300,
    ) -> list[OAuthToken]:
        """Return all active tokens expiring within the given window."""
        cutoff = datetime.now(timezone.utc) + timedelta(seconds=within_seconds)
        result = await db.execute(
            select(OAuthToken).where(
                and_(
                    OAuthToken.status == "active",
                    OAuthToken.expires_at.isnot(None),
                    OAuthToken.expires_at <= cutoff,
                    OAuthToken.refresh_token_encrypted.isnot(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_token_status(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
    ) -> dict[str, Any]:
        """Return token status summary for API responses."""
        token = await self._get_token(db, tenant_id, connector_name, credential_name)
        if token is None:
            return {"has_token": False, "status": "none"}

        now = datetime.now(timezone.utc)
        expires_in = None
        if token.expires_at:
            expires_in = max(0, int((token.expires_at - now).total_seconds()))

        return {
            "has_token": True,
            "status": token.status,
            "provider": token.provider,
            "scope": token.scope,
            "expires_in_seconds": expires_in,
            "last_refreshed_at": token.last_refreshed_at.isoformat() if token.last_refreshed_at else None,
            "refresh_count": token.refresh_count,
            "last_error": token.last_error,
        }

    async def revoke_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str = "default",
    ) -> bool:
        """Mark a token as revoked."""
        token = await self._get_token(db, tenant_id, connector_name, credential_name)
        if token is None:
            return False
        token.status = "revoked"
        await db.flush()
        logger.info("oauth2_token_revoked", connector=connector_name, tenant_id=str(tenant_id))
        return True

    @staticmethod
    def resolve_oauth2_config(oauth2_config: dict[str, Any]) -> dict[str, Any]:
        """Resolve templated OAuth2 config values using the config itself as context."""
        context = {
            key: value
            for key, value in oauth2_config.items()
            if isinstance(value, (str, int, float, bool))
        }
        formatter = Formatter()

        def _resolve(value: Any) -> Any:
            if isinstance(value, str):
                fields = [name for _, name, _, _ in formatter.parse(value) if name]
                if not fields:
                    return value
                missing = [field for field in fields if field not in context]
                if missing:
                    raise ValueError(f"Missing OAuth2 config values for: {', '.join(sorted(missing))}")
                return value.format_map(context)
            if isinstance(value, dict):
                return {k: _resolve(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_resolve(item) for item in value]
            return value

        resolved = {key: _resolve(val) for key, val in oauth2_config.items()}
        for key, value in resolved.items():
            if isinstance(value, (str, int, float, bool)):
                context[key] = value
        return resolved

    async def _get_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str,
    ) -> OAuthToken | None:
        result = await db.execute(
            select(OAuthToken).where(
                OAuthToken.tenant_id == tenant_id,
                OAuthToken.connector_name == connector_name,
                OAuthToken.credential_name == credential_name,
            ).order_by(OAuthToken.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _store_token(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        credential_name: str,
        provider: str,
        token_data: dict[str, Any],
    ) -> OAuthToken:
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        now = datetime.now(timezone.utc)

        expires_at = None
        if expires_in:
            expires_at = now + timedelta(seconds=int(expires_in))

        token = OAuthToken(
            tenant_id=tenant_id,
            connector_name=connector_name,
            credential_name=credential_name,
            provider=provider,
            access_token_encrypted=self._vault._encrypt(access_token),
            refresh_token_encrypted=self._vault._encrypt(refresh_token) if refresh_token else None,
            token_type=token_data.get("token_type", "bearer"),
            scope=token_data.get("scope"),
            expires_at=expires_at,
            status="active",
        )
        db.add(token)
        await db.flush()

        await self._vault.store(db, tenant_id, connector_name, "access_token", access_token, credential_name)
        if refresh_token:
            await self._vault.store(db, tenant_id, connector_name, "refresh_token", refresh_token, credential_name)

        logger.info(
            "oauth2_token_stored",
            connector=connector_name,
            tenant_id=str(tenant_id),
            expires_in=expires_in,
        )
        return token

    async def _update_token(
        self,
        db: AsyncSession,
        oauth_token: OAuthToken,
        token_data: dict[str, Any],
    ) -> OAuthToken:
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        now = datetime.now(timezone.utc)

        oauth_token.access_token_encrypted = self._vault._encrypt(access_token)
        if refresh_token:
            oauth_token.refresh_token_encrypted = self._vault._encrypt(refresh_token)
        if expires_in:
            oauth_token.expires_at = now + timedelta(seconds=int(expires_in))
        oauth_token.last_refreshed_at = now
        oauth_token.refresh_count += 1
        oauth_token.status = "active"
        oauth_token.last_error = None

        await self._vault.store(
            db, oauth_token.tenant_id, oauth_token.connector_name,
            "access_token", access_token, oauth_token.credential_name,
        )
        if refresh_token:
            await self._vault.store(
                db, oauth_token.tenant_id, oauth_token.connector_name,
                "refresh_token", refresh_token, oauth_token.credential_name,
            )

        await db.flush()
        logger.info(
            "oauth2_token_refreshed",
            connector=oauth_token.connector_name,
            tenant_id=str(oauth_token.tenant_id),
            refresh_count=oauth_token.refresh_count,
        )
        return oauth_token

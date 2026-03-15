"""Amazon LWA (Login with Amazon) OAuth2 token management.

Handles access token acquisition via refresh_token grant and automatic renewal
before expiry. Thread-safe per-account token caching.
"""

import logging
import time
from typing import Any

import httpx

from src.config import LWA_TOKEN_URL, AmazonAccountConfig

logger = logging.getLogger(__name__)

TOKEN_REFRESH_MARGIN_SECONDS = 60


class AmazonAuthError(Exception):
    def __init__(self, message: str, raw: dict[str, Any] | None = None):
        self.raw = raw or {}
        super().__init__(message)


class TokenManager:
    """Manages LWA access tokens per account with automatic refresh."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client
        self._tokens: dict[str, tuple[str, float]] = {}

    async def get_access_token(self, account: AmazonAccountConfig) -> str:
        cached = self._tokens.get(account.name)
        if cached and cached[1] > time.monotonic():
            return cached[0]

        token_data = await self._refresh_token(account)
        access_token = token_data["access_token"]
        expires_in = int(token_data.get("expires_in", 3600))
        expires_at = time.monotonic() + expires_in - TOKEN_REFRESH_MARGIN_SECONDS
        self._tokens[account.name] = (access_token, expires_at)

        logger.info("Refreshed LWA access token for account=%s, expires_in=%ds", account.name, expires_in)
        return access_token

    async def _refresh_token(self, account: AmazonAccountConfig) -> dict[str, Any]:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": account.refresh_token,
            "client_id": account.client_id,
            "client_secret": account.client_secret,
        }

        response = await self._http.post(LWA_TOKEN_URL, data=payload)

        if response.status_code != 200:
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise AmazonAuthError(
                f"LWA token refresh failed: {response.status_code} — {body.get('error_description', response.text)}",
                raw=body,
            )

        return response.json()

    async def get_grantless_token(
        self,
        account: AmazonAccountConfig,
        scope: str,
    ) -> str:
        """Get a grantless access token for operations like Notifications management."""
        cache_key = f"{account.name}:grantless:{scope}"
        cached = self._tokens.get(cache_key)
        if cached and cached[1] > time.monotonic():
            return cached[0]

        payload = {
            "grant_type": "client_credentials",
            "client_id": account.client_id,
            "client_secret": account.client_secret,
            "scope": scope,
        }

        response = await self._http.post(LWA_TOKEN_URL, data=payload)

        if response.status_code != 200:
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise AmazonAuthError(
                f"LWA grantless token failed: {response.status_code} — {body.get('error_description', response.text)}",
                raw=body,
            )

        data = response.json()
        access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        expires_at = time.monotonic() + expires_in - TOKEN_REFRESH_MARGIN_SECONDS
        self._tokens[cache_key] = (access_token, expires_at)
        return access_token

    def invalidate(self, account_name: str) -> None:
        keys_to_remove = [k for k in self._tokens if k == account_name or k.startswith(f"{account_name}:")]
        for key in keys_to_remove:
            del self._tokens[key]

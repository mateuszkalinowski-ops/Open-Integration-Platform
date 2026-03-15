"""Apilo OAuth2 token management.

Handles access token acquisition via authorization_code and refresh_token grants.
Access tokens are valid for 21 days, refresh tokens for 2 months.
"""

import base64
import contextlib
import logging
import time
from typing import Any

import httpx

from src.config import ApiloAccountConfig

logger = logging.getLogger(__name__)

TOKEN_REFRESH_MARGIN_SECONDS = 3600


class ApiloAuthError(Exception):
    def __init__(self, message: str, raw: dict[str, Any] | None = None):
        self.raw = raw or {}
        super().__init__(message)


class TokenManager:
    """Manages Apilo access tokens per account with automatic refresh."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client
        self._tokens: dict[str, tuple[str, str, float]] = {}

    async def get_access_token(self, account: ApiloAccountConfig) -> str:
        cached = self._tokens.get(account.name)
        if cached and cached[2] > time.monotonic():
            return cached[0]

        if cached:
            refresh_token = cached[1]
        elif account.refresh_token:
            refresh_token = account.refresh_token
        else:
            token_data = await self._exchange_authorization_code(account)
            return self._cache_tokens(account.name, token_data)

        try:
            token_data = await self._refresh_token(account, refresh_token)
        except ApiloAuthError:
            if account.authorization_code:
                logger.warning("Refresh failed for account=%s, trying authorization_code", account.name)
                token_data = await self._exchange_authorization_code(account)
            else:
                raise

        return self._cache_tokens(account.name, token_data)

    def _cache_tokens(self, account_name: str, token_data: dict[str, Any]) -> str:
        access_token = token_data["accessToken"]
        refresh_token = token_data.get("refreshToken", "")
        _expires_at_str = token_data.get("accessTokenExpireAt", "")

        expires_in = 21 * 24 * 3600
        expires_at = time.monotonic() + expires_in - TOKEN_REFRESH_MARGIN_SECONDS

        self._tokens[account_name] = (access_token, refresh_token, expires_at)
        logger.info("Cached Apilo access token for account=%s", account_name)
        return access_token

    def get_cached_refresh_token(self, account_name: str) -> str | None:
        cached = self._tokens.get(account_name)
        return cached[1] if cached else None

    async def _exchange_authorization_code(self, account: ApiloAccountConfig) -> dict[str, Any]:
        return await self._token_request(
            account,
            {
                "grantType": "authorization_code",
                "token": account.authorization_code,
            },
        )

    async def _refresh_token(self, account: ApiloAccountConfig, refresh_token: str) -> dict[str, Any]:
        return await self._token_request(
            account,
            {
                "grantType": "refresh_token",
                "token": refresh_token,
            },
        )

    async def _token_request(self, account: ApiloAccountConfig, payload: dict[str, Any]) -> dict[str, Any]:
        credentials = base64.b64encode(f"{account.client_id}:{account.client_secret}".encode()).decode()

        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = await self._http.post(account.token_url, json=payload, headers=headers)

        if response.status_code not in (200, 201):
            body: dict[str, Any] = {}
            with contextlib.suppress(Exception):
                body = response.json()
            raise ApiloAuthError(
                f"Apilo token request failed: {response.status_code} — {body.get('message', response.text[:200])}",
                raw=body,
            )

        return response.json()

    def invalidate(self, account_name: str) -> None:
        self._tokens.pop(account_name, None)

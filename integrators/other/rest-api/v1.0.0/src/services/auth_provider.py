"""Authentication provider — generates HTTP headers per auth strategy."""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

import httpx

from src.schemas.account import AccountConfig, AuthType

logger = logging.getLogger(__name__)


class AuthProviderError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AuthProvider:
    """Resolves authentication headers for an account."""

    def __init__(self, account: AccountConfig) -> None:
        self._account = account
        self._oauth2_token: str = ""
        self._oauth2_expires_at: float = 0.0
        self._http_client: httpx.AsyncClient | None = None

    async def get_headers(self) -> dict[str, str]:
        auth = self._account.auth
        headers: dict[str, str] = {}

        match auth.type:
            case AuthType.NONE:
                pass
            case AuthType.BEARER:
                headers["Authorization"] = f"Bearer {auth.bearer_token}"
            case AuthType.BEARER_WITH_CUSTOM_HEADERS:
                headers["Authorization"] = f"Bearer {auth.bearer_token}"
                headers.update(auth.custom_headers)
            case AuthType.BASIC:
                encoded = base64.b64encode(f"{auth.username}:{auth.password}".encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
            case AuthType.API_KEY_HEADER:
                headers[auth.api_key_header_name] = auth.api_key
            case AuthType.API_KEY_QUERY:
                pass
            case AuthType.OAUTH2_CLIENT_CREDENTIALS:
                token = await self._get_oauth2_token()
                headers["Authorization"] = f"Bearer {token}"

        return headers

    def get_query_params(self) -> dict[str, str]:
        """Return auth-related query params (API key in query mode)."""
        auth = self._account.auth
        if auth.type == AuthType.API_KEY_QUERY:
            return {auth.api_key_param_name: auth.api_key}
        return {}

    async def _get_oauth2_token(self) -> str:
        if self._oauth2_token and time.time() < self._oauth2_expires_at - 30:
            return self._oauth2_token

        auth = self._account.auth
        if not auth.token_url:
            raise AuthProviderError("OAuth2 token_url not configured")

        client = await self._get_http_client()
        try:
            data: dict[str, str] = {
                "grant_type": "client_credentials",
                "client_id": auth.client_id,
                "client_secret": auth.client_secret,
            }
            if auth.scope:
                data["scope"] = auth.scope

            response = await client.post(auth.token_url, data=data)
            response.raise_for_status()
            token_data = response.json()

            self._oauth2_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._oauth2_expires_at = time.time() + expires_in

            logger.info(
                "OAuth2 token refreshed for account '%s', expires in %ds",
                self._account.name,
                expires_in,
            )
            return self._oauth2_token

        except httpx.HTTPStatusError as exc:
            raise AuthProviderError(
                f"OAuth2 token request failed: {exc.response.status_code}",
                details={"response": exc.response.text[:500]},
            ) from exc
        except httpx.RequestError as exc:
            raise AuthProviderError(
                f"OAuth2 token request connection error: {exc}",
            ) from exc

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0),
            )
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

"""OAuth2 token management for connectors that use OAuth2 authentication."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class TokenData(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: float | None = None
    scope: str | None = None
    raw: dict[str, Any] | None = None


class OAuth2Manager:
    """Manages OAuth2 authorization code flow with token storage and refresh.

    Tokens are stored in memory by default. Provide ``on_token_save`` and
    ``on_token_load`` callbacks for persistent storage.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob",
        scopes: list[str] | None = None,
        on_token_save: Any | None = None,
        on_token_load: Any | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scopes = scopes or []
        self._on_token_save = on_token_save
        self._on_token_load = on_token_load
        self._tokens: dict[str, TokenData] = {}

    def get_authorization_url(self, state: str | None = None) -> str:
        params: dict[str, str] = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }
        if self.scopes:
            params["scope"] = " ".join(self.scopes)
        if state:
            params["state"] = state
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, account: str = "default") -> TokenData:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

        token_data = self._parse_token_response(response.json())
        await self._store_token(account, token_data)
        logger.info("oauth2_code_exchanged", account=account)
        return token_data

    async def refresh_token(self, account: str = "default") -> TokenData:
        current = await self.get_token(account)
        if current is None or current.refresh_token is None:
            raise ValueError(f"No refresh token available for account '{account}'")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": current.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

        token_data = self._parse_token_response(response.json())
        if token_data.refresh_token is None:
            token_data = TokenData(
                access_token=token_data.access_token,
                refresh_token=current.refresh_token,
                token_type=token_data.token_type,
                expires_at=token_data.expires_at,
                scope=token_data.scope,
                raw=token_data.raw,
            )

        await self._store_token(account, token_data)
        logger.info("oauth2_token_refreshed", account=account)
        return token_data

    async def get_token(self, account: str = "default") -> TokenData | None:
        if account in self._tokens:
            return self._tokens[account]

        if self._on_token_load is not None:
            loaded = await self._on_token_load(account)
            if loaded is not None:
                self._tokens[account] = loaded
                return loaded

        return None

    async def get_valid_token(self, account: str = "default") -> str:
        """Return a valid access token, refreshing if expired."""
        token = await self.get_token(account)
        if token is None:
            raise ValueError(f"No token stored for account '{account}'")

        if token.expires_at is not None and time.time() >= token.expires_at - 60:
            token = await self.refresh_token(account)

        return token.access_token

    async def _store_token(self, account: str, token: TokenData) -> None:
        self._tokens[account] = token
        if self._on_token_save is not None:
            await self._on_token_save(account, token)

    @staticmethod
    def _parse_token_response(data: dict[str, Any]) -> TokenData:
        expires_at: float | None = None
        if "expires_in" in data:
            expires_at = time.time() + int(data["expires_in"])
        elif "expires_at" in data:
            expires_at = float(data["expires_at"])

        return TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope"),
            raw=data,
        )

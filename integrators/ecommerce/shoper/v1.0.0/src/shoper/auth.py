"""Shoper OAuth2 authentication via Basic Auth token exchange.

Shoper uses a simplified OAuth2 flow:
1. POST to /webapi/rest/auth with Basic Auth header (login:password)
2. Receive access_token + expires_in
3. Use Bearer token for subsequent requests
4. Re-authenticate when token expires
"""

import base64
import logging
from datetime import datetime, timezone, timedelta

import httpx

from src.config import settings
from src.shoper.schemas import AuthStatusResponse, ShoperAuthResponse

logger = logging.getLogger(__name__)


class ShoperAuthManager:
    """Manages OAuth2 tokens for multiple Shoper accounts."""

    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}
        self._expiry: dict[str, datetime] = {}

    def is_authenticated(self, account_name: str) -> bool:
        return account_name in self._tokens and not self._is_expired(account_name)

    def _is_expired(self, account_name: str) -> bool:
        expiry = self._expiry.get(account_name)
        if not expiry:
            return True
        return datetime.now(timezone.utc) >= expiry

    async def get_access_token(
        self,
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
    ) -> str:
        if self.is_authenticated(account_name):
            return self._tokens[account_name]

        return await self.authenticate(account_name, shop_url, login, password)

    async def authenticate(
        self,
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
    ) -> str:
        """Authenticate with Shoper API using Basic Auth and store the bearer token."""
        url = f"{shop_url.rstrip('/')}/webapi/rest/auth"
        credentials = base64.b64encode(f"{login}:{password}".encode("ascii")).decode("ascii")

        async with httpx.AsyncClient(timeout=settings.http_connect_timeout) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Basic {credentials}"},
            )
            response.raise_for_status()

        auth_data = ShoperAuthResponse.model_validate(response.json())
        bearer_token = f"Bearer {auth_data.access_token}"
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=auth_data.expires_in - 60)

        self._tokens[account_name] = bearer_token
        self._expiry[account_name] = expires_at

        logger.info(
            "Authenticated account=%s, token expires at %s",
            account_name,
            expires_at.isoformat(),
        )
        return bearer_token

    def invalidate(self, account_name: str) -> None:
        self._tokens.pop(account_name, None)
        self._expiry.pop(account_name, None)

    def get_status(self, account_name: str) -> AuthStatusResponse:
        return AuthStatusResponse(
            account_name=account_name,
            authenticated=self.is_authenticated(account_name),
            token_expires_at=self._expiry.get(account_name),
        )

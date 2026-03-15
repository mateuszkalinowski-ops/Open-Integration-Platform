"""Allegro OAuth2 Device Flow authentication and token management.

Implements the full OAuth lifecycle:
1. Device code request → user authorizes in browser
2. Poll for access token
3. Token refresh when expired
4. Encrypted token persistence in database
"""

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

import httpx

from src.allegro.schemas import (
    AllegroDeviceCodeResponse,
    AllegroTokenResponse,
    AuthStatusResponse,
)
from src.config import settings
from src.models.database import TokenStore

logger = logging.getLogger(__name__)

ALLEGRO_ERRORS = {
    "slow_down": "SLOW_DOWN",
    "authorization_pending": "AUTHORIZATION_PENDING",
    "access_denied": "ACCESS_DENIED",
}


class AllegroAuthManager:
    """Manages OAuth2 tokens for multiple Allegro accounts."""

    def __init__(self, token_store: TokenStore):
        self._token_store = token_store
        self._tokens: dict[str, AllegroTokenResponse] = {}
        self._expiry: dict[str, datetime] = {}
        self._pending_auths: dict[str, AllegroDeviceCodeResponse] = {}

    async def initialize(self) -> None:
        """Load existing tokens from database on startup."""
        all_tokens = await self._token_store.load_all_tokens()
        for account_name, token_data in all_tokens.items():
            self._tokens[account_name] = AllegroTokenResponse(**token_data["token"])
            self._expiry[account_name] = datetime.fromisoformat(token_data["expires_at"])
            logger.info("Loaded token for account=%s, expires=%s", account_name, self._expiry[account_name])

    def is_authenticated(self, account_name: str) -> bool:
        return account_name in self._tokens

    def is_token_expired(self, account_name: str) -> bool:
        expiry = self._expiry.get(account_name)
        if not expiry:
            return True
        return datetime.now(UTC) >= expiry.replace(tzinfo=UTC)

    async def get_access_token(
        self,
        account_name: str,
        client_id: str,
        client_secret: str,
        auth_url: str,
    ) -> str:
        """Get a valid access token, refreshing if needed."""
        if self.is_authenticated(account_name) and not self.is_token_expired(account_name):
            return self._tokens[account_name].access_token

        if self.is_authenticated(account_name):
            logger.info("Token expired for account=%s, refreshing", account_name)
            try:
                token = await self.refresh_token(account_name, client_id, client_secret, auth_url)
                return token.access_token
            except Exception:
                logger.exception("Token refresh failed for account=%s", account_name)
                raise

        raise RuntimeError(
            f"Account '{account_name}' not authenticated. "
            f"Call POST /auth/{account_name}/device-code to start device flow."
        )

    async def start_device_flow(
        self,
        account_name: str,
        client_id: str,
        auth_url: str,
    ) -> AllegroDeviceCodeResponse:
        """Step 1: Request a device code from Allegro."""
        url = f"{auth_url}/device"
        async with httpx.AsyncClient(timeout=settings.http_connect_timeout) as client:
            response = await client.post(
                url,
                data={"client_id": client_id},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

        device_code = AllegroDeviceCodeResponse.model_validate(response.json())
        self._pending_auths[account_name] = device_code
        logger.info(
            "Device flow started for account=%s. User code=%s, URI=%s",
            account_name,
            device_code.user_code,
            device_code.verification_uri_complete,
        )
        return device_code

    async def poll_for_token(
        self,
        account_name: str,
        client_id: str,
        client_secret: str,
        auth_url: str,
        max_wait_seconds: int = 300,
    ) -> AllegroTokenResponse:
        """Step 2: Poll Allegro until user authorizes the device code."""
        device_code_resp = self._pending_auths.get(account_name)
        if not device_code_resp:
            raise RuntimeError(f"No pending device flow for account '{account_name}'")

        url = f"{auth_url}/token"
        interval = device_code_resp.interval
        start = time.monotonic()

        async with httpx.AsyncClient(
            timeout=settings.http_connect_timeout,
            auth=(client_id, client_secret),
        ) as client:
            while time.monotonic() - start < max_wait_seconds:
                await asyncio.sleep(interval)
                response = await client.post(
                    url,
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "device_code": device_code_resp.device_code,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    token = AllegroTokenResponse.model_validate(response.json())
                    await self._store_token(account_name, token)
                    self._pending_auths.pop(account_name, None)
                    logger.info("Device flow completed for account=%s", account_name)
                    return token

                error = response.json().get("error", "")
                if error == "slow_down":
                    interval += 1
                elif error == "authorization_pending":
                    continue
                elif error == "access_denied":
                    self._pending_auths.pop(account_name, None)
                    raise PermissionError(f"User denied access for account '{account_name}'")
                else:
                    raise RuntimeError(f"Unexpected auth error: {error} — {response.text}")

        self._pending_auths.pop(account_name, None)
        raise TimeoutError(f"Device flow timed out for account '{account_name}'")

    async def refresh_token(
        self,
        account_name: str,
        client_id: str,
        client_secret: str,
        auth_url: str,
    ) -> AllegroTokenResponse:
        """Refresh an expired access token using the refresh token."""
        current = self._tokens.get(account_name)
        if not current:
            raise RuntimeError(f"No token to refresh for account '{account_name}'")

        url = f"{auth_url}/token"
        async with httpx.AsyncClient(
            timeout=settings.http_connect_timeout,
            auth=(client_id, client_secret),
        ) as client:
            response = await client.post(
                url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": current.refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code == 401:
            self._tokens.pop(account_name, None)
            self._expiry.pop(account_name, None)
            await self._token_store.delete_token(account_name)
            raise PermissionError(
                f"Refresh token invalid for account '{account_name}'. Re-authenticate via device flow."
            )

        response.raise_for_status()
        token = AllegroTokenResponse.model_validate(response.json())
        await self._store_token(account_name, token)
        logger.info("Token refreshed for account=%s", account_name)
        return token

    async def _store_token(self, account_name: str, token: AllegroTokenResponse) -> None:
        expires_at = datetime.now(UTC) + timedelta(seconds=token.expires_in)
        self._tokens[account_name] = token
        self._expiry[account_name] = expires_at
        await self._token_store.save_token(
            account_name,
            {
                "token": token.model_dump(),
                "expires_at": expires_at.isoformat(),
            },
        )

    def get_status(self, account_name: str) -> AuthStatusResponse:
        pending = self._pending_auths.get(account_name)
        return AuthStatusResponse(
            account_name=account_name,
            authenticated=self.is_authenticated(account_name) and not self.is_token_expired(account_name),
            token_expires_at=self._expiry.get(account_name),
            verification_uri=pending.verification_uri_complete if pending else None,
            user_code=pending.user_code if pending else None,
        )

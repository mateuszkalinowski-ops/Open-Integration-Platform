"""KSeF 2.0 authentication flow — challenge → token/XAdES → JWT.

Supports two authentication methods:
1. KSeF Token: encrypted token|timestamp sent as JSON
2. XAdES Signature: signed XML document (requires qualified certificate)

This module implements method 1 (KSeF Token) as the primary approach,
which is suitable for automated server-to-server integration.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from src.ksef.crypto import encrypt_token_rsa_oaep, parse_public_key_from_der_b64
from src.ksef.schemas import (
    AuthChallengeResponse,
    AuthInitResponse,
    AuthStatusResponse,
    AuthTokenRefreshResponse,
    AuthTokensResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class AuthSession:
    """Holds the current authentication state for a KSeF account."""

    access_token: str = ""
    refresh_token: str = ""
    access_valid_until: datetime = field(default_factory=lambda: datetime.min.replace(tzinfo=datetime.UTC))
    refresh_valid_until: datetime = field(default_factory=lambda: datetime.min.replace(tzinfo=datetime.UTC))
    reference_number: str = ""
    nip: str = ""

    @property
    def is_access_valid(self) -> bool:
        if not self.access_token:
            return False
        buffer = 60  # refresh 60s before expiry
        now = datetime.now(tz=datetime.UTC)
        return now.timestamp() < (self.access_valid_until.timestamp() - buffer)

    @property
    def is_refresh_valid(self) -> bool:
        if not self.refresh_token:
            return False
        now = datetime.now(tz=datetime.UTC)
        return now.timestamp() < self.refresh_valid_until.timestamp()

    @property
    def bearer_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }


class KSeFAuthenticator:
    """Handles the full KSeF 2.0 authentication flow using KSeF tokens."""

    def __init__(
        self,
        api_url: str,
        client: httpx.AsyncClient,
        poll_interval: float = 2.0,
        max_poll_attempts: int = 30,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._client = client
        self._poll_interval = poll_interval
        self._max_poll_attempts = max_poll_attempts
        self._public_key_cache: dict[str, tuple[object, str]] = {}

    async def get_public_key(self, usage: str = "KsefTokenEncryption") -> tuple[object, str]:
        """Fetch the KSeF public key certificate for encryption.

        Args:
            usage: Certificate usage type — 'KsefTokenEncryption' for auth,
                   'SymmetricKeyEncryption' for session key wrapping.

        Returns (RSAPublicKey, serial_number).
        """
        cache_key = f"{self._api_url}:{usage}"
        if cache_key in self._public_key_cache:
            return self._public_key_cache[cache_key]

        response = await self._client.get(f"{self._api_url}/security/public-key-certificates")
        response.raise_for_status()
        data = response.json()

        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            raise RuntimeError("No public key certificates returned by KSeF")

        cert_info = None
        for item in items:
            item_usages = item.get("usage", [])
            if usage in item_usages:
                cert_info = item
                break
        if cert_info is None:
            cert_info = items[0]

        cert_b64 = cert_info["certificate"]
        serial = cert_info.get("serialNumber", "")

        public_key = parse_public_key_from_der_b64(cert_b64)
        self._public_key_cache[cache_key] = (public_key, serial)
        logger.info("Fetched KSeF public key (usage=%s, serial=%s)", usage, serial)
        return public_key, serial

    async def get_challenge(self) -> AuthChallengeResponse:
        """Step 1: Get an authentication challenge (valid for 10 minutes)."""
        response = await self._client.post(f"{self._api_url}/auth/challenge")
        response.raise_for_status()
        return AuthChallengeResponse.model_validate(response.json())

    async def authenticate_with_token(
        self,
        nip: str,
        ksef_token: str,
    ) -> AuthSession:
        """Full authentication flow using KSeF token.

        1. Get challenge
        2. Encrypt token|timestamp with KSeF public key
        3. Send auth request
        4. Poll for completion
        5. Redeem access + refresh tokens
        """
        challenge = await self.get_challenge()
        logger.debug("Got challenge (length=%d)", len(challenge.challenge))

        public_key, _ = await self.get_public_key()

        token_payload = f"{ksef_token}|{challenge.timestamp_ms}"
        encrypted = encrypt_token_rsa_oaep(token_payload, public_key)  # type: ignore[arg-type]
        encrypted_b64 = base64.b64encode(encrypted).decode("ascii")

        auth_body = {
            "challenge": challenge.challenge,
            "contextIdentifier": {
                "type": "Nip",
                "value": nip,
            },
            "encryptedToken": encrypted_b64,
        }

        response = await self._client.post(
            f"{self._api_url}/auth/ksef-token",
            json=auth_body,
        )
        response.raise_for_status()
        init_resp = AuthInitResponse.model_validate(response.json())

        logger.info("Auth initiated, ref=%s", init_resp.reference_number)

        auth_token = init_resp.authentication_token.token
        await self._poll_auth_status(init_resp.reference_number, auth_token)

        tokens = await self._redeem_tokens(auth_token)

        session = AuthSession(
            access_token=tokens.access_token.token,
            refresh_token=tokens.refresh_token.token,
            access_valid_until=_parse_datetime(tokens.access_token.valid_until),
            refresh_valid_until=_parse_datetime(tokens.refresh_token.valid_until),
            reference_number=init_resp.reference_number,
            nip=nip,
        )
        logger.info("Authentication successful for NIP=%s***", nip[:6])
        return session

    async def refresh_access_token(self, session: AuthSession) -> AuthSession:
        """Refresh the access token using the refresh token."""
        headers = {"Authorization": f"Bearer {session.refresh_token}"}
        response = await self._client.post(
            f"{self._api_url}/auth/token/refresh",
            headers=headers,
        )
        response.raise_for_status()
        refresh_resp = AuthTokenRefreshResponse.model_validate(response.json())

        session.access_token = refresh_resp.access_token.token
        session.access_valid_until = _parse_datetime(refresh_resp.access_token.valid_until)
        logger.info("Access token refreshed for NIP=%s***", session.nip[:6])
        return session

    async def ensure_valid_session(
        self,
        session: AuthSession,
        nip: str,
        ksef_token: str,
    ) -> AuthSession:
        """Ensure the session has a valid access token, refreshing or re-authenticating as needed."""
        if session.is_access_valid:
            return session

        if session.is_refresh_valid:
            return await self.refresh_access_token(session)

        return await self.authenticate_with_token(nip, ksef_token)

    async def _poll_auth_status(self, reference_number: str, auth_token: str) -> None:
        """Poll authentication status until success or failure."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        for _ in range(self._max_poll_attempts):
            response = await self._client.get(
                f"{self._api_url}/auth/{reference_number}",
                headers=headers,
            )
            response.raise_for_status()
            status_resp = AuthStatusResponse.model_validate(response.json())

            code = status_resp.status.code
            if code == 200:
                logger.info("Auth completed successfully")
                return
            if code >= 400:
                raise RuntimeError(
                    f"KSeF authentication failed: {status_resp.status.description} "
                    f"(code={code}, details={status_resp.status.details})"
                )

            logger.debug("Auth in progress (code=%d), polling again...", code)
            await asyncio.sleep(self._poll_interval)

        raise RuntimeError(f"Authentication timed out after {self._max_poll_attempts} attempts")

    async def _redeem_tokens(self, auth_token: str) -> AuthTokensResponse:
        """Redeem the authentication token for access + refresh tokens (one-time only)."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = await self._client.post(
            f"{self._api_url}/auth/token/redeem",
            headers=headers,
        )
        response.raise_for_status()
        return AuthTokensResponse.model_validate(response.json())


def _parse_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime string with timezone, handling various formats."""
    dt_str = dt_str.strip()
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)

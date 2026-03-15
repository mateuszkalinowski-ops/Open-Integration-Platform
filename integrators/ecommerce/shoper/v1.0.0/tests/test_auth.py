"""Tests for Shoper authentication service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.shoper.auth import ShoperAuthManager


class TestShoperAuthManager:
    def setup_method(self) -> None:
        self.auth = ShoperAuthManager()

    def test_not_authenticated_initially(self) -> None:
        assert not self.auth.is_authenticated("test-account")

    def test_get_status_unauthenticated(self) -> None:
        status = self.auth.get_status("test-account")
        assert status.account_name == "test-account"
        assert not status.authenticated
        assert status.token_expires_at is None

    @pytest.mark.asyncio
    async def test_authenticate_stores_token(self, sample_auth_response: dict) -> None:
        with patch("src.shoper.auth.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_auth_response
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            token = await self.auth.authenticate(
                "test-account",
                "https://test.shoparena.pl",
                "admin",
                "password123",
            )

            assert token.startswith("Bearer ")
            assert self.auth.is_authenticated("test-account")

    @pytest.mark.asyncio
    async def test_get_access_token_returns_cached(self) -> None:
        self.auth._tokens["cached"] = "Bearer cached_token"
        self.auth._expiry["cached"] = datetime.now(UTC) + timedelta(hours=1)

        token = await self.auth.get_access_token(
            "cached",
            "https://test.shoparena.pl",
            "admin",
            "pass",
        )
        assert token == "Bearer cached_token"

    def test_invalidate_removes_token(self) -> None:
        self.auth._tokens["test"] = "Bearer token"
        self.auth._expiry["test"] = datetime.now(UTC) + timedelta(hours=1)

        self.auth.invalidate("test")
        assert not self.auth.is_authenticated("test")

    def test_expired_token_not_authenticated(self) -> None:
        self.auth._tokens["expired"] = "Bearer old_token"
        self.auth._expiry["expired"] = datetime.now(UTC) - timedelta(hours=1)

        assert not self.auth.is_authenticated("expired")

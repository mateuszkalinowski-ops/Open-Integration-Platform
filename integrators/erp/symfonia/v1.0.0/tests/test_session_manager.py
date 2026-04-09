"""Tests for Symfonia WebAPI session management."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.session_manager import SessionManager


@pytest.fixture
def session_manager():
    return SessionManager(
        base_url="http://localhost:8080",
        application_guid="TEST-GUID-1234",
        device_name="test-device",
        session_timeout_minutes=30,
    )


class TestSessionManager:
    def test_initial_state_has_no_valid_session(self, session_manager: SessionManager):
        assert not session_manager.is_session_valid

    @pytest.mark.asyncio
    async def test_open_session_returns_token(self, session_manager: SessionManager):
        mock_response = MagicMock()
        mock_response.text = '"d28b139a-ea62-492e-a97b-4fd22b9f2f76"'
        mock_response.raise_for_status = MagicMock()

        session_manager._client = AsyncMock()
        session_manager._client.get = AsyncMock(return_value=mock_response)

        token = await session_manager.get_session_token()

        assert token == "d28b139a-ea62-492e-a97b-4fd22b9f2f76"
        assert session_manager.is_session_valid
        session_manager._client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_token_returned_when_valid(self, session_manager: SessionManager):
        session_manager._session_token = "cached-token"
        session_manager._session_created_at = time.monotonic()

        token = await session_manager.get_session_token()

        assert token == "cached-token"

    @pytest.mark.asyncio
    async def test_invalidate_forces_renewal(self, session_manager: SessionManager):
        session_manager._session_token = "old-token"
        session_manager._session_created_at = time.monotonic()

        await session_manager.invalidate()

        assert not session_manager.is_session_valid

    def test_session_expires_after_timeout(self, session_manager: SessionManager):
        session_manager._session_token = "expired-token"
        session_manager._session_created_at = time.monotonic() - 1900

        assert not session_manager.is_session_valid

    def test_get_auth_headers_raises_without_session(self, session_manager: SessionManager):
        with pytest.raises(RuntimeError, match="No active session"):
            session_manager.get_auth_headers()

    def test_get_auth_headers_returns_session_header(self, session_manager: SessionManager):
        session_manager._session_token = "test-token"

        headers = session_manager.get_auth_headers()

        assert headers["Authorization"] == "Session test-token"
        assert headers["Content-Type"] == "application/json"

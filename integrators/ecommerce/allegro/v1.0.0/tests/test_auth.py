"""Tests for Allegro OAuth2 authentication manager."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from src.allegro.auth import AllegroAuthManager
from src.allegro.schemas import AllegroTokenResponse


@pytest.fixture
def token_store():
    store = AsyncMock()
    store.load_all_tokens.return_value = {}
    store.load_all_last_event_ids.return_value = {}
    return store


@pytest.fixture
def auth_mgr(token_store):
    return AllegroAuthManager(token_store)


class TestAllegroAuthManager:
    @pytest.mark.asyncio
    async def test_initialize_loads_tokens(self, auth_mgr, token_store):
        token_store.load_all_tokens.return_value = {
            "shop1": {
                "token": {
                    "access_token": "acc123",
                    "refresh_token": "ref456",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            }
        }
        await auth_mgr.initialize()
        assert auth_mgr.is_authenticated("shop1")
        assert not auth_mgr.is_token_expired("shop1")

    @pytest.mark.asyncio
    async def test_not_authenticated_raises_on_get_token(self, auth_mgr):
        await auth_mgr.initialize()
        with pytest.raises(RuntimeError, match="not authenticated"):
            await auth_mgr.get_access_token("unknown", "cid", "cs", "https://auth")

    def test_is_authenticated_false_for_unknown(self, auth_mgr):
        assert not auth_mgr.is_authenticated("nonexistent")

    def test_is_token_expired_true_for_unknown(self, auth_mgr):
        assert auth_mgr.is_token_expired("nonexistent")

    def test_get_status_unauthenticated(self, auth_mgr):
        status = auth_mgr.get_status("shop1")
        assert status.account_name == "shop1"
        assert status.authenticated is False
        assert status.verification_uri is None

    @pytest.mark.asyncio
    async def test_get_access_token_returns_cached(self, auth_mgr, token_store):
        token_store.load_all_tokens.return_value = {
            "shop1": {
                "token": {
                    "access_token": "cached-token",
                    "refresh_token": "ref",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            }
        }
        await auth_mgr.initialize()
        token = await auth_mgr.get_access_token("shop1", "cid", "cs", "https://auth")
        assert token == "cached-token"

    @pytest.mark.asyncio
    async def test_expired_token_triggers_refresh(self, auth_mgr, token_store):
        token_store.load_all_tokens.return_value = {
            "shop1": {
                "token": {
                    "access_token": "old",
                    "refresh_token": "ref",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
                "expires_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            }
        }
        await auth_mgr.initialize()

        new_token = AllegroTokenResponse(
            access_token="new-token",
            refresh_token="new-ref",
            expires_in=3600,
            token_type="Bearer",
        )

        with patch.object(auth_mgr, "refresh_token", return_value=new_token) as mock_refresh:
            token = await auth_mgr.get_access_token("shop1", "cid", "cs", "https://auth")
            assert token == "new-token"
            mock_refresh.assert_called_once()

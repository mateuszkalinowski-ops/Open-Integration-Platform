"""Tests for Amazon LWA authentication module."""

import pytest
import httpx
import respx

from src.amazon.auth import TokenManager, AmazonAuthError
from src.config import AmazonAccountConfig, LWA_TOKEN_URL


@pytest.fixture
def account() -> AmazonAccountConfig:
    return AmazonAccountConfig(
        name="test",
        client_id="amzn1.test-client",
        client_secret="test-secret",
        refresh_token="Atzr|test-refresh-token",
        marketplace_id="A1PA6795UKMFR9",
        region="eu",
    )


@pytest.mark.asyncio
class TestTokenManager:
    @respx.mock
    async def test_get_access_token_success(self, account: AmazonAccountConfig) -> None:
        respx.post(LWA_TOKEN_URL).mock(return_value=httpx.Response(
            200,
            json={
                "access_token": "Atza|test-access-token",
                "token_type": "bearer",
                "expires_in": 3600,
            },
        ))

        async with httpx.AsyncClient() as http:
            manager = TokenManager(http)
            token = await manager.get_access_token(account)
            assert token == "Atza|test-access-token"

    @respx.mock
    async def test_get_access_token_cached(self, account: AmazonAccountConfig) -> None:
        route = respx.post(LWA_TOKEN_URL).mock(return_value=httpx.Response(
            200,
            json={
                "access_token": "Atza|cached-token",
                "token_type": "bearer",
                "expires_in": 3600,
            },
        ))

        async with httpx.AsyncClient() as http:
            manager = TokenManager(http)
            token1 = await manager.get_access_token(account)
            token2 = await manager.get_access_token(account)
            assert token1 == token2
            assert route.call_count == 1

    @respx.mock
    async def test_get_access_token_auth_error(self, account: AmazonAccountConfig) -> None:
        respx.post(LWA_TOKEN_URL).mock(return_value=httpx.Response(
            400,
            json={"error": "invalid_grant", "error_description": "Invalid refresh token"},
        ))

        async with httpx.AsyncClient() as http:
            manager = TokenManager(http)
            with pytest.raises(AmazonAuthError, match="Invalid refresh token"):
                await manager.get_access_token(account)

    @respx.mock
    async def test_invalidate_clears_cache(self, account: AmazonAccountConfig) -> None:
        route = respx.post(LWA_TOKEN_URL).mock(return_value=httpx.Response(
            200,
            json={"access_token": "Atza|fresh", "expires_in": 3600},
        ))

        async with httpx.AsyncClient() as http:
            manager = TokenManager(http)
            await manager.get_access_token(account)
            manager.invalidate("test")
            await manager.get_access_token(account)
            assert route.call_count == 2

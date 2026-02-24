"""Tests for Apilo OAuth2 authentication."""

import pytest
import httpx
import respx

from src.apilo.auth import ApiloAuthError, TokenManager
from src.config import ApiloAccountConfig


@pytest.fixture
def account() -> ApiloAccountConfig:
    return ApiloAccountConfig(
        name="test",
        client_id="test-client-id",
        client_secret="test-client-secret",
        authorization_code="test-auth-code",
        refresh_token="test-refresh-token",
        base_url="https://test.apilo.com",
    )


@pytest.fixture
def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


class TestTokenManager:
    @respx.mock
    @pytest.mark.asyncio
    async def test_exchange_authorization_code(self, account: ApiloAccountConfig) -> None:
        respx.post("https://test.apilo.com/rest/auth/token/").mock(
            return_value=httpx.Response(201, json={
                "accessToken": "new-access-token",
                "accessTokenExpireAt": "2026-03-20T12:00:00Z",
                "refreshToken": "new-refresh-token",
                "refreshTokenExpireAt": "2026-05-20T12:00:00Z",
            })
        )

        async with httpx.AsyncClient() as client:
            manager = TokenManager(client)
            account_no_refresh = ApiloAccountConfig(
                name="test",
                client_id="test-client-id",
                client_secret="test-client-secret",
                authorization_code="test-auth-code",
                base_url="https://test.apilo.com",
            )
            token = await manager.get_access_token(account_no_refresh)

        assert token == "new-access-token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_refresh_token_flow(self, account: ApiloAccountConfig) -> None:
        respx.post("https://test.apilo.com/rest/auth/token/").mock(
            return_value=httpx.Response(201, json={
                "accessToken": "refreshed-access-token",
                "accessTokenExpireAt": "2026-03-20T12:00:00Z",
                "refreshToken": "new-refresh-token",
                "refreshTokenExpireAt": "2026-05-20T12:00:00Z",
            })
        )

        async with httpx.AsyncClient() as client:
            manager = TokenManager(client)
            token = await manager.get_access_token(account)

        assert token == "refreshed-access-token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_cached_token_reuse(self, account: ApiloAccountConfig) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(201, json={
                "accessToken": f"token-{call_count}",
                "accessTokenExpireAt": "2026-03-20T12:00:00Z",
                "refreshToken": "refresh-token",
                "refreshTokenExpireAt": "2026-05-20T12:00:00Z",
            })

        respx.post("https://test.apilo.com/rest/auth/token/").mock(side_effect=handler)

        async with httpx.AsyncClient() as client:
            manager = TokenManager(client)
            token1 = await manager.get_access_token(account)
            token2 = await manager.get_access_token(account)

        assert token1 == token2
        assert call_count == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_auth_error_on_failure(self, account: ApiloAccountConfig) -> None:
        respx.post("https://test.apilo.com/rest/auth/token/").mock(
            return_value=httpx.Response(401, json={"message": "Invalid credentials"})
        )

        async with httpx.AsyncClient() as client:
            manager = TokenManager(client)
            account_no_code = ApiloAccountConfig(
                name="test",
                client_id="bad-id",
                client_secret="bad-secret",
                refresh_token="bad-refresh",
                base_url="https://test.apilo.com",
            )
            with pytest.raises(ApiloAuthError):
                await manager.get_access_token(account_no_code)

    def test_invalidate_clears_cache(self, account: ApiloAccountConfig) -> None:
        async_client = httpx.AsyncClient()
        manager = TokenManager(async_client)
        manager._tokens["test"] = ("token", "refresh", float("inf"))

        manager.invalidate("test")
        assert "test" not in manager._tokens

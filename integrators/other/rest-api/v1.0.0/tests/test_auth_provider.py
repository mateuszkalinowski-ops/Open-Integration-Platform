"""Tests for AuthProvider."""

from __future__ import annotations

import base64

import pytest
from src.schemas.account import AccountConfig, AuthConfig, AuthType
from src.services.auth_provider import AuthProvider


def _make_account(auth: AuthConfig) -> AccountConfig:
    return AccountConfig(name="test", base_url="https://example.com", auth=auth)


@pytest.mark.asyncio
async def test_no_auth():
    provider = AuthProvider(_make_account(AuthConfig(type=AuthType.NONE)))
    headers = await provider.get_headers()
    assert headers == {}
    await provider.close()


@pytest.mark.asyncio
async def test_bearer_auth():
    provider = AuthProvider(_make_account(AuthConfig(type=AuthType.BEARER, bearer_token="my-token")))
    headers = await provider.get_headers()
    assert headers == {"Authorization": "Bearer my-token"}
    await provider.close()


@pytest.mark.asyncio
async def test_bearer_with_custom_headers():
    provider = AuthProvider(
        _make_account(
            AuthConfig(
                type=AuthType.BEARER_WITH_CUSTOM_HEADERS,
                bearer_token="jwt-abc",
                custom_headers={"token-mer": "mer-xyz", "X-Tenant": "clip"},
            )
        )
    )
    headers = await provider.get_headers()
    assert headers["Authorization"] == "Bearer jwt-abc"
    assert headers["token-mer"] == "mer-xyz"
    assert headers["X-Tenant"] == "clip"
    await provider.close()


@pytest.mark.asyncio
async def test_basic_auth():
    provider = AuthProvider(
        _make_account(
            AuthConfig(
                type=AuthType.BASIC,
                username="admin",
                password="secret123",
            )
        )
    )
    headers = await provider.get_headers()
    expected = base64.b64encode(b"admin:secret123").decode()
    assert headers["Authorization"] == f"Basic {expected}"
    await provider.close()


@pytest.mark.asyncio
async def test_api_key_header():
    provider = AuthProvider(
        _make_account(
            AuthConfig(
                type=AuthType.API_KEY_HEADER,
                api_key="key-123",
                api_key_header_name="X-API-Key",
            )
        )
    )
    headers = await provider.get_headers()
    assert headers == {"X-API-Key": "key-123"}
    await provider.close()


@pytest.mark.asyncio
async def test_api_key_query():
    provider = AuthProvider(
        _make_account(
            AuthConfig(
                type=AuthType.API_KEY_QUERY,
                api_key="key-456",
                api_key_param_name="apikey",
            )
        )
    )
    headers = await provider.get_headers()
    assert headers == {}
    params = provider.get_query_params()
    assert params == {"apikey": "key-456"}
    await provider.close()

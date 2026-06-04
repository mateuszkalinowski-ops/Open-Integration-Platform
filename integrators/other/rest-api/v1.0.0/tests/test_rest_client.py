"""Tests for RestClient."""

from __future__ import annotations

import pytest
from src.schemas.account import (
    AccountConfig,
    ActionDefinition,
    AuthConfig,
    AuthType,
    ResponseMappingConfig,
    RetryConfig,
    TimeoutConfig,
)
from src.services.auth_provider import AuthProvider
from src.services.response_parser import ResponseParser
from src.services.rest_client import RestClient, RestClientError


def _make_client(
    base_url: str = "https://example.com",
    path_prefix: str = "",
    action_registry: dict | None = None,
) -> RestClient:
    account = AccountConfig(
        name="test",
        base_url=base_url,
        path_prefix=path_prefix,
        auth=AuthConfig(type=AuthType.NONE),
        response_mapping=ResponseMappingConfig(use_http_status=True),
        retry=RetryConfig(max_attempts=1, backoff_initial_s=0.01),
        timeouts=TimeoutConfig(connect_s=5, read_s=10),
        action_registry={
            k: ActionDefinition(**v) if isinstance(v, dict) else v for k, v in (action_registry or {}).items()
        },
    )
    auth = AuthProvider(account)
    parser = ResponseParser(account)
    return RestClient(account=account, auth_provider=auth, response_parser=parser)


def test_build_url_no_prefix():
    client = _make_client(base_url="https://api.example.com")
    assert client._build_url("users") == "https://api.example.com/users"


def test_build_url_with_prefix():
    client = _make_client(base_url="https://api.example.com", path_prefix="/v2")
    assert client._build_url("users") == "https://api.example.com/v2/users"


def test_build_url_strips_slashes():
    client = _make_client(base_url="https://api.example.com/", path_prefix="/integration/")
    assert client._build_url("/tos_test") == "https://api.example.com/integration/tos_test"


def test_build_url_empty_endpoint():
    client = _make_client(base_url="https://api.example.com", path_prefix="/api")
    assert client._build_url("") == "https://api.example.com/api"


@pytest.mark.asyncio
async def test_call_named_unknown_action():
    client = _make_client()
    with pytest.raises(RestClientError) as exc_info:
        await client.call_named("nonexistent.action")
    assert exc_info.value.status_code == 400
    assert "nonexistent.action" in exc_info.value.message
    await client.close()


@pytest.mark.asyncio
async def test_call_named_resolves_from_registry():
    client = _make_client(
        base_url="https://test.pinquark.app",
        path_prefix="/integration",
        action_registry={
            "awk.create": ActionDefinition(
                endpoint="tos_notification_rail_save",
                method="POST",
            ),
        },
    )
    assert "awk.create" in client.account.action_registry
    action_def = client.account.action_registry["awk.create"]
    assert action_def.endpoint == "tos_notification_rail_save"
    await client.close()

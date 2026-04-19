"""Test fixtures for REST API Gateway connector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.main import create_app
from src.schemas.account import (
    AccountConfig,
    ActionDefinition,
    AuthConfig,
    AuthType,
    ResponseMappingConfig,
    RetryConfig,
    TimeoutConfig,
)
from src.services.account_manager import AccountManager


@pytest.fixture
def pinquark_account() -> AccountConfig:
    return AccountConfig(
        name="test-pinquark",
        description="Test Pinquark TOS account",
        profile="pinquark",
        base_url="https://test.pinquark.app",
        path_prefix="/integration",
        default_method="POST",
        auth=AuthConfig(
            type=AuthType.BEARER_WITH_CUSTOM_HEADERS,
            bearer_token="test-jwt-token",
            custom_headers={"token-mer": "test-mer-token"},
        ),
        timeouts=TimeoutConfig(connect_s=10, read_s=30),
        retry=RetryConfig(max_attempts=2, backoff_initial_s=0.1),
        response_mapping=ResponseMappingConfig(
            status_field="status",
            status_ok_values=["OK"],
            status_error_values=["ERROR"],
            message_field="message",
            data_field="data",
        ),
        action_registry={
            "awk.create": ActionDefinition(
                endpoint="tos_notification_rail_save",
                method="POST",
                description="Create rail notification",
            ),
            "events.poll": ActionDefinition(
                endpoint="tos_get_events_since",
                method="POST",
                description="Poll events",
            ),
        },
    )


@pytest.fixture
def generic_account() -> AccountConfig:
    return AccountConfig(
        name="test-generic",
        description="Test generic REST API",
        profile="generic",
        base_url="https://api.example.com",
        auth=AuthConfig(type=AuthType.BEARER, bearer_token="test-token"),
        response_mapping=ResponseMappingConfig(use_http_status=True),
    )


@pytest.fixture
def account_manager(pinquark_account: AccountConfig, generic_account: AccountConfig) -> AccountManager:
    manager = AccountManager()
    manager._accounts = {
        pinquark_account.name: pinquark_account,
        generic_account.name: generic_account,
    }
    return manager


@pytest.fixture
def test_client(account_manager: AccountManager) -> TestClient:
    app_state.account_manager = account_manager
    app_state.discovery = MagicMock()
    app_state.discovery.discover = AsyncMock()

    app = create_app()
    return TestClient(app)

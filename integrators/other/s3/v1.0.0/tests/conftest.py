"""Shared test fixtures for S3 integrator tests."""

import base64
from datetime import UTC
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import S3AccountConfig
from src.main import create_app
from src.models.database import StateStore
from src.s3_client.integration import S3Integration
from src.s3_client.schemas import ObjectInfo
from src.services.account_manager import AccountManager


@pytest.fixture
def sample_account() -> S3AccountConfig:
    return S3AccountConfig(
        name="test-s3",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        region="eu-central-1",
        default_bucket="test-bucket",
    )


@pytest.fixture
def minio_account() -> S3AccountConfig:
    return S3AccountConfig(
        name="minio-local",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        region="us-east-1",
        endpoint_url="http://localhost:9000",
        use_path_style=True,
        default_bucket="test-bucket",
    )


@pytest.fixture
def account_manager(sample_account: S3AccountConfig) -> AccountManager:
    manager = AccountManager()
    manager.add_account(sample_account)
    return manager


@pytest.fixture
def mock_integration(account_manager: AccountManager) -> S3Integration:
    return S3Integration(account_manager)


@pytest.fixture
def sample_object_info() -> ObjectInfo:
    from datetime import datetime

    return ObjectInfo(
        key="data/report.csv",
        bucket="test-bucket",
        size=1024,
        last_modified=datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC),
        etag="d41d8cd98f00b204e9800998ecf8427e",
        storage_class="STANDARD",
    )


@pytest.fixture
def sample_base64_content() -> str:
    return base64.b64encode(b"Hello, S3 world!").decode("ascii")


@pytest.fixture
def test_client(account_manager: AccountManager):
    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as c:
        mock_state_store = AsyncMock(spec=StateStore)
        mock_integration_obj = AsyncMock(spec=S3Integration)

        app_state.account_manager = account_manager
        app_state.integration = mock_integration_obj
        app_state.state_store = mock_state_store
        app_state.health_checker = None

        yield c

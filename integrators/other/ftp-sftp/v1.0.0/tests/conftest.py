"""Shared test fixtures for FTP/SFTP integrator tests."""

import base64
from datetime import UTC
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import FtpAccountConfig
from src.ftp_client.integration import FtpSftpIntegration
from src.ftp_client.schemas import FileInfo
from src.main import create_app
from src.models.database import StateStore
from src.services.account_manager import AccountManager


@pytest.fixture
def sample_account() -> FtpAccountConfig:
    return FtpAccountConfig(
        name="test-server",
        host="sftp.example.com",
        protocol="sftp",
        port=22,
        username="testuser",
        password="testpass",
        base_path="/data",
    )


@pytest.fixture
def ftp_account() -> FtpAccountConfig:
    return FtpAccountConfig(
        name="ftp-server",
        host="ftp.example.com",
        protocol="ftp",
        port=21,
        username="ftpuser",
        password="ftppass",
        passive_mode=True,
        base_path="/",
    )


@pytest.fixture
def account_manager(sample_account: FtpAccountConfig) -> AccountManager:
    manager = AccountManager()
    manager.add_account(sample_account)
    return manager


@pytest.fixture
def mock_integration(account_manager: AccountManager) -> FtpSftpIntegration:
    return FtpSftpIntegration(account_manager)


@pytest.fixture
def sample_file_info() -> FileInfo:
    from datetime import datetime

    return FileInfo(
        filename="report.csv",
        path="/data/report.csv",
        size=1024,
        is_directory=False,
        modified_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_base64_content() -> str:
    return base64.b64encode(b"Hello, FTP world!").decode("ascii")


@pytest.fixture
def test_client(account_manager: AccountManager) -> TestClient:
    application = create_app()

    mock_state_store = AsyncMock(spec=StateStore)
    mock_integration = AsyncMock(spec=FtpSftpIntegration)

    app_state.account_manager = account_manager
    app_state.integration = mock_integration
    app_state.state_store = mock_state_store
    app_state.health_checker = None

    return TestClient(application)

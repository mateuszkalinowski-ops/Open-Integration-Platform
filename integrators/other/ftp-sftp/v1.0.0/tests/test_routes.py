"""Tests for FastAPI route handlers."""

import base64
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import FtpAccountConfig
from src.ftp_client.schemas import (
    ConnectionTestResponse,
    DirectoryCreateResponse,
    FileDownloadResponse,
    FileInfo,
    FileUploadResponse,
)
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture
def client() -> TestClient:
    application = create_app()

    manager = AccountManager()
    manager.add_account(FtpAccountConfig(name="test-server", host="sftp.example.com"))
    app_state.account_manager = manager

    mock_integration = AsyncMock()
    app_state.integration = mock_integration
    app_state.health_checker = None

    return TestClient(application)


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_endpoint(client: TestClient):
    response = client.get("/readiness")
    assert response.status_code == 200


def test_list_accounts(client: TestClient):
    response = client.get("/accounts")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 1
    assert accounts[0]["name"] == "test-server"


def test_add_account(client: TestClient):
    response = client.post(
        "/accounts",
        json={
            "name": "new-server",
            "host": "ftp.new.com",
            "protocol": "ftp",
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "new-server"


def test_remove_account(client: TestClient):
    app_state.integration.remove_client = lambda n: None
    response = client.delete("/accounts/test-server")
    assert response.status_code == 200


def test_remove_nonexistent_account_returns_404(client: TestClient):
    response = client.delete("/accounts/ghost")
    assert response.status_code == 404


def test_list_files(client: TestClient):
    app_state.integration.list_files.return_value = [
        FileInfo(
            filename="report.csv",
            path="/data/report.csv",
            size=1024,
            modified_at=datetime(2026, 1, 15, tzinfo=UTC),
        ),
    ]
    response = client.get("/files?account_name=test-server&remote_path=/data")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 1
    assert files[0]["filename"] == "report.csv"


def test_list_files_with_pattern(client: TestClient):
    app_state.integration.list_files.return_value = []
    response = client.get("/files?account_name=test-server&remote_path=/&pattern=*.csv")
    assert response.status_code == 200


def test_list_files_unknown_account_returns_404(client: TestClient):
    response = client.get("/files?account_name=unknown&remote_path=/")
    assert response.status_code == 404


def test_upload_file(client: TestClient):
    app_state.integration.upload_file.return_value = FileUploadResponse(
        remote_path="/upload",
        filename="data.csv",
        size=17,
    )
    content = base64.b64encode(b"Hello, FTP world!").decode()
    response = client.post(
        "/files/upload?account_name=test-server",
        json={
            "remote_path": "/upload",
            "filename": "data.csv",
            "content_base64": content,
        },
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "data.csv"


def test_download_file(client: TestClient):
    content_b64 = base64.b64encode(b"file content").decode()
    app_state.integration.download_file.return_value = FileDownloadResponse(
        filename="file.txt",
        remote_path="/data/file.txt",
        content_base64=content_b64,
        size=12,
    )
    response = client.get("/files/download?account_name=test-server&remote_path=/data/file.txt")
    assert response.status_code == 200
    assert response.json()["filename"] == "file.txt"


def test_move_file(client: TestClient):
    app_state.integration.move_file.return_value = {
        "status": "moved",
        "source_path": "/a/file.txt",
        "destination_path": "/b/file.txt",
    }
    response = client.post(
        "/files/move?account_name=test-server",
        json={"source_path": "/a/file.txt", "destination_path": "/b/file.txt"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "moved"


def test_create_directory(client: TestClient):
    app_state.integration.create_directory.return_value = DirectoryCreateResponse(
        remote_path="/new/dir",
    )
    response = client.post(
        "/directories?account_name=test-server",
        json={"remote_path": "/new/dir"},
    )
    assert response.status_code == 200
    assert response.json()["remote_path"] == "/new/dir"


def test_list_directories(client: TestClient):
    app_state.integration.list_files.return_value = [
        FileInfo(filename="subdir", path="/subdir", is_directory=True),
        FileInfo(filename="file.txt", path="/file.txt", is_directory=False),
    ]
    response = client.get("/directories?account_name=test-server&remote_path=/")
    assert response.status_code == 200
    dirs = response.json()
    assert len(dirs) == 1
    assert dirs[0]["filename"] == "subdir"


def test_connection_test(client: TestClient):
    app_state.integration.test_connection.return_value = ConnectionTestResponse(
        status="connected",
        protocol="sftp",
        host="sftp.example.com",
        port=22,
        current_directory="/home/user",
    )
    response = client.post("/auth/test-server/test")
    assert response.status_code == 200
    assert response.json()["status"] == "connected"


def test_connection_test_unknown_account(client: TestClient):
    response = client.post("/auth/unknown/test")
    assert response.status_code == 404

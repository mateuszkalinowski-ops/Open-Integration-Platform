"""Tests for FastAPI route handlers."""

import base64
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import S3AccountConfig
from src.main import create_app
from src.s3_client.schemas import (
    BucketCreateResponse,
    BucketInfo,
    ConnectionTestResponse,
    ObjectCopyResponse,
    ObjectDownloadResponse,
    ObjectInfo,
    ObjectUploadResponse,
    PresignResponse,
)
from src.services.account_manager import AccountManager


@pytest.fixture
def client():
    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as c:
        manager = AccountManager()
        manager.add_account(
            S3AccountConfig(
                name="test-s3",
                aws_access_key_id="AKIAEXAMPLE",
                aws_secret_access_key="secretkey",
                region="eu-central-1",
                default_bucket="test-bucket",
            )
        )
        app_state.account_manager = manager

        mock_integration = AsyncMock()
        app_state.integration = mock_integration
        app_state.health_checker = None

        yield c


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
    assert accounts[0]["name"] == "test-s3"


def test_add_account(client: TestClient):
    response = client.post(
        "/accounts",
        json={
            "name": "new-s3",
            "aws_access_key_id": "AKIANEWKEY",
            "aws_secret_access_key": "newsecret",
            "region": "us-west-2",
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "new-s3"


def test_remove_account(client: TestClient):
    app_state.integration.remove_client = lambda n: None
    response = client.delete("/accounts/test-s3")
    assert response.status_code == 200


def test_remove_nonexistent_account_returns_404(client: TestClient):
    response = client.delete("/accounts/ghost")
    assert response.status_code == 404


def test_list_objects(client: TestClient):
    app_state.integration.list_objects.return_value = [
        ObjectInfo(
            key="data/report.csv",
            bucket="test-bucket",
            size=1024,
            last_modified=datetime(2026, 1, 15, tzinfo=UTC),
            etag="abc123",
        ),
    ]
    response = client.get("/objects?account_name=test-s3&bucket=test-bucket&prefix=data/")
    assert response.status_code == 200
    objects = response.json()
    assert len(objects) == 1
    assert objects[0]["key"] == "data/report.csv"


def test_list_objects_unknown_account_returns_404(client: TestClient):
    response = client.get("/objects?account_name=unknown&bucket=b")
    assert response.status_code == 404


def test_upload_object(client: TestClient):
    app_state.integration.upload_object.return_value = ObjectUploadResponse(
        bucket="test-bucket",
        key="data/file.csv",
        size=16,
        etag="abc",
    )
    content = base64.b64encode(b"Hello, S3 world!").decode()
    response = client.post(
        "/objects/upload?account_name=test-s3",
        json={
            "bucket": "test-bucket",
            "key": "data/file.csv",
            "content_base64": content,
        },
    )
    assert response.status_code == 200
    assert response.json()["key"] == "data/file.csv"


def test_download_object(client: TestClient):
    content_b64 = base64.b64encode(b"file content").decode()
    app_state.integration.download_object.return_value = ObjectDownloadResponse(
        key="file.txt",
        bucket="test-bucket",
        content_base64=content_b64,
        size=12,
        content_type="text/plain",
    )
    response = client.get(
        "/objects/download?account_name=test-s3&bucket=test-bucket&key=file.txt",
    )
    assert response.status_code == 200
    assert response.json()["key"] == "file.txt"


def test_delete_object(client: TestClient):
    app_state.integration.delete_object.return_value = {
        "status": "deleted",
        "bucket": "test-bucket",
        "key": "old.txt",
    }
    response = client.request(
        "DELETE",
        "/objects?account_name=test-s3",
        json={"bucket": "test-bucket", "key": "old.txt"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_copy_object(client: TestClient):
    app_state.integration.copy_object.return_value = ObjectCopyResponse(
        source_bucket="bucket-a",
        source_key="file.txt",
        destination_bucket="bucket-b",
        destination_key="archive/file.txt",
    )
    response = client.post(
        "/objects/copy?account_name=test-s3",
        json={
            "source_bucket": "bucket-a",
            "source_key": "file.txt",
            "destination_bucket": "bucket-b",
            "destination_key": "archive/file.txt",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "copied"


def test_generate_presigned_url(client: TestClient):
    app_state.integration.generate_presigned_url.return_value = PresignResponse(
        url="https://s3.example.com/presigned",
        bucket="test-bucket",
        key="file.txt",
        expires_in=3600,
        method="GET",
    )
    response = client.post(
        "/objects/presign?account_name=test-s3",
        json={"bucket": "test-bucket", "key": "file.txt"},
    )
    assert response.status_code == 200
    assert "url" in response.json()


def test_list_buckets(client: TestClient):
    app_state.integration.list_buckets.return_value = [
        BucketInfo(name="bucket-a"),
        BucketInfo(name="bucket-b"),
    ]
    response = client.get("/buckets?account_name=test-s3")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_bucket(client: TestClient):
    app_state.integration.create_bucket.return_value = BucketCreateResponse(
        bucket="new-bucket",
        region="eu-central-1",
    )
    response = client.post(
        "/buckets?account_name=test-s3",
        json={"bucket": "new-bucket", "region": "eu-central-1"},
    )
    assert response.status_code == 200
    assert response.json()["bucket"] == "new-bucket"


def test_delete_bucket(client: TestClient):
    app_state.integration.delete_bucket.return_value = {
        "status": "deleted",
        "bucket": "old-bucket",
    }
    response = client.delete("/buckets/old-bucket?account_name=test-s3")
    assert response.status_code == 200


def test_connection_test(client: TestClient):
    app_state.integration.test_connection.return_value = ConnectionTestResponse(
        status="connected",
        region="eu-central-1",
        buckets_accessible=3,
    )
    response = client.post("/auth/test-s3/test")
    assert response.status_code == 200
    assert response.json()["status"] == "connected"


def test_connection_test_get(client: TestClient):
    """GET /auth/{account}/test — required for platform credential validation."""
    app_state.integration.test_connection.return_value = ConnectionTestResponse(
        status="connected",
        region="us-east-1",
        buckets_accessible=1,
    )
    response = client.get("/auth/test-s3/test")
    assert response.status_code == 200
    assert response.json()["status"] == "connected"


def test_connection_test_unknown_account(client: TestClient):
    response = client.post("/auth/unknown/test")
    assert response.status_code == 404


def test_upload_bad_base64_returns_400(client: TestClient):
    import binascii

    app_state.integration.upload_object.side_effect = binascii.Error("Invalid base64")
    response = client.post(
        "/objects/upload?account_name=test-s3",
        json={
            "bucket": "test-bucket",
            "key": "file.csv",
            "content_base64": "not-valid-base64!!!",
        },
    )
    assert response.status_code == 400


def test_list_objects_no_bucket_returns_400(client: TestClient):
    app_state.integration.list_objects.side_effect = ValueError(
        "No bucket specified and no default_bucket configured for this account"
    )
    response = client.get("/objects?account_name=test-s3&bucket=")
    assert response.status_code == 400


def test_presign_invalid_method_returns_422(client: TestClient):
    response = client.post(
        "/objects/presign?account_name=test-s3",
        json={"bucket": "b", "key": "k", "method": "DELETE"},
    )
    assert response.status_code == 422


def test_connection_test_via_get(client: TestClient):
    app_state.integration.test_connection.return_value = ConnectionTestResponse(
        status="connected",
        region="eu-central-1",
        buckets_accessible=3,
    )
    response = client.get("/auth/test-s3/test")
    assert response.status_code == 200
    assert response.json()["status"] == "connected"

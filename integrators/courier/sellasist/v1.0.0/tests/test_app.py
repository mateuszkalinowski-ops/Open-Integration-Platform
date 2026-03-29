"""Tests for SellAsist Courier FastAPI endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

VALID_CREDENTIALS = {"login": "testshop", "api_key": "test-api-key-123"}


@pytest.fixture
def client():
    with patch("src.app.SellAsistIntegration") as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance
        mock_instance.close = AsyncMock()
        from src.app import app

        with TestClient(app) as c:
            yield c


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_readiness_endpoint(client: TestClient):
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["version"] == "1.0.0"


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration, client: TestClient):
    mock_integration.get_label_bytes = AsyncMock(return_value=(b"%PDF-1.4 sellasist label", 200))
    response = client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["SA123456"],
            "external_id": "ORD-001",
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers


@patch("src.app.integration")
def test_get_label_filename_from_waybill(mock_integration, client: TestClient):
    mock_integration.get_label_bytes = AsyncMock(return_value=(b"%PDF-1.4 label", 200))
    response = client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["WB999"],
            "external_id": "ORD-002",
        },
    )
    assert response.status_code == 200
    assert "WB999.pdf" in response.headers["content-disposition"]


@patch("src.app.integration")
def test_get_label_error_returns_json(mock_integration, client: TestClient):
    mock_integration.get_label_bytes = AsyncMock(return_value=("Label not found", 404))
    response = client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["INVALID"],
            "external_id": "ORD-003",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "LABEL_RETRIEVAL_FAILED"


@patch("src.app.integration")
def test_get_label_error_message_in_response(mock_integration, client: TestClient):
    mock_integration.get_label_bytes = AsyncMock(return_value=("API key expired", 401))
    response = client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["SA123456"],
            "external_id": "ORD-004",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["message"] == "API key expired"


@patch("src.app.integration")
def test_get_label_server_error(mock_integration, client: TestClient):
    mock_integration.get_label_bytes = AsyncMock(return_value=("Internal server error", 500))
    response = client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["SA123456"],
            "external_id": "ORD-005",
        },
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "LABEL_RETRIEVAL_FAILED"


@patch("src.app.integration")
def test_get_label_calls_integration_correctly(mock_integration, client: TestClient):
    mock_integration.get_label_bytes = AsyncMock(return_value=(b"%PDF", 200))
    client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["WB001", "WB002"],
            "external_id": "EXT-100",
        },
    )
    mock_integration.get_label_bytes.assert_called_once()
    call_kwargs = mock_integration.get_label_bytes.call_args
    assert call_kwargs.kwargs["waybill_numbers"] == ["WB001", "WB002"]
    assert call_kwargs.kwargs["external_id"] == "EXT-100"


def test_missing_credentials_returns_422(client: TestClient):
    response = client.post(
        "/labels",
        json={"waybill_numbers": ["WB001"], "external_id": "EXT"},
    )
    assert response.status_code == 422


def test_missing_waybill_numbers_returns_422(client: TestClient):
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "external_id": "EXT"},
    )
    assert response.status_code == 422

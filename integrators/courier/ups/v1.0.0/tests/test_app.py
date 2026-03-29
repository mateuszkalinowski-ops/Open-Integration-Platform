"""Tests for UPS Courier FastAPI endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_CREDENTIALS = {
    "login": "client_id",
    "password": "client_secret",
    "shipper_number": "ABC123",
    "access_token": "bearer-token-xyz",
}

VALID_SHIPMENT_PAYLOAD = {
    "credentials": VALID_CREDENTIALS,
    "serviceName": "11",
    "content": "Electronics",
    "parcels": [{"height": 10.0, "length": 30.0, "weight": 5.0, "width": 20.0}],
    "shipper": {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "street": "Testowa",
        "building_number": "1",
        "city": "Warszawa",
        "postal_code": "00-001",
        "country_code": "PL",
    },
    "receiver": {
        "first_name": "Anna",
        "last_name": "Nowak",
        "street": "Odbiorcza",
        "building_number": "5",
        "city": "Krakow",
        "postal_code": "30-001",
        "country_code": "PL",
    },
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "ups"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["http_client"] == "ok"


@patch("src.app.integration")
def test_login_success(mock_integration):
    mock_integration.login = AsyncMock(
        return_value=({"access_token": "new-token", "token_type": "Bearer", "expires_in": 3600}, 200)
    )
    response = client.post(
        "/login",
        json={"credentials": VALID_CREDENTIALS},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "new-token"


@patch("src.app.integration")
def test_login_failure(mock_integration):
    mock_integration.login = AsyncMock(side_effect=Exception("Auth failed"))
    response = client.post(
        "/login",
        json={"credentials": VALID_CREDENTIALS},
    )
    assert response.status_code == 500


@patch("src.app.integration")
def test_create_shipment_success(mock_integration):
    mock_integration.create_order = AsyncMock(
        return_value=(
            {"id": "UPS-001", "waybill_number": "1Z999AA10123456784", "order_status": "CREATED"},
            201,
        )
    )
    response = client.post("/shipments", json=VALID_SHIPMENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "UPS-001"
    assert data["waybill_number"] == "1Z999AA10123456784"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = AsyncMock(side_effect=Exception("UPS API error"))
    response = client.post("/shipments", json=VALID_SHIPMENT_PAYLOAD)
    assert response.status_code == 500


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = AsyncMock(
        return_value=(b"%PDF-1.4 UPS shipping label", 200)
    )
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["1Z999AA10123456784"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_error_returns_json(mock_integration):
    mock_integration.get_waybill_label_bytes = AsyncMock(
        return_value=("Label not found", 404)
    )
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["INVALID"]},
    )
    assert response.status_code == 404
    assert "error" in response.json()


@patch("src.app.integration")
def test_get_label_exception(mock_integration):
    mock_integration.get_waybill_label_bytes = AsyncMock(side_effect=Exception("Network error"))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["1Z999AA10123456784"]},
    )
    assert response.status_code == 500


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = AsyncMock(
        return_value=("IN_TRANSIT", 200)
    )
    response = client.post(
        "/shipments/1Z999AA10123456784/status",
        json={"credentials": VALID_CREDENTIALS},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_TRANSIT"


@patch("src.app.integration")
def test_get_status_error(mock_integration):
    mock_integration.get_order_status = AsyncMock(
        return_value=("Tracking not available", 404)
    )
    response = client.post(
        "/shipments/1Z999AA10123456784/status",
        json={"credentials": VALID_CREDENTIALS},
    )
    assert response.status_code == 404
    assert "error" in response.json()


@patch("src.app.integration")
def test_get_status_exception(mock_integration):
    mock_integration.get_order_status = AsyncMock(side_effect=Exception("Timeout"))
    response = client.post(
        "/shipments/1Z999AA10123456784/status",
        json={"credentials": VALID_CREDENTIALS},
    )
    assert response.status_code == 500


@patch("src.app.integration")
def test_get_rates_success(mock_integration):
    mock_integration.get_rates = AsyncMock(
        return_value=(
            {
                "products": [
                    {"name": "UPS Express", "price": 45.99, "currency": "PLN", "delivery_days": 1},
                    {"name": "UPS Standard", "price": 25.50, "currency": "PLN", "delivery_days": 3},
                ],
                "source": "ups",
                "raw": {},
            },
            200,
        )
    )
    response = client.post(
        "/rates",
        json={
            "credentials": VALID_CREDENTIALS,
            "senderPostalCode": "00-001",
            "senderCity": "Warszawa",
            "receiverPostalCode": "30-001",
            "receiverCity": "Krakow",
            "weight": 5.0,
            "length": 30,
            "width": 20,
            "height": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) == 2


@patch("src.app.integration")
def test_get_rates_error_returns_empty_products(mock_integration):
    mock_integration.get_rates = AsyncMock(
        return_value=({"error": "Rate lookup failed"}, 500)
    )
    response = client.post(
        "/rates",
        json={
            "credentials": VALID_CREDENTIALS,
            "senderPostalCode": "00-001",
            "receiverPostalCode": "30-001",
            "weight": 5.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "ups"
    assert data["products"] == []


@patch("src.app.integration")
def test_get_rates_exception_returns_fallback(mock_integration):
    mock_integration.get_rates = AsyncMock(side_effect=Exception("Network error"))
    response = client.post(
        "/rates",
        json={
            "credentials": VALID_CREDENTIALS,
            "senderPostalCode": "00-001",
            "receiverPostalCode": "30-001",
            "weight": 5.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "ups"


@patch("src.app.integration")
def test_upload_document_success(mock_integration):
    mock_integration.upload_file_to_order = AsyncMock(
        return_value=({"status": "uploaded", "document_id": "DOC-001"}, 200)
    )
    response = client.post(
        "/upload-documents",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill": "1Z999AA10123456784",
            "filename": "invoice.pdf",
            "file": "base64encodedcontent==",
            "type": "001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "DOC-001"


@patch("src.app.integration")
def test_upload_document_error(mock_integration):
    mock_integration.upload_file_to_order = AsyncMock(side_effect=Exception("Upload failed"))
    response = client.post(
        "/upload-documents",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill": "1Z999AA10123456784",
            "filename": "doc.pdf",
            "file": "base64==",
        },
    )
    assert response.status_code == 500


@pytest.mark.parametrize(
    "status_value",
    ["CREATED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "EXCEPTION"],
)
@patch("src.app.integration")
def test_status_mapping(mock_integration, status_value):
    mock_integration.get_order_status = AsyncMock(
        return_value=(status_value, 200)
    )
    response = client.post(
        "/shipments/1Z999AA10123456784/status",
        json={"credentials": VALID_CREDENTIALS},
    )
    assert response.status_code == 200
    assert response.json()["status"] == status_value

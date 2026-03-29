"""Tests for Packeta Courier FastAPI endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_CREDENTIALS = {"api_password": "test-api-pass", "eshop": "test-eshop"}
VALID_COMMAND = {
    "service_name": "STANDARD",
    "shipment_date": "2026-03-01",
    "content": "Books",
    "parcels": [{"weight": 5.0, "length": 30, "width": 20, "height": 10}],
    "shipper": {"first_name": "Jan", "last_name": "Kowalski", "city": "Warszawa", "postal_code": "00-001"},
    "receiver": {"first_name": "Anna", "last_name": "Nowak", "city": "Krakow", "postal_code": "30-001"},
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "packeta"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "soap_client" in data["checks"]


@patch("src.app.integration")
def test_create_shipment_success(mock_integration):
    mock_integration.create_order = MagicMock(
        return_value=({"order_id": "PKT-123", "waybill_number": "Z000111222"}, 201)
    )
    response = client.post(
        "/shipments",
        json={"credentials": VALID_CREDENTIALS, "command": VALID_COMMAND},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == "PKT-123"
    assert data["waybill_number"] == "Z000111222"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = MagicMock(
        return_value=({"error": "Invalid address"}, 400)
    )
    response = client.post(
        "/shipments",
        json={"credentials": VALID_CREDENTIALS, "command": VALID_COMMAND},
    )
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = MagicMock(
        return_value=("DELIVERED", 200)
    )
    response = client.post(
        "/shipments/status",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "Z000111222"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"


@patch("src.app.integration")
def test_get_status_error(mock_integration):
    mock_integration.get_order_status = MagicMock(
        return_value=("Not found", 404)
    )
    response = client.post(
        "/shipments/status",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "INVALID"},
    )
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(
        return_value=(b"%PDF-1.4 fake label", 200)
    )
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["Z000111222"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_with_external_id(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(
        return_value=(b"%PDF-1.4 label", 200)
    )
    response = client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["Z000111222"],
            "external_id": "EXT-001",
        },
    )
    assert response.status_code == 200
    mock_integration.get_waybill_label_bytes.assert_called_once()


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(
        return_value=("Label generation failed", 500)
    )
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["INVALID"]},
    )
    assert response.status_code == 500


@patch("src.app.integration")
def test_cancel_shipment_success(mock_integration):
    mock_integration.delete_order = MagicMock(
        return_value=("cancelled", 200)
    )
    response = client.post(
        "/shipments/delete",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "Z000111222"},
    )
    assert response.status_code == 200
    assert response.json()["result"] == "cancelled"


@patch("src.app.integration")
def test_cancel_shipment_error(mock_integration):
    mock_integration.delete_order = MagicMock(
        return_value=("Cannot cancel shipped order", 409)
    )
    response = client.post(
        "/shipments/delete",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "Z000111222"},
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "status_value",
    ["CREATED", "IN_TRANSIT", "DELIVERED", "RETURNED", "CANCELLED"],
)
@patch("src.app.integration")
def test_status_mapping(mock_integration, status_value):
    mock_integration.get_order_status = MagicMock(
        return_value=(status_value, 200)
    )
    response = client.post(
        "/shipments/status",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "Z000111222"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == status_value

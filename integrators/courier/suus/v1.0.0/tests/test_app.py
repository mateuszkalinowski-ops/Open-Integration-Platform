"""Tests for Suus Courier FastAPI endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_CREDENTIALS = {"login": "testuser", "password": "testpass"}
VALID_COMMAND = {
    "service_name": "STANDARD",
    "shipment_date": "2026-03-01",
    "content": "Pallets",
    "parcels": [{"weight": 500.0, "length": 120, "width": 80, "height": 100}],
    "shipper": {"first_name": "Jan", "last_name": "Kowalski", "city": "Warszawa", "postal_code": "00-001"},
    "receiver": {"first_name": "Anna", "last_name": "Nowak", "city": "Krakow", "postal_code": "30-001"},
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "suus"


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
        return_value=({"order_id": "SUUS-001", "waybill_number": "SUUS123456"}, 201)
    )
    response = client.post(
        "/shipments",
        json={"credentials": VALID_CREDENTIALS, "command": VALID_COMMAND},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == "SUUS-001"
    assert data["waybill_number"] == "SUUS123456"


@patch("src.app.integration")
def test_create_shipment_bad_request(mock_integration):
    mock_integration.create_order = MagicMock(return_value=({"error": "Invalid address"}, 400))
    response = client.post(
        "/shipments",
        json={"credentials": VALID_CREDENTIALS, "command": VALID_COMMAND},
    )
    assert response.status_code == 400


@patch("src.app.integration")
def test_create_shipment_unauthorized(mock_integration):
    mock_integration.create_order = MagicMock(return_value=({"error": "Invalid credentials"}, 401))
    response = client.post(
        "/shipments",
        json={"credentials": VALID_CREDENTIALS, "command": VALID_COMMAND},
    )
    assert response.status_code == 401


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=("DELIVERED", 200))
    response = client.post(
        "/shipments/status",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "SUUS123456"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"


@patch("src.app.integration")
def test_get_status_not_found(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=("Not found", 404))
    response = client.post(
        "/shipments/status",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "INVALID"},
    )
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 suus label content", 200))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["SUUS123456"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_multiple_waybills(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 merged labels", 200))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["SUUS001", "SUUS002"]},
    )
    assert response.status_code == 200
    mock_integration.get_waybill_label_bytes.assert_called_once()


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=("Label generation failed", 500))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["INVALID"]},
    )
    assert response.status_code == 500


@pytest.mark.parametrize(
    "status_value",
    ["CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"],
)
@patch("src.app.integration")
def test_status_mapping(mock_integration, status_value):
    mock_integration.get_order_status = MagicMock(return_value=(status_value, 200))
    response = client.post(
        "/shipments/status",
        json={"credentials": VALID_CREDENTIALS, "waybill_number": "SUUS123456"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == status_value


@pytest.mark.parametrize(
    "error_code",
    [400, 401, 403, 404, 500],
)
@patch("src.app.integration")
def test_create_shipment_error_codes(mock_integration, error_code):
    mock_integration.create_order = MagicMock(return_value=({"error": "fail"}, error_code))
    response = client.post(
        "/shipments",
        json={"credentials": VALID_CREDENTIALS, "command": VALID_COMMAND},
    )
    assert response.status_code == error_code

"""Tests for Schenker Courier FastAPI endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_CREDENTIALS = {"login": "testuser", "password": "testpass"}
HEADER_CREDENTIALS = {"X-Login": "testuser", "X-Password": "testpass"}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "schenker"


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
        return_value=({"order_id": "SCH-001", "waybill_number": "SCH123456789"}, 201)
    )
    response = client.post(
        "/shipments",
        json={
            "credentials": VALID_CREDENTIALS,
            "shipper": {"first_name": "Jan", "last_name": "Kowalski", "city": "Warszawa", "postal_code": "00-001"},
            "receiver": {"first_name": "Anna", "last_name": "Nowak", "city": "Krakow", "postal_code": "30-001"},
            "parcels": [{"weight": 500.0, "parcel_type": "PALLET"}],
            "content": "Industrial parts",
            "service_name": "SYSTEM",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == "SCH-001"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = MagicMock(side_effect=ValueError("Invalid weight"))
    response = client.post(
        "/shipments",
        json={
            "credentials": VALID_CREDENTIALS,
            "parcels": [{"weight": -1}],
        },
    )
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=("IN_TRANSIT", 200))
    response = client.get(
        "/shipments/SCH123456789/status",
        headers=HEADER_CREDENTIALS,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_TRANSIT"


@patch("src.app.integration")
def test_get_status_with_credentials_id(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=("DELIVERED", 200))
    response = client.get(
        "/shipments/SCH123456789/status",
        headers={**HEADER_CREDENTIALS, "X-Credentials-Id": "CRED-001"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"


@patch("src.app.integration")
def test_get_status_exception(mock_integration):
    mock_integration.get_order_status = MagicMock(side_effect=RuntimeError("Service down"))
    response = client.get(
        "/shipments/SCH123456789/status",
        headers=HEADER_CREDENTIALS,
    )
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_tracking_success(mock_integration):
    mock_integration.get_tracking_info = MagicMock(
        return_value=(
            {"waybill": "SCH123456789", "events": [{"status": "PICKED_UP", "timestamp": "2026-03-01T08:00:00Z"}]},
            200,
        )
    )
    response = client.get("/shipments/SCH123456789/tracking")
    assert response.status_code == 200
    data = response.json()
    assert data["waybill"] == "SCH123456789"


@patch("src.app.integration")
def test_get_tracking_not_found(mock_integration):
    mock_integration.get_tracking_info = MagicMock(return_value=({"error": "Not found"}, 404))
    response = client.get("/shipments/INVALID/tracking")
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 schenker label", 200))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["SCH123456789"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=("Label unavailable", 404))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["INVALID"]},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "Label unavailable"


@patch("src.app.integration")
def test_get_label_exception(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(side_effect=Exception("SOAP fault"))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["SCH123456789"]},
    )
    assert response.status_code == 400


@patch("src.app.integration")
def test_cancel_shipment_success(mock_integration):
    mock_integration.delete_order = MagicMock(return_value=({"status": "cancelled"}, 200))
    response = client.delete(
        "/shipments/SCH123456789",
        headers=HEADER_CREDENTIALS,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@patch("src.app.integration")
def test_cancel_shipment_error(mock_integration):
    mock_integration.delete_order = MagicMock(side_effect=RuntimeError("Cannot cancel"))
    response = client.delete(
        "/shipments/SCH123456789",
        headers=HEADER_CREDENTIALS,
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "status_value",
    ["CREATED", "PICKED_UP", "IN_TRANSIT", "AT_TERMINAL", "DELIVERED", "CANCELLED"],
)
@patch("src.app.integration")
def test_status_mapping(mock_integration, status_value):
    mock_integration.get_order_status = MagicMock(return_value=(status_value, 200))
    response = client.get(
        "/shipments/SCH123456789/status",
        headers=HEADER_CREDENTIALS,
    )
    assert response.status_code == 200
    assert response.json()["status"] == status_value

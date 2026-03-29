"""Tests for Poczta Polska Courier FastAPI endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_CREDENTIALS = {"login": "testuser", "password": "testpass"}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "pocztapolska"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "tracking_client" in data["checks"]
    assert "posting_client" in data["checks"]


@patch("src.app.integration")
def test_create_shipment_success(mock_integration):
    mock_integration.create_order = MagicMock(
        return_value=({"order_id": "PP-123", "waybill_number": "PP000111222PL"}, 201)
    )
    response = client.post(
        "/shipments",
        json={
            "credentials": VALID_CREDENTIALS,
            "shipper": {"first_name": "Jan", "last_name": "Kowalski", "city": "Warszawa", "postal_code": "00-001"},
            "receiver": {"first_name": "Anna", "last_name": "Nowak", "city": "Krakow", "postal_code": "30-001"},
            "parcels": [{"weight": 5.0}],
            "content": "Documents",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == "PP-123"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = MagicMock(side_effect=ValueError("Invalid parcel dimensions"))
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
    mock_integration.get_order_status = MagicMock(return_value=("DELIVERED", 200))
    response = client.get(
        "/shipments/PP000111222PL/status",
        headers={"X-Login": "testuser", "X-Password": "testpass"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"


@patch("src.app.integration")
def test_get_status_exception(mock_integration):
    mock_integration.get_order_status = MagicMock(side_effect=RuntimeError("API down"))
    response = client.get(
        "/shipments/PP000111222PL/status",
        headers={"X-Login": "testuser", "X-Password": "testpass"},
    )
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_tracking_success(mock_integration):
    mock_integration.get_tracking_info = MagicMock(
        return_value=(
            {"waybill": "PP000111222PL", "events": [{"status": "ACCEPTED", "timestamp": "2026-03-01T10:00:00Z"}]},
            200,
        )
    )
    response = client.get("/shipments/PP000111222PL/tracking")
    assert response.status_code == 200
    data = response.json()
    assert data["waybill"] == "PP000111222PL"
    assert len(data["events"]) == 1


@patch("src.app.integration")
def test_get_tracking_not_found(mock_integration):
    mock_integration.get_tracking_info = MagicMock(return_value=({"error": "Not found"}, 404))
    response = client.get("/shipments/INVALID/tracking")
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 poczta polska label", 200))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["PP000111222PL"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_with_external_id(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 label", 200))
    response = client.post(
        "/labels",
        json={
            "credentials": VALID_CREDENTIALS,
            "waybill_numbers": ["PP000111222PL"],
            "external_id": ["EXT-001"],
        },
    )
    assert response.status_code == 200


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=("Label not available", 404))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["INVALID"]},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "Label not available"


@patch("src.app.integration")
def test_get_label_exception(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(side_effect=Exception("SOAP fault"))
    response = client.post(
        "/labels",
        json={"credentials": VALID_CREDENTIALS, "waybill_numbers": ["PP000111222PL"]},
    )
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_points_success(mock_integration):
    mock_integration.get_points = MagicMock(
        return_value=(
            {"points": [{"id": "WAW01", "name": "Warszawa Centrum", "type": "POST_OFFICE"}]},
            200,
        )
    )
    response = client.post(
        "/points",
        json={"credentials": VALID_CREDENTIALS, "voivodeship_id": "14"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) == 1


@patch("src.app.integration")
def test_get_points_exception(mock_integration):
    mock_integration.get_points = MagicMock(side_effect=RuntimeError("Service unavailable"))
    response = client.post(
        "/points",
        json={"credentials": VALID_CREDENTIALS, "voivodeship_id": "14"},
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "status_value",
    ["ACCEPTED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "RETURNED"],
)
@patch("src.app.integration")
def test_status_mapping(mock_integration, status_value):
    mock_integration.get_order_status = MagicMock(return_value=(status_value, 200))
    response = client.get(
        "/shipments/PP000111222PL/status",
        headers={"X-Login": "testuser", "X-Password": "testpass"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == status_value

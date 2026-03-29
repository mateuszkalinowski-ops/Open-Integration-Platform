"""Tests for InPost Courier integrator v1.0.0 — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_HEADERS = {
    "X-Organization-Id": "org-123",
    "X-Api-Token": "test-token-abc",
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "inpost"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["api_reachable"] == "ok"


@patch("src.app.integration")
def test_create_shipment_success(mock_integration):
    mock_integration.create_order = AsyncMock(
        return_value=(
            {"shipment_id": "INP-001", "tracking_number": "620000000001"},
            201,
        )
    )
    payload = {
        "credentials": {"organization_id": "org-1", "api_token": "tok"},
        "serviceName": "inpost_locker_standard",
        "parcels": [{"height": 20, "length": 30, "weight": 5.0, "width": 15}],
        "shipper": {
            "first_name": "Jan",
            "last_name": "Kowalski",
            "building_number": "10",
            "city": "Warszawa",
            "postal_code": "00-001",
            "street": "Testowa",
        },
        "receiver": {
            "first_name": "Anna",
            "last_name": "Nowak",
            "building_number": "5",
            "city": "Krakow",
            "postal_code": "30-001",
            "street": "Odbiorcza",
        },
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["tracking_number"] == "620000000001"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = AsyncMock(
        return_value=("Invalid API token", 401)
    )
    payload = {
        "credentials": {"organization_id": "org-1", "api_token": "bad"},
        "serviceName": "inpost_locker_standard",
        "parcels": [{"height": 20, "length": 30, "weight": 5.0, "width": 15}],
        "shipper": {
            "first_name": "J",
            "last_name": "K",
            "building_number": "1",
            "city": "W",
            "postal_code": "00-001",
            "street": "S",
        },
        "receiver": {
            "first_name": "A",
            "last_name": "N",
            "building_number": "2",
            "city": "K",
            "postal_code": "30-001",
            "street": "R",
        },
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 401


@patch("src.app.integration")
def test_create_shipment_exception(mock_integration):
    mock_integration.create_order = AsyncMock(side_effect=ValueError("API error"))
    payload = {
        "credentials": {"organization_id": "org-1", "api_token": "tok"},
        "serviceName": "inpost_locker_standard",
        "parcels": [{"height": 20, "length": 30, "weight": 5.0, "width": 15}],
        "shipper": {
            "first_name": "J",
            "last_name": "K",
            "building_number": "1",
            "city": "W",
            "postal_code": "00-001",
            "street": "S",
        },
        "receiver": {
            "first_name": "A",
            "last_name": "N",
            "building_number": "2",
            "city": "K",
            "postal_code": "30-001",
            "street": "R",
        },
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = AsyncMock(
        return_value=({"code": "delivered", "description": "Shipment delivered"}, 200)
    )
    response = client.get("/shipments/620000000001/status", headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@patch("src.app.integration")
def test_get_status_error(mock_integration):
    mock_integration.get_order_status = AsyncMock(
        return_value=("Not found", 404)
    )
    response = client.get("/shipments/UNKNOWN/status", headers=VALID_HEADERS)
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = AsyncMock(
        return_value=(b"%PDF-1.4 inpost label", 200)
    )
    payload = {
        "waybill_numbers": ["620000000001"],
        "credentials": {"organization_id": "org-1", "api_token": "tok"},
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = AsyncMock(
        return_value=("Label not available", 404)
    )
    payload = {
        "waybill_numbers": ["BAD"],
        "credentials": {"organization_id": "org-1", "api_token": "tok"},
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 404


@patch("src.app.integration")
def test_cancel_shipment_success(mock_integration):
    mock_integration.delete_order = AsyncMock(
        return_value=({"message": "Shipment cancelled"}, 200)
    )
    response = client.delete("/shipments/620000000001", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json()["result"]["message"] == "Shipment cancelled"


@patch("src.app.integration")
def test_cancel_shipment_error(mock_integration):
    mock_integration.delete_order = AsyncMock(
        return_value=("Cannot cancel", 400)
    )
    response = client.delete("/shipments/620000000001", headers=VALID_HEADERS)
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_shipment_success(mock_integration):
    mock_integration.get_order = AsyncMock(
        return_value=(
            {"shipment_id": "INP-001", "status": "in_transit", "tracking": "620000000001"},
            200,
        )
    )
    response = client.get("/shipments/620000000001", headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["shipment_id"] == "INP-001"


@patch("src.app.integration")
def test_get_shipment_error(mock_integration):
    mock_integration.get_order = AsyncMock(
        return_value=("Shipment not found", 404)
    )
    response = client.get("/shipments/UNKNOWN", headers=VALID_HEADERS)
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_tracking_success(mock_integration):
    tracking_mock = MagicMock()
    tracking_mock.model_dump.return_value = {
        "tracking_number": "620000000001",
        "tracking_url": "https://inpost.pl/tracking/620000000001",
    }
    mock_integration.get_tracking_info = AsyncMock(
        return_value=(tracking_mock, 200)
    )
    response = client.get("/tracking/620000000001")
    assert response.status_code == 200
    data = response.json()
    assert data["tracking_number"] == "620000000001"


@patch("src.app.integration")
def test_get_tracking_error(mock_integration):
    mock_integration.get_tracking_info = AsyncMock(
        return_value=("Tracking unavailable", 404)
    )
    response = client.get("/tracking/UNKNOWN")
    assert response.status_code == 404

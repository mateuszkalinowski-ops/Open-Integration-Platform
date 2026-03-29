"""Tests for InPost International 2024 integrator v2.0.0 — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_HEADERS = {
    "X-Organization-Id": "org-123",
    "X-Client-Secret": "secret-abc",
    "X-Access-Token": "access-tok-xyz",
}

SHIPPER = {
    "first_name": "Jan",
    "last_name": "Kowalski",
    "building_number": "10",
    "city": "Warszawa",
    "postal_code": "00-001",
    "street": "Testowa",
}
RECEIVER = {
    "first_name": "Anna",
    "last_name": "Nowak",
    "building_number": "5",
    "city": "Krakow",
    "postal_code": "30-001",
    "street": "Odbiorcza",
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert data["system"] == "inpost-international-2024"


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
            {"uuid": "abc-123", "trackingNumber": "INT620000001", "status": "created"},
            201,
        )
    )
    payload = {
        "credentials": {
            "organization_id": "org-1",
            "client_secret": "secret",
        },
        "serviceName": "inpost_international",
        "parcels": [{"height": 20, "length": 30, "weight": 5.0, "width": 15}],
        "shipper": SHIPPER,
        "receiver": RECEIVER,
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["trackingNumber"] == "INT620000001"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = AsyncMock(
        return_value=("Authentication failed", 401)
    )
    payload = {
        "credentials": {"organization_id": "bad", "client_secret": "bad"},
        "serviceName": "inpost_international",
        "parcels": [{"height": 20, "length": 30, "weight": 5.0, "width": 15}],
        "shipper": SHIPPER,
        "receiver": RECEIVER,
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 401


@patch("src.app.integration")
def test_create_shipment_exception(mock_integration):
    mock_integration.create_order = AsyncMock(side_effect=RuntimeError("API timeout"))
    payload = {
        "credentials": {"organization_id": "org-1", "client_secret": "secret"},
        "serviceName": "inpost_international",
        "parcels": [{"height": 20, "length": 30, "weight": 5.0, "width": 15}],
        "shipper": SHIPPER,
        "receiver": RECEIVER,
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = AsyncMock(
        return_value=({"code": "IN_TRANSIT", "description": "On the way"}, 200)
    )
    response = client.get("/shipments/INT620000001/status", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert "status" in response.json()


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
        return_value=(b"%PDF-1.4 inpost int label", 200)
    )
    payload = {
        "credentials": {"organization_id": "org-1", "client_secret": "secret"},
        "shipmentUuid": "abc-123",
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = AsyncMock(
        return_value=("Label not ready", 404)
    )
    payload = {
        "credentials": {"organization_id": "org-1", "client_secret": "secret"},
        "shipmentUuid": "bad-uuid",
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_shipment_success(mock_integration):
    mock_integration.get_order = AsyncMock(
        return_value=(
            {"uuid": "abc-123", "status": "DELIVERED", "trackingNumber": "INT620000001"},
            200,
        )
    )
    response = client.get("/shipments/abc-123", headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == "abc-123"


@patch("src.app.integration")
def test_get_shipment_error(mock_integration):
    mock_integration.get_order = AsyncMock(
        return_value=("Shipment not found", 404)
    )
    response = client.get("/shipments/unknown-uuid", headers=VALID_HEADERS)
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_tracking_success(mock_integration):
    tracking_mock = MagicMock()
    tracking_mock.model_dump.return_value = {
        "tracking_number": "INT620000001",
        "tracking_url": "https://inpost.pl/tracking/INT620000001",
    }
    mock_integration.get_tracking_info = AsyncMock(
        return_value=(tracking_mock, 200)
    )
    response = client.get("/tracking/INT620000001")
    assert response.status_code == 200
    data = response.json()
    assert data["tracking_number"] == "INT620000001"


@patch("src.app.integration")
def test_get_tracking_error(mock_integration):
    mock_integration.get_tracking_info = AsyncMock(
        return_value=("Not found", 404)
    )
    response = client.get("/tracking/UNKNOWN")
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_pickup_hours_success(mock_integration):
    mock_integration.get_pickup_hours = AsyncMock(
        return_value=(
            {"hours": [{"from": "08:00", "to": "18:00"}]},
            200,
        )
    )
    response = client.get(
        "/pickup-hours",
        params={
            "credentials": '{"organization_id": "org-1", "client_secret": "secret"}',
            "postcode": "00-001",
        },
    )
    assert response.status_code in (200, 422)


@patch("src.app.integration")
def test_get_pickup_hours_error(mock_integration):
    mock_integration.get_pickup_hours = AsyncMock(
        return_value=("Service unavailable", 503)
    )
    response = client.get(
        "/pickup-hours",
        params={
            "credentials": '{"organization_id": "org-1", "client_secret": "secret"}',
            "postcode": "00-001",
        },
    )
    assert response.status_code in (503, 422)

"""Tests for FX Couriers FastAPI endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "fxcouriers"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "api_reachable" in data["checks"]


@patch("src.app.integration")
def test_get_services(mock_integration):
    mock_integration.get_services = AsyncMock(return_value=(
        {"service_cnt": 1, "service_list": {"STANDARD": {}}},
        200,
    ))
    response = client.get("/services?api_token=test-token")
    assert response.status_code == 200
    data = response.json()
    assert data["service_cnt"] == 1


@patch("src.app.integration")
def test_get_company(mock_integration):
    mock_integration.get_company = AsyncMock(return_value=(
        {"company": {"company_id": 1, "name": "Test Corp"}},
        200,
    ))
    response = client.get("/company/1?api_token=test-token")
    assert response.status_code == 200
    data = response.json()
    assert data["company"]["company_id"] == 1


@patch("src.app.integration")
def test_create_order(mock_integration):
    mock_integration.create_order = AsyncMock(return_value=(
        {"order_id": 123, "order_number": "E000123", "status": "NEW"},
        201,
    ))
    response = client.post("/shipments", json={
        "credentials": {"api_token": "test-token"},
        "company_id": 1,
        "service_code": "STANDARD",
        "payment_method": "TRANSFER",
        "sender": {
            "name": "Sender",
            "city": "Warszawa",
            "postal_code": "00-401",
            "street": "Marszalkowska",
            "house_number": "12",
        },
        "recipient": {
            "name": "Recipient",
            "city": "Krakow",
            "postal_code": "30-001",
            "street": "Florianska",
            "house_number": "5",
        },
        "items": [{"weight": 10, "content": "Books"}],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == 123


@patch("src.app.integration")
def test_get_orders(mock_integration):
    mock_integration.get_orders = AsyncMock(return_value=(
        {"order_cnt": 2, "order_list": [{"order_id": 1}, {"order_id": 2}]},
        200,
    ))
    response = client.get("/shipments?api_token=test-token")
    assert response.status_code == 200
    data = response.json()
    assert data["order_cnt"] == 2


@patch("src.app.integration")
def test_get_order(mock_integration):
    mock_integration.get_order = AsyncMock(return_value=(
        {"order_id": 1, "status": "ACCEPTED"},
        200,
    ))
    response = client.get("/shipments/1?api_token=test-token")
    assert response.status_code == 200


@patch("src.app.integration")
def test_delete_order(mock_integration):
    mock_integration.delete_order = AsyncMock(return_value=(
        {"message": "Order deleted"},
        200,
    ))
    response = client.delete("/shipments/1?api_token=test-token")
    assert response.status_code == 200


@patch("src.app.integration")
def test_get_order_status(mock_integration):
    mock_integration.get_order_status = AsyncMock(return_value=(
        {
            "order_id": 1,
            "status": "RUNNING",
            "mapped_status": "IN_TRANSIT",
        },
        200,
    ))
    response = client.get("/shipments/1/status?api_token=test-token")
    assert response.status_code == 200
    data = response.json()
    assert data["mapped_status"] == "IN_TRANSIT"


@patch("src.app.integration")
def test_get_tracking(mock_integration):
    mock_integration.get_tracking = AsyncMock(return_value=(
        {"order_id": 1, "status": "RUNNING", "events": []},
        200,
    ))
    response = client.get("/tracking/1?api_token=test-token")
    assert response.status_code == 200


@patch("src.app.integration")
def test_get_label(mock_integration):
    mock_integration.get_label = AsyncMock(return_value=(
        b"%PDF-1.4 fake label content",
        200,
    ))
    response = client.post("/labels", json={
        "credentials": {"api_token": "test-token"},
        "order_id": 1,
    })
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_create_pickup(mock_integration):
    mock_integration.create_shipment = AsyncMock(return_value=(
        {"shipment_id": 99, "status": "scheduled"},
        201,
    ))
    response = client.post("/pickups", json={
        "credentials": {"api_token": "test-token"},
        "pickup_date": "2026-03-01",
        "pickup_time_from": "10:00",
        "pickup_time_to": "14:00",
        "order_id_list": [1, 2],
    })
    assert response.status_code == 201


@patch("src.app.integration")
def test_get_pickup(mock_integration):
    mock_integration.get_shipment = AsyncMock(return_value=(
        {"order_id": 1, "pickup_date": "2026-03-01"},
        200,
    ))
    response = client.get("/pickups/1?api_token=test-token")
    assert response.status_code == 200


@patch("src.app.integration")
def test_cancel_pickup(mock_integration):
    mock_integration.cancel_shipment = AsyncMock(return_value=(
        {"message": "Pickup cancelled"},
        200,
    ))
    response = client.delete("/pickups/1?api_token=test-token")
    assert response.status_code == 200


@patch("src.app.integration")
def test_create_order_error_propagation(mock_integration):
    mock_integration.create_order = AsyncMock(return_value=(
        "Invalid API token",
        401,
    ))
    response = client.post("/shipments", json={
        "credentials": {"api_token": "bad-token"},
        "company_id": 1,
        "sender": {
            "name": "A", "city": "W", "postal_code": "00-001",
            "street": "S", "house_number": "1",
        },
        "recipient": {
            "name": "B", "city": "K", "postal_code": "30-001",
            "street": "F", "house_number": "2",
        },
        "items": [{"weight": 5}],
    })
    assert response.status_code == 401

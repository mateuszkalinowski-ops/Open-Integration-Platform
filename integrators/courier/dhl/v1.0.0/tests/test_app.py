"""Tests for DHL Courier integrator — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_HEADERS = {
    "X-Username": "testuser",
    "X-Password": "testpass",
    "X-Account-Number": "123456",
    "X-Sap-Number": "SAP001",
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "dhl"


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
        return_value=(
            {"waybill_number": "DHL123456", "status": "created"},
            201,
        )
    )
    payload = {
        "credentials": {"username": "user", "password": "pass"},
        "command": {"sender": {"name": "Test"}, "receiver": {"name": "Recv"}},
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["waybill_number"] == "DHL123456"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = MagicMock(return_value=("Invalid credentials", 401))
    payload = {
        "credentials": {"username": "bad", "password": "bad"},
        "command": {},
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 401


@patch("src.app.integration")
def test_create_shipment_exception(mock_integration):
    mock_integration.create_order = MagicMock(side_effect=ValueError("SOAP fault"))
    payload = {
        "credentials": {"username": "user", "password": "pass"},
        "command": {},
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = MagicMock(
        return_value=({"code": "DELIVERED", "description": "Shipment delivered"}, 200)
    )
    response = client.get("/shipments/DHL123456/status", headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@patch("src.app.integration")
def test_get_status_error(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=("Waybill not found", 404))
    response = client.get("/shipments/UNKNOWN/status", headers=VALID_HEADERS)
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 fake label", 200))
    payload = {
        "waybill_numbers": ["DHL123456"],
        "credentials": {"username": "user", "password": "pass"},
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=("Label generation failed", 500))
    payload = {
        "waybill_numbers": ["BAD"],
        "credentials": {"username": "user", "password": "pass"},
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 500


def test_rates_domestic():
    payload = {
        "sender_country_code": "PL",
        "receiver_country_code": "PL",
        "weight": 3.0,
        "length": 30,
        "width": 20,
        "height": 15,
    }
    response = client.post("/rates", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "dhl"
    assert len(data["products"]) >= 2
    names = [p["name"] for p in data["products"]]
    assert "DHL Parcel Standard" in names
    assert "DHL Parcel Connect" in names


def test_rates_international():
    payload = {
        "sender_country_code": "PL",
        "receiver_country_code": "DE",
        "weight": 5.0,
        "length": 30,
        "width": 20,
        "height": 15,
    }
    response = client.post("/rates", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "dhl"
    assert len(data["products"]) >= 1
    assert data["products"][0]["name"] == "DHL Parcel International"


@pytest.mark.parametrize(
    "weight,expected_min_products",
    [
        (0.5, 4),
        (5.0, 4),
        (15.0, 4),
        (35.0, 2),
    ],
)
def test_rates_domestic_product_count_by_weight(weight, expected_min_products):
    payload = {
        "sender_country_code": "PL",
        "receiver_country_code": "PL",
        "weight": weight,
        "length": 20,
        "width": 15,
        "height": 10,
    }
    response = client.post("/rates", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) >= expected_min_products


@patch("src.app.integration")
def test_cancel_shipment_success(mock_integration):
    mock_integration.delete_order = MagicMock(return_value=({"message": "Order cancelled"}, 200))
    response = client.delete("/shipments/DHL123456", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json()["result"]["message"] == "Order cancelled"


@patch("src.app.integration")
def test_cancel_shipment_error(mock_integration):
    mock_integration.delete_order = MagicMock(return_value=("Cannot cancel delivered shipment", 400))
    response = client.delete("/shipments/DHL123456", headers=VALID_HEADERS)
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_points_success(mock_integration):
    mock_integration.get_points = MagicMock(
        return_value=(
            {"points": [{"name": "DHL POP Warszawa", "id": "PL001"}]},
            200,
        )
    )
    response = client.get(
        "/points",
        headers=VALID_HEADERS,
        params={"city": "Warszawa", "postal_code": "00-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) == 1


@patch("src.app.integration")
def test_get_points_error(mock_integration):
    mock_integration.get_points = MagicMock(return_value=("Service unavailable", 503))
    response = client.get("/points", headers=VALID_HEADERS)
    assert response.status_code == 503

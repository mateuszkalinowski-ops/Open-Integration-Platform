"""Tests for DPD Courier integrator — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

VALID_HEADERS = {
    "X-Login": "testlogin",
    "X-Password": "testpass",
    "X-Master-Fid": "12345",
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "dpd"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "soap_client" in data["checks"]
    assert "soap_info_client" in data["checks"]


@patch("src.app.integration")
def test_create_shipment_success(mock_integration):
    mock_integration.create_order = MagicMock(
        return_value=(
            {"waybill_number": "DPD987654", "status": "created", "session_id": 1001},
            201,
        )
    )
    payload = {
        "credentials": {"login": "user", "password": "pass"},
        "command": {"sender": {"name": "Test Corp"}},
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["waybill_number"] == "DPD987654"


@patch("src.app.integration")
def test_create_shipment_error(mock_integration):
    mock_integration.create_order = MagicMock(return_value=("Invalid credentials", 401))
    payload = {
        "credentials": {"login": "bad", "password": "bad"},
        "command": {},
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 401


@patch("src.app.integration")
def test_create_shipment_exception(mock_integration):
    mock_integration.create_order = MagicMock(side_effect=RuntimeError("SOAP fault"))
    payload = {
        "credentials": {"login": "user", "password": "pass"},
        "command": {},
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 500


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=({"statusCode": "DEL", "description": "Delivered"}, 200))
    response = client.get("/shipments/DPD987654/status", headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@patch("src.app.integration")
def test_get_status_with_info_channel(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=({"statusCode": "IN_TRANSIT"}, 200))
    response = client.get(
        "/shipments/DPD987654/status",
        headers=VALID_HEADERS,
        params={"info_channel": "sms"},
    )
    assert response.status_code == 200


@patch("src.app.integration")
def test_get_status_error(mock_integration):
    mock_integration.get_order_status = MagicMock(return_value=("Not found", 404))
    response = client.get("/shipments/UNKNOWN/status", headers=VALID_HEADERS)
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_label_returns_pdf(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 dpd label", 200))
    payload = {
        "waybill_numbers": ["DPD987654"],
        "credentials": {"login": "user", "password": "pass"},
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_with_external_id(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=(b"%PDF-1.4 dpd label", 200))
    payload = {
        "waybill_numbers": ["DPD987654"],
        "credentials": {"login": "user", "password": "pass"},
        "external_id": "EXT-001",
    }
    response = client.post("/labels", json=payload)
    assert response.status_code == 200


@patch("src.app.integration")
def test_get_label_error(mock_integration):
    mock_integration.get_waybill_label_bytes = MagicMock(return_value=("Label error", 500))
    payload = {
        "waybill_numbers": ["BAD"],
        "credentials": {"login": "user", "password": "pass"},
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
    assert data["source"] == "dpd"
    assert len(data["products"]) >= 2
    names = [p["name"] for p in data["products"]]
    assert "DPD Classic" in names
    assert "DPD Pickup" in names


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
    assert data["source"] == "dpd"
    assert len(data["products"]) == 1
    assert data["products"][0]["name"] == "DPD Classic International"


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
def test_generate_protocol_success(mock_integration):
    mock_integration.generate_protocol = MagicMock(return_value=(b"%PDF-1.4 protocol", 200))
    payload = {
        "waybill_numbers": ["DPD001", "DPD002"],
        "credentials": {"login": "user", "password": "pass"},
        "session_type": "DOMESTIC",
    }
    response = client.post("/protocol", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_generate_protocol_error(mock_integration):
    mock_integration.generate_protocol = MagicMock(return_value=("Protocol generation failed", 500))
    payload = {
        "waybill_numbers": ["BAD"],
        "credentials": {"login": "user", "password": "pass"},
    }
    response = client.post("/protocol", json=payload)
    assert response.status_code == 500

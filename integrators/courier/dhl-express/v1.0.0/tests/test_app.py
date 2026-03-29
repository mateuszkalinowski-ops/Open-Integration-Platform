"""Tests for DHL Express Courier integrator — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from src.app import _normalize_dhl_express_rates, _validate_path_id, app
from src.integration import DhlExpressError

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "dhl-express"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "api_configured" in data["checks"]


def test_validate_path_id_valid():
    assert _validate_path_id("ABC-123_456") == "ABC-123_456"


def test_validate_path_id_invalid():
    with pytest.raises(HTTPException):
        _validate_path_id("../../../etc/passwd")


def test_validate_path_id_empty():
    with pytest.raises(HTTPException):
        _validate_path_id("")


@patch("src.app.integration")
def test_create_shipment_success(mock_integration):
    mock_integration.create_shipment = AsyncMock(
        return_value=(
            {
                "shipmentTrackingNumber": "1234567890",
                "packages": [{"trackingNumber": "JD01234567890"}],
            },
            201,
        )
    )
    payload = {
        "plannedShippingDateAndTime": "2026-04-01T10:00:00Z",
        "productCode": "P",
        "shipper": {
            "address": {
                "streetLine1": "Testowa 1",
                "city": "Warszawa",
                "postalCode": "00-001",
                "countryCode": "PL",
            },
            "contact": {
                "companyName": "Sender Co",
                "fullName": "Jan Kowalski",
                "phone": "+48123456789",
            },
        },
        "receiver": {
            "address": {
                "streetLine1": "Empfanger 2",
                "city": "Berlin",
                "postalCode": "10115",
                "countryCode": "DE",
            },
            "contact": {
                "companyName": "Receiver GmbH",
                "fullName": "Hans Mueller",
                "phone": "+4930123456",
            },
        },
        "content": {
            "packages": [{"weight": 5.0}],
        },
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["shipmentTrackingNumber"] == "1234567890"


@patch("src.app.integration")
def test_create_shipment_dhl_error(mock_integration):
    mock_integration.create_shipment = AsyncMock(side_effect=DhlExpressError("Bad request", 400))
    payload = {
        "plannedShippingDateAndTime": "2026-04-01T10:00:00Z",
        "shipper": {
            "address": {"streetLine1": "T", "city": "W", "postalCode": "00-001", "countryCode": "PL"},
            "contact": {"companyName": "S", "fullName": "J", "phone": "1"},
        },
        "receiver": {
            "address": {"streetLine1": "R", "city": "B", "postalCode": "10115", "countryCode": "DE"},
            "contact": {"companyName": "R", "fullName": "H", "phone": "2"},
        },
        "content": {"packages": [{"weight": 1.0}]},
    }
    response = client.post("/shipments", json=payload)
    assert response.status_code == 400


@patch("src.app.integration")
def test_get_status_success(mock_integration):
    mock_integration.get_tracking = AsyncMock(
        return_value=(
            {
                "shipments": [
                    {
                        "shipmentTrackingNumber": "1234567890",
                        "status": "transit",
                        "events": [{"description": "Shipment picked up"}],
                    }
                ]
            },
            200,
        )
    )
    response = client.get("/shipments/1234567890/status")
    assert response.status_code == 200
    data = response.json()
    assert "shipments" in data


@patch("src.app.integration")
def test_get_status_not_found(mock_integration):
    mock_integration.get_tracking = AsyncMock(side_effect=DhlExpressError("Not found", 404))
    response = client.get("/shipments/UNKNOWN123/status")
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_rates_success(mock_integration):
    mock_integration.get_rates = AsyncMock(
        return_value=(
            {
                "products": [
                    {
                        "productName": "EXPRESS WORLDWIDE",
                        "productCode": "P",
                        "totalPrice": [{"price": 150.00, "priceCurrency": "EUR"}],
                    },
                ]
            },
            200,
        )
    )
    payload = {
        "shipperCountryCode": "PL",
        "shipperPostalCode": "00-001",
        "shipperCity": "Warszawa",
        "receiverCountryCode": "DE",
        "receiverPostalCode": "10115",
        "receiverCity": "Berlin",
        "plannedShippingDate": "2026-04-01T10:00:00Z",
        "weight": 5.0,
        "length": 30,
        "width": 20,
        "height": 15,
    }
    response = client.post("/rates", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


@patch("src.app.integration")
def test_get_rates_standardized_success(mock_integration):
    mock_integration.get_rates = AsyncMock(
        return_value=(
            {
                "products": [
                    {
                        "productName": "EXPRESS WORLDWIDE",
                        "productCode": "P",
                        "totalPrice": [{"price": 150.00, "priceCurrency": "EUR"}],
                        "deliveryCapabilities": {"estimatedDeliveryDateAndTime": "2026-04-03T18:00:00"},
                    },
                ]
            },
            200,
        )
    )
    payload = {
        "shipperCountryCode": "PL",
        "receiverCountryCode": "DE",
        "weight": 5.0,
    }
    response = client.post("/rates/standardized", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "dhl-express"
    assert len(data["products"]) == 1
    assert data["products"][0]["name"] == "EXPRESS WORLDWIDE"


@patch("src.app.integration")
def test_get_rates_standardized_dhl_error(mock_integration):
    mock_integration.get_rates = AsyncMock(side_effect=DhlExpressError("Rate limit", 429))
    payload = {"shipperCountryCode": "PL", "receiverCountryCode": "DE", "weight": 5.0}
    response = client.post("/rates/standardized", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "dhl-express"
    assert "error" in data["raw"]


@patch("src.app.integration")
def test_get_label_success(mock_integration):
    mock_integration.get_label_bytes = AsyncMock(return_value=(b"%PDF-1.4 dhl express label", 200))
    response = client.get("/shipments/1234567890/label")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@patch("src.app.integration")
def test_get_label_not_found(mock_integration):
    mock_integration.get_label_bytes = AsyncMock(return_value=(b"", 200))
    response = client.get("/shipments/1234567890/label")
    assert response.status_code == 404


@patch("src.app.integration")
def test_get_documents_success(mock_integration):
    mock_integration.get_shipment_image = AsyncMock(
        return_value=(
            {"documents": [{"typeCode": "label", "imageFormat": "PDF"}]},
            200,
        )
    )
    response = client.get("/shipments/1234567890/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data


@patch("src.app.integration")
def test_create_pickup_success(mock_integration):
    mock_integration.create_pickup = AsyncMock(
        return_value=(
            {"dispatchConfirmationNumbers": ["PRG999123"]},
            201,
        )
    )
    payload = {
        "plannedPickupDateAndTime": "2026-04-01T10:00:00Z",
        "closeTime": "18:00",
        "location": "Reception",
    }
    response = client.post("/pickups", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "dispatchConfirmationNumbers" in data


@patch("src.app.integration")
def test_update_pickup_success(mock_integration):
    mock_integration.update_pickup = AsyncMock(return_value=({"status": "updated"}, 200))
    response = client.patch(
        "/pickups/PRG999123",
        json={"closeTime": "19:00"},
    )
    assert response.status_code == 200


@patch("src.app.integration")
def test_cancel_pickup_success(mock_integration):
    mock_integration.cancel_pickup = AsyncMock(return_value=({"status": "cancelled"}, 200))
    response = client.delete(
        "/pickups/PRG999123",
        params={"requestorName": "Jan Kowalski", "reason": "rescheduled"},
    )
    assert response.status_code == 200


@patch("src.app.integration")
def test_validate_address_success(mock_integration):
    mock_integration.validate_address = AsyncMock(
        return_value=(
            {"address": [{"cityName": "Warszawa", "countryCode": "PL"}]},
            200,
        )
    )
    response = client.get(
        "/address-validate",
        params={"countryCode": "PL", "postalCode": "00-001", "cityName": "Warszawa"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "address" in data


@patch("src.app.integration")
def test_get_service_points_success(mock_integration):
    mock_integration.get_service_points = AsyncMock(
        return_value=(
            {"servicePoints": [{"id": "SP001", "name": "DHL ServicePoint"}]},
            200,
        )
    )
    response = client.get(
        "/points",
        params={"countryCode": "PL", "postalCode": "00-001"},
    )
    assert response.status_code == 200


@patch("src.app.integration")
def test_get_products_success(mock_integration):
    mock_integration.get_products = AsyncMock(
        return_value=(
            {"products": [{"productCode": "P", "productName": "EXPRESS WORLDWIDE"}]},
            200,
        )
    )
    response = client.get(
        "/products",
        params={
            "originCountryCode": "PL",
            "receiverCountryCode": "DE",
            "weight": 5.0,
            "plannedShippingDate": "2026-04-01T10:00:00Z",
        },
    )
    assert response.status_code == 200


@patch("src.app.integration")
def test_get_landed_cost_success(mock_integration):
    mock_integration.get_landed_cost = AsyncMock(return_value=({"landedCost": {"totalCost": 250.00}}, 200))
    response = client.post("/landed-cost", json={"items": [{"description": "Books"}]})
    assert response.status_code == 200


def test_normalize_dhl_express_rates():
    raw = {
        "products": [
            {
                "productName": "EXPRESS WORLDWIDE",
                "productCode": "P",
                "totalPrice": [{"price": 150.00, "priceCurrency": "EUR"}],
                "deliveryCapabilities": {
                    "estimatedDeliveryDateAndTime": "2026-04-03T18:00:00",
                },
                "weight": {"unitOfMeasurement": "KG"},
            },
            {
                "productCode": "N",
                "totalPrice": [{"price": 100.00, "priceCurrency": "EUR"}],
            },
        ]
    }
    result = _normalize_dhl_express_rates(raw)
    assert result.source == "dhl-express"
    assert len(result.products) == 2
    assert result.products[0].name == "EXPRESS WORLDWIDE"
    assert result.products[0].price == 150.00
    assert result.products[0].currency == "EUR"
    assert result.products[0].delivery_date == "2026-04-03T18:00:00"
    assert result.products[1].name == "N"


def test_normalize_dhl_express_rates_empty():
    result = _normalize_dhl_express_rates({})
    assert result.source == "dhl-express"
    assert result.products == []


@pytest.mark.parametrize(
    "status_code,expected_detail",
    [
        (400, "Bad request to DHL Express"),
        (401, "DHL Express authentication failed"),
        (403, "Access denied by DHL Express"),
        (404, "Resource not found"),
        (429, "Rate limited by DHL Express"),
        (502, "DHL Express error (HTTP 502)"),
    ],
)
def test_sanitize_dhl_error_messages(status_code, expected_detail):
    from src.app import _sanitize_dhl_error

    exc = DhlExpressError("raw error", status_code)
    http_exc = _sanitize_dhl_error(exc)
    assert http_exc.status_code == status_code
    assert http_exc.detail == expected_detail

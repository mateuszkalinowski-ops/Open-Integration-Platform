"""Tests for GLS integrator — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:
    def test_health_returns_healthy(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["system"] == "gls"

    @patch("src.app.integration")
    def test_readiness_healthy_when_client_available(self, mock_integration, client: TestClient):
        mock_integration.client = MagicMock()
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["soap_client"] == "ok"

    @patch("src.app.integration")
    def test_readiness_degraded_when_client_unavailable(self, mock_integration, client: TestClient):
        mock_integration.client = None
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["soap_client"] == "unavailable"


class TestCreateShipment:
    @patch("src.app.integration.create_order")
    def test_create_shipment_success_tuple(self, mock_create, client: TestClient):
        mock_create.return_value = (
            {"waybillNumber": "GLS123", "status": "created"},
            201,
        )
        payload = {
            "credentials": {"username": "user", "password": "pass"},
            "command": {"shipper": {}, "receiver": {}},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201
        assert response.json()["waybillNumber"] == "GLS123"

    @patch("src.app.integration.create_order")
    def test_create_shipment_success_non_tuple(self, mock_create, client: TestClient):
        mock_create.return_value = {"waybillNumber": "GLS456", "status": "created"}
        payload = {
            "credentials": {"username": "user", "password": "pass"},
            "command": {},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201

    @patch("src.app.integration.create_order")
    def test_create_shipment_error_status(self, mock_create, client: TestClient):
        mock_create.return_value = ({"error": "Validation failed"}, 400)
        payload = {
            "credentials": {"username": "user", "password": "pass"},
            "command": {},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400

    @patch("src.app.integration.create_order")
    def test_create_shipment_exception_returns_500(self, mock_create, client: TestClient):
        mock_create.side_effect = Exception("SOAP fault")
        payload = {
            "credentials": {"username": "user", "password": "pass"},
            "command": {},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 500


class TestTracking:
    @patch("src.app.integration.get_tracking_info")
    def test_get_tracking_success(self, mock_tracking, client: TestClient):
        mock_tracking.return_value = (
            {"waybillNumber": "GLS123", "status": "in_transit", "events": []},
            200,
        )
        response = client.get(
            "/shipments/GLS123/status",
            headers={"X-Username": "user", "X-Password": "pass"},
        )
        assert response.status_code == 200
        assert response.json()["waybillNumber"] == "GLS123"

    @patch("src.app.integration.get_tracking_info")
    def test_get_tracking_error_status(self, mock_tracking, client: TestClient):
        mock_tracking.return_value = ("Not found", 404)
        response = client.get(
            "/shipments/INVALID/status",
            headers={"X-Username": "user", "X-Password": "pass"},
        )
        assert response.status_code == 404

    @patch("src.app.integration.get_tracking_info")
    def test_get_tracking_exception_returns_500(self, mock_tracking, client: TestClient):
        mock_tracking.side_effect = Exception("Connection error")
        response = client.get(
            "/shipments/GLS123/status",
            headers={"X-Username": "user", "X-Password": "pass"},
        )
        assert response.status_code == 500

    def test_get_tracking_missing_headers_returns_422(self, client: TestClient):
        response = client.get("/shipments/GLS123/status")
        assert response.status_code == 422


class TestRates:
    def test_get_rates_domestic_light_parcel(self, client: TestClient):
        payload = {
            "sender_country_code": "PL",
            "receiver_country_code": "PL",
            "weight": 1.5,
            "length": 20,
            "width": 15,
            "height": 10,
        }
        response = client.post("/rates", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "gls"
        assert len(data["products"]) >= 2
        product_names = [p["name"] for p in data["products"]]
        assert "GLS Business Parcel" in product_names
        assert "GLS ShopDelivery" in product_names

    def test_get_rates_domestic_heavy_parcel_no_guarantee(self, client: TestClient):
        payload = {
            "sender_country_code": "PL",
            "receiver_country_code": "PL",
            "weight": 35.0,
            "length": 60,
            "width": 40,
            "height": 40,
        }
        response = client.post("/rates", json=payload)
        assert response.status_code == 200
        data = response.json()
        product_names = [p["name"] for p in data["products"]]
        assert "GLS 10:00" not in product_names
        assert "GLS 12:00" not in product_names

    def test_get_rates_international(self, client: TestClient):
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
        assert len(data["products"]) == 1
        assert data["products"][0]["name"] == "GLS EuroBusinessParcel"

    @pytest.mark.parametrize(
        "weight,expected_base",
        [
            (1.0, 10.50),
            (3.0, 12.50),
            (7.0, 14.50),
            (15.0, 17.50),
            (25.0, 21.00),
            (35.0, 28.00),
        ],
    )
    def test_domestic_rate_tiers(self, client: TestClient, weight: float, expected_base: float):
        payload = {
            "sender_country_code": "PL",
            "receiver_country_code": "PL",
            "weight": weight,
            "length": 0,
            "width": 0,
            "height": 0,
        }
        response = client.post("/rates", json=payload)
        data = response.json()
        business_parcel = next(p for p in data["products"] if p["name"] == "GLS Business Parcel")
        assert business_parcel["price"] == expected_base

    def test_get_rates_domestic_includes_guarantee_for_light_parcel(self, client: TestClient):
        payload = {
            "sender_country_code": "PL",
            "receiver_country_code": "PL",
            "weight": 5.0,
            "length": 0,
            "width": 0,
            "height": 0,
        }
        response = client.post("/rates", json=payload)
        data = response.json()
        product_names = [p["name"] for p in data["products"]]
        assert "GLS 10:00" in product_names
        assert "GLS 12:00" in product_names


class TestLabels:
    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_returns_pdf(self, mock_label, client: TestClient):
        mock_label.return_value = (b"%PDF-1.4 fake content", 200)
        payload = {
            "waybill_numbers": ["GLS123"],
            "credentials": {"username": "user", "password": "pass"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_with_external_id(self, mock_label, client: TestClient):
        mock_label.return_value = (b"%PDF-1.4 fake content", 200)
        payload = {
            "waybill_numbers": ["GLS123"],
            "credentials": {"username": "user", "password": "pass"},
            "external_id": "EXT-001",
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 200
        call_args = mock_label.call_args
        assert call_args[0][2] == {"external_id": "EXT-001"}

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_error_status(self, mock_label, client: TestClient):
        mock_label.return_value = ("Label not found", 404)
        payload = {
            "waybill_numbers": ["INVALID"],
            "credentials": {"username": "user", "password": "pass"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 404

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_exception_returns_500(self, mock_label, client: TestClient):
        mock_label.side_effect = Exception("PDF error")
        payload = {
            "waybill_numbers": ["GLS123"],
            "credentials": {"username": "user", "password": "pass"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 500

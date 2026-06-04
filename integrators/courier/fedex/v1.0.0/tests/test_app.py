"""Tests for FedEx integrator — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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
        assert data["system"] == "fedex"

    def test_readiness_returns_healthy(self, client: TestClient):
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["api_reachable"] == "ok"


class TestCreateShipment:
    @patch("src.app.integration.create_order", new_callable=AsyncMock)
    def test_create_shipment_success(self, mock_create, client: TestClient):
        mock_create.return_value = (
            {"trackingNumber": "FX123456789", "status": "created"},
            201,
        )
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "command": {"shipper": {}, "receiver": {}},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201
        assert response.json()["trackingNumber"] == "FX123456789"

    @patch("src.app.integration.create_order", new_callable=AsyncMock)
    def test_create_shipment_returns_error_status(self, mock_create, client: TestClient):
        mock_create.return_value = ({"error": "Invalid address"}, 400)
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "command": {},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400

    @patch("src.app.integration.create_order", new_callable=AsyncMock)
    def test_create_shipment_exception_returns_400(self, mock_create, client: TestClient):
        mock_create.side_effect = Exception("Connection timeout")
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "command": {},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400


class TestCancelShipment:
    @patch("src.app.integration.delete_order", new_callable=AsyncMock)
    def test_cancel_shipment_success(self, mock_delete, client: TestClient):
        mock_delete.return_value = ({"status": "cancelled"}, 200)
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "extras": {},
        }
        response = client.request("DELETE", "/shipments/ORD-123", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    @patch("src.app.integration.delete_order", new_callable=AsyncMock)
    def test_cancel_shipment_exception_returns_400(self, mock_delete, client: TestClient):
        mock_delete.side_effect = Exception("Not found")
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "extras": {},
        }
        response = client.request("DELETE", "/shipments/ORD-123", json=payload)
        assert response.status_code == 400


class TestLabels:
    @patch("src.app.FedexIntegration.get_tracking_info")
    def test_get_label_returns_tracking_info(self, mock_tracking, client: TestClient):
        mock_tracking.return_value = (
            {"trackingNumber": "FX123", "status": "delivered"},
            200,
        )
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "waybill_numbers": ["FX123"],
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 200
        assert response.json()["trackingNumber"] == "FX123"

    @patch("src.app.FedexIntegration.get_tracking_info")
    def test_get_label_exception_returns_400(self, mock_tracking, client: TestClient):
        mock_tracking.side_effect = Exception("Tracking failed")
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "waybill_numbers": ["INVALID"],
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 400


class TestRates:
    @patch("src.app.integration.get_rates", new_callable=AsyncMock)
    def test_get_rates_success(self, mock_rates, client: TestClient):
        mock_rates.return_value = (
            {
                "products": [{"name": "FedEx Priority", "price": 45.0, "currency": "PLN"}],
                "source": "fedex",
            },
            200,
        )
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "sender_postal_code": "00-001",
            "receiver_postal_code": "30-001",
            "weight": 5.0,
        }
        response = client.post("/rates", json=payload)
        assert response.status_code == 200

    @patch("src.app.integration.get_rates", new_callable=AsyncMock)
    def test_get_rates_non_200_returns_standardized_error(self, mock_rates, client: TestClient):
        mock_rates.return_value = ("Rate lookup failed", 500)
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "weight": 5.0,
        }
        response = client.post("/rates", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "fedex"
        assert "error" in data["raw"]

    @patch("src.app.integration.get_rates", new_callable=AsyncMock)
    def test_get_rates_exception_returns_standardized_error(self, mock_rates, client: TestClient):
        mock_rates.side_effect = Exception("Timeout")
        payload = {"weight": 5.0}
        response = client.post("/rates", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "fedex"
        assert "error" in data["raw"]


class TestPoints:
    @patch("src.app.integration.get_points", new_callable=AsyncMock)
    def test_get_points_success(self, mock_points, client: TestClient):
        mock_points.return_value = (
            [{"id": "P1", "name": "FedEx Point", "city": "Warszawa"}],
            200,
        )
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "city": "Warszawa",
            "postcode": "00-001",
        }
        response = client.post("/points", json=payload)
        assert response.status_code == 200

    @patch("src.app.integration.get_points", new_callable=AsyncMock)
    def test_get_points_exception_returns_400(self, mock_points, client: TestClient):
        mock_points.side_effect = Exception("Service unavailable")
        payload = {
            "credentials": {"client_id": "cid", "client_secret": "csecret"},
            "city": "Warszawa",
        }
        response = client.post("/points", json=payload)
        assert response.status_code == 400


class TestTracking:
    @patch("src.app.FedexIntegration.get_tracking_info")
    def test_get_tracking_success(self, mock_tracking, client: TestClient):
        mock_tracking.return_value = (
            {"trackingNumber": "FX123", "status": "in_transit"},
            200,
        )
        response = client.get("/tracking/FX123")
        assert response.status_code == 200
        assert response.json()["trackingNumber"] == "FX123"

    @patch("src.app.FedexIntegration.get_tracking_info")
    def test_get_tracking_not_found(self, mock_tracking, client: TestClient):
        mock_tracking.return_value = ({"error": "Not found"}, 404)
        response = client.get("/tracking/INVALID")
        assert response.status_code == 404

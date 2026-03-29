"""Tests for FedEx PL integrator — FastAPI endpoints."""

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
        assert data["system"] == "fedexpl"

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
    def test_create_shipment_success(self, mock_create, client: TestClient):
        mock_create.return_value = (
            {"waybillNumber": "FXPL123", "status": "created"},
            201,
        )
        payload = {
            "credentials": {"api_key": "key", "client_id": "cid"},
            "command": {
                "shipper": {"first_name": "Jan", "city": "Warszawa"},
                "receiver": {"first_name": "Anna", "city": "Kraków"},
                "parcels": [{"weight": 5.0}],
            },
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201
        assert response.json()["waybillNumber"] == "FXPL123"

    @patch("src.app.integration.create_order")
    def test_create_shipment_error_status(self, mock_create, client: TestClient):
        mock_create.return_value = ({"error": "Invalid address"}, 400)
        payload = {
            "credentials": {"api_key": "key", "client_id": "cid"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400

    @patch("src.app.integration.create_order")
    def test_create_shipment_exception_returns_500(self, mock_create, client: TestClient):
        mock_create.side_effect = Exception("SOAP fault")
        payload = {
            "credentials": {"api_key": "key", "client_id": "cid"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 500


class TestGetStatus:
    @patch("src.app.integration.get_order_status")
    def test_get_status_success(self, mock_status, client: TestClient):
        mock_status.return_value = ("delivered", 200)
        response = client.request(
            "GET",
            "/shipments/FXPL123/status",
            json={"api_key": "key", "client_id": "cid"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "delivered"

    @patch("src.app.integration.get_order_status")
    def test_get_status_exception_returns_500(self, mock_status, client: TestClient):
        mock_status.side_effect = Exception("SOAP timeout")
        response = client.request(
            "GET",
            "/shipments/FXPL123/status",
            json={"api_key": "key", "client_id": "cid"},
        )
        assert response.status_code == 500


class TestLabels:
    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_returns_pdf(self, mock_label, client: TestClient):
        mock_label.return_value = (b"%PDF-1.4 fake", 200)
        payload = {
            "credentials": {"api_key": "key", "client_id": "cid"},
            "waybill_numbers": ["FXPL123"],
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_non_200_returns_error_json(self, mock_label, client: TestClient):
        mock_label.return_value = ("Label not found", 404)
        payload = {
            "credentials": {"api_key": "key", "client_id": "cid"},
            "waybill_numbers": ["INVALID"],
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 404
        assert "error" in response.json()

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_exception_returns_500(self, mock_label, client: TestClient):
        mock_label.side_effect = Exception("PDF generation failed")
        payload = {
            "credentials": {"api_key": "key", "client_id": "cid"},
            "waybill_numbers": ["FXPL123"],
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 500

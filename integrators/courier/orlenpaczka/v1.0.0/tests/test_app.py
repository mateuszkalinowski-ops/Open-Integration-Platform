"""Tests for Orlen Paczka integrator — FastAPI endpoints."""

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
        assert data["system"] == "orlenpaczka"

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
    def test_create_shipment_success_dict(self, mock_create, client: TestClient):
        mock_create.return_value = (
            {"id": "OP123", "waybill_number": "ORLEN-456"},
            201,
        )
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "command": {
                "shipper": {"first_name": "Jan", "city": "Warszawa"},
                "receiver": {"first_name": "Anna", "city": "Kraków"},
                "parcels": [{"weight": 3.0}],
            },
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201
        assert response.json()["waybill_number"] == "ORLEN-456"

    @patch("src.app.integration.create_order")
    def test_create_shipment_success_model(self, mock_create, client: TestClient):
        result_mock = MagicMock()
        result_mock.model_dump.return_value = {"id": "OP123", "waybill_number": "ORLEN-456"}
        mock_create.return_value = (result_mock, 201)
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201

    @patch("src.app.integration.create_order")
    def test_create_shipment_error_status(self, mock_create, client: TestClient):
        mock_create.return_value = ("Validation error", 400)
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400

    @patch("src.app.integration.create_order")
    def test_create_shipment_exception(self, mock_create, client: TestClient):
        mock_create.side_effect = Exception("Connection error")
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400


class TestGetStatus:
    @patch("src.app.integration.get_order_status")
    def test_get_status_success(self, mock_status, client: TestClient):
        mock_status.return_value = ("delivered", 200)
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "order_id": "OP123",
        }
        response = client.post("/shipments/status", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "delivered"

    @patch("src.app.integration.get_order_status")
    def test_get_status_error(self, mock_status, client: TestClient):
        mock_status.return_value = ("Not found", 404)
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "order_id": "INVALID",
        }
        response = client.post("/shipments/status", json=payload)
        assert response.status_code == 404

    @patch("src.app.integration.get_order_status")
    def test_get_status_exception(self, mock_status, client: TestClient):
        mock_status.side_effect = Exception("Timeout")
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "order_id": "OP123",
        }
        response = client.post("/shipments/status", json=payload)
        assert response.status_code == 400


class TestTracking:
    @patch("src.app.integration.get_tracking_info")
    def test_get_tracking_success(self, mock_tracking, client: TestClient):
        result_mock = MagicMock()
        result_mock.model_dump.return_value = {
            "tracking_number": "ORLEN-456",
            "tracking_url": "https://tracking.orlenpaczka.pl/ORLEN-456",
        }
        mock_tracking.return_value = (result_mock, 200)
        response = client.get("/shipments/OP123/tracking")
        assert response.status_code == 200
        data = response.json()
        assert data["tracking_number"] == "ORLEN-456"
        assert "tracking_url" in data


class TestLabels:
    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_returns_pdf(self, mock_label, client: TestClient):
        mock_label.return_value = (b"%PDF-1.4 fake", 200)
        payload = {
            "waybill_numbers": ["ORLEN-456"],
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_error_status(self, mock_label, client: TestClient):
        mock_label.return_value = ("Label not found", 404)
        payload = {
            "waybill_numbers": ["INVALID"],
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 404

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_exception(self, mock_label, client: TestClient):
        mock_label.side_effect = Exception("PDF error")
        payload = {
            "waybill_numbers": ["ORLEN-456"],
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 400


class TestDeleteShipment:
    @patch("src.app.integration.delete_order")
    def test_delete_success(self, mock_delete, client: TestClient):
        mock_delete.return_value = ({"message": "Shipment cancelled"}, 200)
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "order_id": "OP123",
        }
        response = client.post("/shipments/delete", json=payload)
        assert response.status_code == 200

    @patch("src.app.integration.delete_order")
    def test_delete_error_status(self, mock_delete, client: TestClient):
        mock_delete.return_value = ("Cannot delete", 400)
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "order_id": "OP123",
        }
        response = client.post("/shipments/delete", json=payload)
        assert response.status_code == 400

    @patch("src.app.integration.delete_order")
    def test_delete_exception(self, mock_delete, client: TestClient):
        mock_delete.side_effect = Exception("Service error")
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
            "order_id": "OP123",
        }
        response = client.post("/shipments/delete", json=payload)
        assert response.status_code == 400


class TestGetPoints:
    @patch("src.app.integration.get_points")
    def test_get_points_success(self, mock_points, client: TestClient):
        mock_points.return_value = (
            [{"id": "P1", "name": "Orlen Station", "city": "Warszawa"}],
            200,
        )
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
        }
        response = client.post("/points", json=payload)
        assert response.status_code == 200

    @patch("src.app.integration.get_points")
    def test_get_points_error_status(self, mock_points, client: TestClient):
        mock_points.return_value = ("Service unavailable", 503)
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
        }
        response = client.post("/points", json=payload)
        assert response.status_code == 503

    @patch("src.app.integration.get_points")
    def test_get_points_exception(self, mock_points, client: TestClient):
        mock_points.side_effect = Exception("Connection error")
        payload = {
            "credentials": {"partner_id": "pid", "partner_key": "pkey"},
        }
        response = client.post("/points", json=payload)
        assert response.status_code == 400

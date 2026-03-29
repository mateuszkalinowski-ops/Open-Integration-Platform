"""Tests for Geis integrator — FastAPI endpoints."""

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
        assert data["system"] == "geis"

    @patch("src.app.integration")
    def test_readiness_healthy(self, mock_integration, client: TestClient):
        mock_integration.client = MagicMock()
        mock_integration.check_healthy.return_value = True
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["soap_client"] == "ok"
        assert data["checks"]["geis_service"] == "ok"

    @patch("src.app.integration")
    def test_readiness_degraded_no_client(self, mock_integration, client: TestClient):
        mock_integration.client = None
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["soap_client"] == "unavailable"

    @patch("src.app.integration")
    def test_readiness_degraded_unhealthy_service(self, mock_integration, client: TestClient):
        mock_integration.client = MagicMock()
        mock_integration.check_healthy.return_value = False
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["geis_service"] == "unhealthy"


class TestCreateShipment:
    @patch("src.app.integration.create_order")
    def test_create_shipment_success_dict(self, mock_create, client: TestClient):
        mock_create.return_value = (
            {"id": "G123", "waybill_number": "GEIS-456"},
            201,
        )
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "command": {
                "shipper": {"first_name": "Jan", "city": "Warszawa"},
                "receiver": {"first_name": "Anna", "city": "Kraków"},
                "parcels": [{"weight": 5.0}],
            },
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201
        assert response.json()["waybill_number"] == "GEIS-456"

    @patch("src.app.integration.create_order")
    def test_create_shipment_success_model(self, mock_create, client: TestClient):
        result_mock = MagicMock()
        result_mock.model_dump.return_value = {"id": "G123", "waybill_number": "GEIS-456"}
        mock_create.return_value = (result_mock, 201)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201
        assert response.json()["waybill_number"] == "GEIS-456"

    @patch("src.app.integration.create_order")
    def test_create_shipment_error_status(self, mock_create, client: TestClient):
        mock_create.return_value = ("Validation error", 400)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400

    @patch("src.app.integration.create_order")
    def test_create_shipment_exception(self, mock_create, client: TestClient):
        mock_create.side_effect = Exception("SOAP fault")
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "command": {"shipper": {}, "receiver": {}, "parcels": []},
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 400


class TestGetStatus:
    @patch("src.app.integration.get_order_status")
    def test_get_status_success(self, mock_status, client: TestClient):
        mock_status.return_value = ("delivered", 200)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "GEIS-456",
        }
        response = client.post("/shipments/status", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "delivered"

    @patch("src.app.integration.get_order_status")
    def test_get_status_error(self, mock_status, client: TestClient):
        mock_status.return_value = ("Not found", 404)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "INVALID",
        }
        response = client.post("/shipments/status", json=payload)
        assert response.status_code == 404

    @patch("src.app.integration.get_order_status")
    def test_get_status_exception(self, mock_status, client: TestClient):
        mock_status.side_effect = Exception("Timeout")
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "GEIS-456",
        }
        response = client.post("/shipments/status", json=payload)
        assert response.status_code == 400


class TestGetOrderDetail:
    @patch("src.app.integration.get_order")
    def test_get_order_detail_success(self, mock_order, client: TestClient):
        mock_order.return_value = (
            {"id": "G123", "waybill_number": "GEIS-456", "status": "in_transit"},
            200,
        )
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "GEIS-456",
        }
        response = client.post("/shipments/detail", json=payload)
        assert response.status_code == 200
        assert response.json()["waybill_number"] == "GEIS-456"

    @patch("src.app.integration.get_order")
    def test_get_order_detail_error(self, mock_order, client: TestClient):
        mock_order.return_value = ("Order not found", 404)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "INVALID",
        }
        response = client.post("/shipments/detail", json=payload)
        assert response.status_code == 404


class TestLabels:
    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_returns_pdf(self, mock_label, client: TestClient):
        mock_label.return_value = (b"%PDF-1.4 fake", 200)
        payload = {
            "waybill_numbers": ["GEIS-456"],
            "credentials": {"customer_code": "CC01", "password": "pass"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_error_status(self, mock_label, client: TestClient):
        mock_label.return_value = ("Label error", 500)
        payload = {
            "waybill_numbers": ["INVALID"],
            "credentials": {"customer_code": "CC01", "password": "pass"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 500

    @patch("src.app.integration.get_waybill_label_bytes")
    def test_get_label_exception(self, mock_label, client: TestClient):
        mock_label.side_effect = Exception("PDF error")
        payload = {
            "waybill_numbers": ["GEIS-456"],
            "credentials": {"customer_code": "CC01", "password": "pass"},
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 400


class TestDeleteShipment:
    @patch("src.app.integration.delete_order")
    def test_delete_success(self, mock_delete, client: TestClient):
        mock_delete.return_value = ({"deleted": True}, 200)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "GEIS-456",
        }
        response = client.post("/shipments/delete", json=payload)
        assert response.status_code == 200
        assert response.json()["deleted"] is True

    @patch("src.app.integration.delete_order")
    def test_delete_error_status(self, mock_delete, client: TestClient):
        mock_delete.return_value = ("Cannot delete", 400)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "GEIS-456",
        }
        response = client.post("/shipments/delete", json=payload)
        assert response.status_code == 400

    @patch("src.app.integration.delete_order")
    def test_delete_exception(self, mock_delete, client: TestClient):
        mock_delete.side_effect = Exception("Service error")
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "GEIS-456",
        }
        response = client.post("/shipments/delete", json=payload)
        assert response.status_code == 400


class TestAssignRange:
    @patch("src.app.integration.assign_range")
    def test_assign_range_success(self, mock_range, client: TestClient):
        mock_range.return_value = ((100, 200), 200)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "dummy",
        }
        response = client.post("/shipments/assign-range", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["range_low"] == 100
        assert data["range_high"] == 200

    @patch("src.app.integration.assign_range")
    def test_assign_range_error(self, mock_range, client: TestClient):
        mock_range.return_value = ("No ranges available", 400)
        payload = {
            "credentials": {"customer_code": "CC01", "password": "pass"},
            "waybill_number": "dummy",
        }
        response = client.post("/shipments/assign-range", json=payload)
        assert response.status_code == 400

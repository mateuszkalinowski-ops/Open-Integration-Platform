"""Tests for Raben Group integrator — FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_healthy(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["system"] == "raben"

    def test_readiness_returns_healthy(self, client: TestClient):
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["api_reachable"] == "ok"


# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------


class TestCreateShipment:
    @patch("src.app.integration.create_order", new_callable=AsyncMock)
    def test_create_shipment_returns_201(self, mock_create, client: TestClient):
        mock_create.return_value = (
            {
                "orderId": "ORD-123",
                "waybillNumber": "RAB-456",
                "status": "created",
                "serviceType": "cargo_classic",
                "createdAt": "2026-02-22T10:00:00Z",
            },
            201,
        )
        payload = {
            "credentials": {"username": "test", "password": "test123"},
            "sender": {
                "companyName": "Sender Co",
                "contactPerson": "Jan Kowalski",
                "phone": "+48123456789",
                "street": "Testowa 1",
                "city": "Warszawa",
                "postalCode": "00-001",
                "countryCode": "PL",
            },
            "receiver": {
                "companyName": "Receiver Co",
                "contactPerson": "Anna Nowak",
                "phone": "+48987654321",
                "street": "Odbiorcza 2",
                "city": "Krakow",
                "postalCode": "30-001",
                "countryCode": "PL",
            },
            "packages": [
                {
                    "packageType": "pallet",
                    "quantity": 1,
                    "weight": 500.0,
                    "dimensions": {"length": 120, "width": 80, "height": 100},
                },
            ],
            "serviceType": "cargo_classic",
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["orderId"] == "ORD-123"
        assert data["waybillNumber"] == "RAB-456"

    @patch("src.app.integration.create_order", new_callable=AsyncMock)
    def test_create_shipment_returns_error_on_invalid_credentials(self, mock_create, client: TestClient):
        mock_create.return_value = ("Invalid credentials", 401)
        payload = {
            "credentials": {"username": "bad", "password": "bad"},
            "sender": {
                "companyName": "S",
                "contactPerson": "J",
                "phone": "1",
                "street": "S",
                "city": "W",
                "postalCode": "00-001",
                "countryCode": "PL",
            },
            "receiver": {
                "companyName": "R",
                "contactPerson": "A",
                "phone": "2",
                "street": "R",
                "city": "K",
                "postalCode": "30-001",
                "countryCode": "PL",
            },
            "packages": [{"weight": 100.0}],
        }
        response = client.post("/shipments", json=payload)
        assert response.status_code == 401


class TestGetShipment:
    @patch("src.app.integration.get_order", new_callable=AsyncMock)
    def test_get_shipment_returns_order(self, mock_get, client: TestClient):
        mock_get.return_value = (
            {"orderId": "ORD-123", "waybillNumber": "RAB-456", "status": "in_transit"},
            200,
        )
        response = client.get("/shipments/RAB-456", headers={"X-Username": "test", "X-Password": "test123"})
        assert response.status_code == 200
        assert response.json()["waybillNumber"] == "RAB-456"


class TestCancelShipment:
    @patch("src.app.integration.cancel_order", new_callable=AsyncMock)
    def test_cancel_shipment_returns_success(self, mock_cancel, client: TestClient):
        mock_cancel.return_value = ({"status": "cancelled"}, 200)
        response = client.put("/shipments/RAB-456/cancel", headers={"X-Username": "test", "X-Password": "test123"})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------


class TestTracking:
    @patch("src.app.integration.get_tracking", new_callable=AsyncMock)
    def test_get_tracking_returns_events(self, mock_tracking, client: TestClient):
        mock_tracking.return_value = (
            {
                "waybillNumber": "RAB-456",
                "status": "in_transit",
                "events": [
                    {"timestamp": "2026-02-22T08:00:00Z", "status": "picked_up", "description": "Shipment picked up"},
                    {
                        "timestamp": "2026-02-22T10:00:00Z",
                        "status": "in_transit",
                        "description": "In transit to terminal",
                    },
                ],
                "eta": {"etaFrom": "2026-02-23T08:00:00Z", "etaTo": "2026-02-23T10:00:00Z"},
            },
            200,
        )
        response = client.get("/tracking/RAB-456", headers={"X-Username": "test", "X-Password": "test123"})
        assert response.status_code == 200
        data = response.json()
        assert data["waybillNumber"] == "RAB-456"
        assert len(data["events"]) == 2

    @patch("src.app.integration.get_shipment_status", new_callable=AsyncMock)
    def test_get_status_returns_current_status(self, mock_status, client: TestClient):
        mock_status.return_value = (
            {
                "waybillNumber": "RAB-456",
                "status": "out_for_delivery",
                "statusDescription": "Shipment out for delivery",
                "eta": {"etaFrom": "2026-02-22T14:00:00Z", "etaTo": "2026-02-22T16:00:00Z"},
            },
            200,
        )
        response = client.get("/shipments/RAB-456/status", headers={"X-Username": "test", "X-Password": "test123"})
        assert response.status_code == 200
        assert response.json()["status"] == "out_for_delivery"

    @patch("src.app.integration.get_eta", new_callable=AsyncMock)
    def test_get_eta_returns_eta_info(self, mock_eta, client: TestClient):
        mock_eta.return_value = (
            {"etaFrom": "2026-02-23T08:00:00Z", "etaTo": "2026-02-23T10:00:00Z"},
            200,
        )
        response = client.get("/shipments/RAB-456/eta", headers={"X-Username": "test", "X-Password": "test123"})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------


class TestLabels:
    @patch("src.app.integration.get_label", new_callable=AsyncMock)
    def test_get_label_returns_pdf(self, mock_label, client: TestClient):
        mock_label.return_value = (b"%PDF-1.4 fake content", 200)
        payload = {
            "credentials": {"username": "test", "password": "test123"},
            "waybillNumber": "RAB-456",
            "format": "pdf",
        }
        response = client.post("/labels", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------


class TestClaims:
    @patch("src.app.integration.create_claim", new_callable=AsyncMock)
    def test_create_claim_returns_201(self, mock_claim, client: TestClient):
        mock_claim.return_value = (
            {
                "claimId": "CLM-789",
                "waybillNumber": "RAB-456",
                "claimType": "damage",
                "status": "submitted",
                "createdAt": "2026-02-22T10:00:00Z",
            },
            201,
        )
        payload = {
            "credentials": {"username": "test", "password": "test123"},
            "waybillNumber": "RAB-456",
            "claimType": "damage",
            "description": "Package was damaged during transport",
            "contactEmail": "user@example.com",
        }
        response = client.post("/claims", json=payload)
        assert response.status_code == 201
        assert response.json()["claimId"] == "CLM-789"


# ---------------------------------------------------------------------------
# Delivery confirmation (PCD)
# ---------------------------------------------------------------------------


class TestDeliveryConfirmation:
    @patch("src.app.integration.get_delivery_confirmation", new_callable=AsyncMock)
    def test_get_delivery_confirmation_returns_pcd(self, mock_pcd, client: TestClient):
        mock_pcd.return_value = (
            {
                "waybillNumber": "RAB-456",
                "deliveredAt": "2026-02-22T14:30:00Z",
                "deliveryLocation": "Warehouse dock 3",
                "gpsLatitude": 52.2297,
                "gpsLongitude": 21.0122,
                "vehicleRegistration": "WA 12345",
                "photos": ["https://example.com/pcd/photo1.jpg", "https://example.com/pcd/photo2.jpg"],
                "documentUrl": "https://example.com/pcd/doc.pdf",
            },
            200,
        )
        response = client.get(
            "/deliveries/RAB-456/confirmation", headers={"X-Username": "test", "X-Password": "test123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["waybillNumber"] == "RAB-456"
        assert len(data["photos"]) == 2

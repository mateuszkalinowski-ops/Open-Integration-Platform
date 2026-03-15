"""Tests for Raben Group integrator — business logic layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from src.integration import RabenIntegration, _map_status
from src.schemas import (
    ClaimType,
    CreateShipmentRequest,
    Package,
    RabenCredentials,
    ShipmentParty,
    ShipmentStatus,
)


class TestStatusMapping:
    @pytest.mark.parametrize(
        "raw_status,expected",
        [
            ("new", ShipmentStatus.CREATED),
            ("registered", ShipmentStatus.CREATED),
            ("accepted", ShipmentStatus.CREATED),
            ("picked_up", ShipmentStatus.PICKED_UP),
            ("collected", ShipmentStatus.PICKED_UP),
            ("in_transit", ShipmentStatus.IN_TRANSIT),
            ("hub_scan", ShipmentStatus.IN_TRANSIT),
            ("at_terminal", ShipmentStatus.AT_TERMINAL),
            ("cross_dock", ShipmentStatus.AT_TERMINAL),
            ("out_for_delivery", ShipmentStatus.OUT_FOR_DELIVERY),
            ("on_vehicle", ShipmentStatus.OUT_FOR_DELIVERY),
            ("delivered", ShipmentStatus.DELIVERED),
            ("pcd_confirmed", ShipmentStatus.DELIVERED),
            ("cancelled", ShipmentStatus.CANCELLED),
            ("exception", ShipmentStatus.EXCEPTION),
            ("damage", ShipmentStatus.EXCEPTION),
            ("returned", ShipmentStatus.RETURNED),
        ],
    )
    def test_maps_known_statuses(self, raw_status: str, expected: ShipmentStatus):
        assert _map_status(raw_status) == expected

    def test_maps_unknown_status_to_in_transit(self):
        assert _map_status("unknown_status") == ShipmentStatus.IN_TRANSIT

    def test_case_insensitive_mapping(self):
        assert _map_status("DELIVERED") == ShipmentStatus.DELIVERED
        assert _map_status("In_Transit") == ShipmentStatus.IN_TRANSIT


@pytest.fixture
def credentials():
    return RabenCredentials(
        username="test_user",
        password="test_pass",
        access_token="test_token",
    )


@pytest.fixture
def integration():
    return RabenIntegration()


class TestRabenIntegration:
    @pytest.mark.asyncio
    @patch("src.integration.RabenIntegration._ensure_token", new_callable=AsyncMock)
    async def test_create_order_calls_api(self, mock_token, credentials, integration):
        mock_result = {
            "orderId": "ORD-123",
            "waybillNumber": "RAB-456",
            "status": "created",
            "serviceType": "cargo_classic",
            "createdAt": "2026-02-22T10:00:00Z",
        }
        integration._orders.create_transport_order = AsyncMock(return_value=(mock_result, 201))

        request = CreateShipmentRequest(
            credentials=credentials,
            sender=ShipmentParty(
                companyName="Sender",
                contactPerson="Jan",
                phone="1",
                street="S",
                city="W",
                postalCode="00-001",
            ),
            receiver=ShipmentParty(
                companyName="Receiver",
                contactPerson="Anna",
                phone="2",
                street="R",
                city="K",
                postalCode="30-001",
            ),
            packages=[Package(weight=500.0)],
        )
        result, status = await integration.create_order(credentials, request)
        assert status == 201
        assert result["waybillNumber"] == "RAB-456"

    @pytest.mark.asyncio
    @patch("src.integration.RabenIntegration._ensure_token", new_callable=AsyncMock)
    async def test_get_tracking_transforms_response(self, mock_token, credentials, integration):
        mock_raw = {
            "status": "in_transit",
            "events": [
                {"timestamp": "2026-02-22T08:00:00Z", "status": "picked_up", "description": "Picked up"},
                {"timestamp": "2026-02-22T10:00:00Z", "status": "in_transit", "description": "In transit"},
            ],
            "eta": {
                "etaFrom": "2026-02-23T08:00:00Z",
                "etaTo": "2026-02-23T10:00:00Z",
                "lastUpdated": "2026-02-22T10:00:00Z",
            },
        }
        integration._tracking.get_tracking = AsyncMock(return_value=(mock_raw, 200))

        result, status = await integration.get_tracking(credentials, "RAB-456")
        assert status == 200
        assert result["waybillNumber"] == "RAB-456"
        assert result["status"] == "in_transit"
        assert len(result["events"]) == 2
        assert result["eta"]["etaFrom"] == "2026-02-23T08:00:00Z"

    @pytest.mark.asyncio
    @patch("src.integration.RabenIntegration._ensure_token", new_callable=AsyncMock)
    async def test_get_shipment_status_transforms_response(self, mock_token, credentials, integration):
        mock_raw = {
            "status": "out_for_delivery",
            "statusDescription": "Shipment is out for delivery",
            "eta": {
                "etaFrom": "2026-02-22T14:00:00Z",
                "etaTo": "2026-02-22T16:00:00Z",
            },
            "lastEvent": {
                "timestamp": "2026-02-22T12:00:00Z",
                "status": "on_vehicle",
                "description": "Loaded on delivery vehicle",
            },
        }
        integration._tracking.get_shipment_status = AsyncMock(return_value=(mock_raw, 200))

        result, status = await integration.get_shipment_status(credentials, "RAB-456")
        assert status == 200
        assert result["status"] == "out_for_delivery"
        assert result["eta"]["etaFrom"] == "2026-02-22T14:00:00Z"

    @pytest.mark.asyncio
    @patch("src.integration.RabenIntegration._ensure_token", new_callable=AsyncMock)
    async def test_cancel_order_returns_result(self, mock_token, credentials, integration):
        integration._orders.cancel_order = AsyncMock(return_value=({"status": "cancelled"}, 200))
        _result, status = await integration.cancel_order(credentials, "RAB-456")
        assert status == 200

    @pytest.mark.asyncio
    @patch("src.integration.RabenIntegration._ensure_token", new_callable=AsyncMock)
    async def test_create_claim_submits_complaint(self, mock_token, credentials, integration):
        mock_result = {
            "claimId": "CLM-789",
            "waybillNumber": "RAB-456",
            "claimType": "damage",
            "status": "submitted",
            "createdAt": "2026-02-22T10:00:00Z",
        }
        integration._claims.create_claim = AsyncMock(return_value=(mock_result, 201))

        result, status = await integration.create_claim(
            credentials,
            "RAB-456",
            ClaimType.DAMAGE,
            "Package damaged",
            "user@example.com",
        )
        assert status == 201
        assert result["claimId"] == "CLM-789"

    @pytest.mark.asyncio
    @patch("src.integration.RabenIntegration._ensure_token", new_callable=AsyncMock)
    async def test_get_delivery_confirmation_returns_pcd(self, mock_token, credentials, integration):
        mock_result = {
            "waybillNumber": "RAB-456",
            "deliveredAt": "2026-02-22T14:30:00Z",
            "photos": ["url1", "url2", "url3"],
        }
        integration._pcd.get_delivery_confirmation = AsyncMock(return_value=(mock_result, 200))

        result, status = await integration.get_delivery_confirmation(credentials, "RAB-456")
        assert status == 200
        assert len(result["photos"]) == 3

    @pytest.mark.asyncio
    @patch("src.integration.RabenIntegration._ensure_token", new_callable=AsyncMock)
    async def test_get_label_returns_bytes(self, mock_token, credentials, integration):
        integration._labels.get_label = AsyncMock(return_value=(b"%PDF-1.4 fake", 200))
        result, status = await integration.get_label(credentials, "RAB-456", "pdf")
        assert status == 200
        assert isinstance(result, bytes)

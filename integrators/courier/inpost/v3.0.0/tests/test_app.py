"""Tests for InPost International 2025 integrator v3.0.0 — SDK-based connector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.app import InPostConnector, _calculate_inpost_rates


class TestCalculateInpostRates:
    def test_domestic_small_parcel_has_paczkomat_a(self):
        products = _calculate_inpost_rates(
            weight=1.0,
            length=20,
            width=15,
            height=10,
            sender_country="PL",
            receiver_country="PL",
        )
        names = [p.name for p in products]
        assert "InPost Paczkomat (A)" in names

    def test_domestic_includes_courier_options(self):
        products = _calculate_inpost_rates(
            weight=2.0,
            length=30,
            width=20,
            height=15,
            sender_country="PL",
            receiver_country="PL",
        )
        names = [p.name for p in products]
        assert "InPost Kurier Standard" in names
        assert "InPost Kurier Express" in names

    def test_domestic_large_parcel_excludes_paczkomat_a(self):
        products = _calculate_inpost_rates(
            weight=5.0,
            length=50,
            width=40,
            height=45,
            sender_country="PL",
            receiver_country="PL",
        )
        names = [p.name for p in products]
        assert "InPost Paczkomat (A)" not in names

    def test_international_has_standard_and_express(self):
        products = _calculate_inpost_rates(
            weight=5.0,
            length=30,
            width=20,
            height=15,
            sender_country="PL",
            receiver_country="DE",
        )
        names = [p.name for p in products]
        assert "InPost International Standard" in names
        assert "InPost International Express" in names

    def test_international_heavy_parcel_empty(self):
        products = _calculate_inpost_rates(
            weight=35.0,
            length=50,
            width=50,
            height=50,
            sender_country="PL",
            receiver_country="DE",
        )
        assert len(products) == 0

    @pytest.mark.parametrize(
        "weight,max_dim,expected_paczkomat_sizes",
        [
            (1.0, 30, 3),
            (1.0, 50, 2),
            (1.0, 70, 1),
            (26.0, 30, 0),
        ],
    )
    def test_paczkomat_size_availability(self, weight, max_dim, expected_paczkomat_sizes):
        products = _calculate_inpost_rates(
            weight=weight,
            length=max_dim,
            width=15,
            height=10,
            sender_country="PL",
            receiver_country="PL",
        )
        paczkomat_products = [p for p in products if "Paczkomat" in p.name]
        assert len(paczkomat_products) == expected_paczkomat_sizes

    def test_all_products_have_required_fields(self):
        products = _calculate_inpost_rates(
            weight=2.0,
            length=30,
            width=20,
            height=15,
            sender_country="PL",
            receiver_country="PL",
        )
        for product in products:
            assert product.name
            assert product.price > 0
            assert product.currency == "PLN"
            assert product.delivery_days is not None
            assert "source" in product.attributes
            assert product.attributes["source"] == "inpost"


def _make_connector(**overrides):
    conn = object.__new__(InPostConnector)
    conn._integration = MagicMock()
    conn.accounts = {}
    for k, v in overrides.items():
        setattr(conn, k, v)
    return conn


class TestInPostConnectorCreds:
    def test_creds_from_payload_credentials(self):
        connector = _make_connector()
        payload = {
            "credentials": {
                "organization_id": "org-1",
                "client_secret": "sec",
            }
        }
        creds = connector._creds(payload)
        assert creds.organization_id == "org-1"
        assert creds.client_secret == "sec"

    def test_creds_from_account_store(self):
        connector = _make_connector(
            accounts={
                "default": {
                    "organization_id": "stored-org",
                    "client_secret": "stored-sec",
                }
            }
        )
        payload = {}
        creds = connector._creds(payload)
        assert creds.organization_id == "stored-org"
        assert creds.client_secret == "stored-sec"

    def test_creds_with_named_account(self):
        connector = _make_connector(
            accounts={
                "prod": {
                    "organization_id": "prod-org",
                    "client_secret": "prod-sec",
                    "sandbox_mode": False,
                }
            }
        )
        payload = {"account_name": "prod"}
        creds = connector._creds(payload)
        assert creds.organization_id == "prod-org"


class TestInPostConnectorActions:
    @pytest.fixture
    def connector(self):
        return _make_connector()

    @pytest.mark.asyncio
    async def test_get_shipment_status(self, connector):
        connector._integration.get_order_status = AsyncMock(return_value=({"code": "DELIVERED"}, 200))
        result = await connector.get_shipment_status(
            {
                "credentials": {"organization_id": "org-1", "client_secret": "sec"},
                "waybill": "620000000001",
            }
        )
        assert result["status"]["code"] == "DELIVERED"
        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_cancel_shipment(self, connector):
        connector._integration.delete_order = AsyncMock(return_value=({"message": "cancelled"}, 200))
        result = await connector.cancel_shipment(
            {
                "credentials": {"organization_id": "org-1", "client_secret": "sec"},
                "waybill": "620000000001",
            }
        )
        assert result["result"]["message"] == "cancelled"

    @pytest.mark.asyncio
    async def test_get_tracking(self, connector):
        tracking_mock = MagicMock()
        tracking_mock.model_dump.return_value = {
            "tracking_number": "620000000001",
            "tracking_url": "https://inpost.pl/620000000001",
        }
        connector._integration.get_tracking_info = AsyncMock(return_value=(tracking_mock, 200))
        result = await connector.get_tracking(
            {
                "waybill": "620000000001",
            }
        )
        assert result["tracking_number"] == "620000000001"

    @pytest.mark.asyncio
    async def test_get_rates(self, connector):
        result = await connector.get_rates(
            {
                "weight": 2.0,
                "length": 30,
                "width": 20,
                "height": 15,
                "sender_country_code": "PL",
                "receiver_country_code": "PL",
            }
        )
        assert result["source"] == "inpost"
        assert len(result["products"]) > 0

    @pytest.mark.asyncio
    async def test_get_shipment_error(self, connector):
        connector._integration.get_order = AsyncMock(return_value=("Not found", 404))
        result = await connector.get_shipment(
            {
                "credentials": {"organization_id": "org-1", "client_secret": "sec"},
                "tracking_number": "UNKNOWN",
            }
        )
        assert result["error"] == "Not found"
        assert result["status_code"] == 404

    @pytest.mark.asyncio
    async def test_get_label(self, connector):
        connector._integration.get_waybill_label_bytes = AsyncMock(return_value=(b"%PDF-1.4 label", 200))
        result = await connector.get_label(
            {
                "credentials": {"organization_id": "org-1", "client_secret": "sec"},
                "tracking_number": "620000000001",
            }
        )
        assert "label_base64" in result
        assert result["content_type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_get_pickup_points(self, connector):
        connector._integration.get_points = AsyncMock(return_value=({"items": [{"id": "KRA001"}]}, 200))
        result = await connector.get_pickup_points(
            {
                "credentials": {"organization_id": "org-1", "client_secret": "sec"},
                "city": "Krakow",
            }
        )
        assert "items" in result

"""Tests for DHL Courier integrator — Pydantic schemas."""

from __future__ import annotations

import pytest
from src.schemas import (
    CreateShipmentRequest,
    DhlCredentials,
    DhlExtras,
    LabelRequest,
    RateProduct,
    RateRequest,
    StandardizedRateResponse,
)


class TestDhlCredentials:
    def test_create_with_required_fields(self):
        creds = DhlCredentials(username="user", password="pass")
        assert creds.username == "user"
        assert creds.password == "pass"
        assert creds.account_number == ""
        assert creds.sap_number == ""

    def test_create_with_all_fields(self):
        creds = DhlCredentials(
            username="user",
            password="pass",
            account_number="ACC123",
            sap_number="SAP456",
        )
        assert creds.account_number == "ACC123"
        assert creds.sap_number == "SAP456"

    def test_serialization(self):
        creds = DhlCredentials(username="u", password="p")
        data = creds.model_dump()
        assert "username" in data
        assert "password" in data
        assert "account_number" in data
        assert "sap_number" in data


class TestDhlExtras:
    def test_defaults(self):
        extras = DhlExtras()
        assert extras.pickup_date == ""
        assert extras.book_courier is False
        assert extras.insurance is False
        assert extras.insurance_value == 0
        assert extras.return_on_delivery is False
        assert extras.proof_of_delivery is False

    def test_with_values(self):
        extras = DhlExtras(
            pickup_date="2026-03-28",
            pickup_time_from="08:00",
            pickup_time_to="16:00",
            book_courier=True,
            insurance=True,
            insurance_value=5000.0,
        )
        assert extras.pickup_date == "2026-03-28"
        assert extras.book_courier is True
        assert extras.insurance_value == 5000.0


class TestLabelRequest:
    def test_create_label_request(self):
        req = LabelRequest(
            waybill_numbers=["DHL001", "DHL002"],
            credentials=DhlCredentials(username="u", password="p"),
        )
        assert len(req.waybill_numbers) == 2
        assert req.credentials.username == "u"

    def test_serialization(self):
        req = LabelRequest(
            waybill_numbers=["DHL001"],
            credentials=DhlCredentials(username="u", password="p"),
        )
        data = req.model_dump()
        assert data["waybill_numbers"] == ["DHL001"]
        assert "credentials" in data


class TestCreateShipmentRequest:
    def test_create_with_defaults(self):
        req = CreateShipmentRequest(
            credentials=DhlCredentials(username="u", password="p"),
        )
        assert req.command == {}

    def test_create_with_command(self):
        req = CreateShipmentRequest(
            credentials=DhlCredentials(username="u", password="p"),
            command={"sender": {"name": "Test"}},
        )
        assert req.command["sender"]["name"] == "Test"


class TestRateRequest:
    def test_defaults(self):
        req = RateRequest()
        assert req.sender_country_code == "PL"
        assert req.receiver_country_code == "PL"
        assert req.weight == 0
        assert req.credentials is None

    def test_with_values(self):
        creds = DhlCredentials(username="u", password="p")
        req = RateRequest(
            credentials=creds,
            sender_postal_code="00-001",
            receiver_postal_code="30-001",
            weight=5.0,
            length=30,
            width=20,
            height=15,
        )
        assert req.weight == 5.0
        assert req.sender_postal_code == "00-001"


class TestRateProduct:
    def test_create_product(self):
        product = RateProduct(
            name="DHL Parcel Standard",
            price=13.00,
            currency="PLN",
            delivery_days=2,
        )
        assert product.name == "DHL Parcel Standard"
        assert product.price == 13.00
        assert product.delivery_days == 2

    def test_defaults(self):
        product = RateProduct(name="Test", price=10.0)
        assert product.currency == "PLN"
        assert product.delivery_days is None
        assert product.delivery_date == ""
        assert product.attributes == {}

    def test_serialization(self):
        product = RateProduct(
            name="DHL Parcel Standard",
            price=13.00,
            attributes={"source": "dhl", "service": "standard"},
        )
        data = product.model_dump()
        assert data["name"] == "DHL Parcel Standard"
        assert data["attributes"]["source"] == "dhl"


class TestStandardizedRateResponse:
    def test_empty_response(self):
        resp = StandardizedRateResponse(source="dhl")
        assert resp.products == []
        assert resp.source == "dhl"
        assert resp.raw == {}

    def test_with_products(self):
        products = [
            RateProduct(name="Standard", price=13.0),
            RateProduct(name="Express", price=25.0),
        ]
        resp = StandardizedRateResponse(
            products=products,
            source="dhl",
            raw={"method": "pricing_table"},
        )
        assert len(resp.products) == 2
        data = resp.model_dump()
        assert data["source"] == "dhl"
        assert len(data["products"]) == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("username", "testuser"),
        ("password", "testpass"),
        ("account_number", "ACC001"),
        ("sap_number", "SAP001"),
    ],
)
def test_credentials_fields(field, value):
    creds = DhlCredentials(
        username="testuser",
        password="testpass",
        account_number="ACC001",
        sap_number="SAP001",
    )
    assert getattr(creds, field) == value

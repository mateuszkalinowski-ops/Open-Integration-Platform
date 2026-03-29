"""Tests for GLS integrator — Pydantic schemas."""

from __future__ import annotations

from src.schemas import (
    CreateShipmentRequest,
    GlsCredentials,
    LabelRequest,
    Parcel,
    RateProduct,
    RateRequest,
    ShipmentParty,
    StandardizedRateResponse,
)


class TestGlsCredentials:
    def test_create(self):
        creds = GlsCredentials(username="user", password="pass")
        assert creds.username == "user"
        assert creds.password == "pass"

    def test_model_dump(self):
        creds = GlsCredentials(username="user", password="pass")
        data = creds.model_dump()
        assert data["username"] == "user"
        assert data["password"] == "pass"


class TestParcel:
    def test_defaults(self):
        p = Parcel()
        assert p.weight == 0
        assert p.quantity == 1
        assert p.parcel_type == "PACKAGE"
        assert p.length == 0
        assert p.width == 0
        assert p.height == 0

    def test_custom_values(self):
        p = Parcel(weight=10.5, length=30, width=20, height=15, quantity=2)
        assert p.weight == 10.5
        assert p.quantity == 2

    def test_model_dump(self):
        p = Parcel(weight=5.0, quantity=3)
        data = p.model_dump()
        assert data["weight"] == 5.0
        assert data["quantity"] == 3
        assert data["parcel_type"] == "PACKAGE"


class TestShipmentParty:
    def test_defaults(self):
        party = ShipmentParty()
        assert party.first_name == ""
        assert party.last_name == ""
        assert party.country_code == "PL"
        assert party.contact_person == ""

    def test_custom_values(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            company_name="Test Sp. z o.o.",
            city="Warszawa",
            postal_code="00-001",
        )
        assert party.first_name == "Jan"
        assert party.company_name == "Test Sp. z o.o."
        assert party.city == "Warszawa"

    def test_model_dump(self):
        party = ShipmentParty(first_name="Jan", city="Warszawa")
        data = party.model_dump()
        assert data["first_name"] == "Jan"
        assert data["country_code"] == "PL"


class TestCreateShipmentRequest:
    def test_create_with_defaults(self):
        req = CreateShipmentRequest(
            credentials=GlsCredentials(username="u", password="p"),
        )
        assert req.command == {}

    def test_create_with_command(self):
        req = CreateShipmentRequest(
            credentials=GlsCredentials(username="u", password="p"),
            command={"shipper": {"city": "Warszawa"}},
        )
        assert req.command["shipper"]["city"] == "Warszawa"

    def test_model_dump(self):
        req = CreateShipmentRequest(
            credentials=GlsCredentials(username="u", password="p"),
            command={"key": "value"},
        )
        data = req.model_dump()
        assert data["credentials"]["username"] == "u"
        assert data["command"]["key"] == "value"


class TestLabelRequest:
    def test_create_without_external_id(self):
        req = LabelRequest(
            waybill_numbers=["GLS123"],
            credentials=GlsCredentials(username="u", password="p"),
        )
        assert len(req.waybill_numbers) == 1
        assert req.external_id is None

    def test_create_with_external_id(self):
        req = LabelRequest(
            waybill_numbers=["GLS123"],
            credentials=GlsCredentials(username="u", password="p"),
            external_id="EXT-001",
        )
        assert req.external_id == "EXT-001"

    def test_model_dump(self):
        req = LabelRequest(
            waybill_numbers=["GLS123", "GLS456"],
            credentials=GlsCredentials(username="u", password="p"),
        )
        data = req.model_dump()
        assert len(data["waybill_numbers"]) == 2


class TestRateRequest:
    def test_defaults(self):
        req = RateRequest()
        assert req.credentials is None
        assert req.sender_country_code == "PL"
        assert req.receiver_country_code == "PL"
        assert req.weight == 0

    def test_with_values(self):
        req = RateRequest(
            sender_postal_code="00-001",
            receiver_postal_code="30-001",
            weight=5.0,
            length=30,
            width=20,
            height=15,
        )
        assert req.weight == 5.0
        assert req.length == 30

    def test_model_dump(self):
        req = RateRequest(weight=7.5)
        data = req.model_dump()
        assert data["weight"] == 7.5
        assert data["sender_country_code"] == "PL"


class TestRateProduct:
    def test_create_with_required_fields(self):
        p = RateProduct(name="GLS Business", price=12.50)
        assert p.name == "GLS Business"
        assert p.price == 12.50
        assert p.currency == "PLN"
        assert p.delivery_days is None
        assert p.delivery_date == ""

    def test_create_with_all_fields(self):
        p = RateProduct(
            name="GLS 10:00",
            price=24.15,
            currency="EUR",
            delivery_days=1,
            delivery_date="2026-04-01",
            attributes={"service": "guarantee_1000"},
        )
        assert p.delivery_days == 1
        assert p.currency == "EUR"

    def test_model_dump(self):
        p = RateProduct(
            name="GLS 10:00",
            price=24.15,
            attributes={"service": "guarantee_1000"},
        )
        data = p.model_dump()
        assert data["attributes"]["service"] == "guarantee_1000"


class TestStandardizedRateResponse:
    def test_defaults(self):
        resp = StandardizedRateResponse()
        assert resp.products == []
        assert resp.source == ""
        assert resp.raw == {}

    def test_with_products(self):
        resp = StandardizedRateResponse(
            products=[RateProduct(name="GLS Business", price=12.50)],
            source="gls",
            raw={"method": "pricing_table"},
        )
        assert len(resp.products) == 1
        assert resp.source == "gls"

    def test_model_dump(self):
        resp = StandardizedRateResponse(
            products=[RateProduct(name="GLS Business", price=12.50)],
            source="gls",
        )
        data = resp.model_dump()
        assert len(data["products"]) == 1
        assert data["source"] == "gls"

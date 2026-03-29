"""Tests for DPD Courier integrator — Pydantic schemas."""

from __future__ import annotations

import pytest
from src.schemas import (
    CreateShipmentRequest,
    DpdCredentials,
    DpdInfoCredentials,
    LabelRequest,
    Parcel,
    Payment,
    ProtocolRequest,
    RateProduct,
    RateRequest,
    ShipmentParty,
    StandardizedRateResponse,
    StatusRequest,
)


class TestDpdCredentials:
    def test_create_with_required_fields(self):
        creds = DpdCredentials(login="user", password="pass")
        assert creds.login == "user"
        assert creds.password == "pass"
        assert creds.master_fid is None

    def test_create_with_master_fid(self):
        creds = DpdCredentials(login="user", password="pass", master_fid=12345)
        assert creds.master_fid == 12345

    def test_serialization(self):
        creds = DpdCredentials(login="user", password="pass", master_fid=100)
        data = creds.model_dump()
        assert data["login"] == "user"
        assert data["master_fid"] == 100


class TestDpdInfoCredentials:
    def test_create_with_defaults(self):
        creds = DpdInfoCredentials(login="user", password="pass")
        assert creds.channel == ""

    def test_create_with_channel(self):
        creds = DpdInfoCredentials(login="user", password="pass", channel="sms")
        assert creds.channel == "sms"


class TestParcel:
    def test_defaults(self):
        parcel = Parcel()
        assert parcel.weight == 0
        assert parcel.quantity == 1
        assert parcel.parcel_type == "PACKAGE"
        assert parcel.content == ""

    def test_with_values(self):
        parcel = Parcel(
            weight=15.5,
            length=40,
            width=30,
            height=20,
            quantity=2,
            parcel_type="ENVELOPE",
            content="Documents",
        )
        assert parcel.weight == 15.5
        assert parcel.quantity == 2

    def test_serialization(self):
        parcel = Parcel(weight=10, length=30, width=20, height=15)
        data = parcel.model_dump()
        assert data["weight"] == 10
        assert data["length"] == 30


class TestShipmentParty:
    def test_defaults(self):
        party = ShipmentParty()
        assert party.first_name == ""
        assert party.country_code == "PL"
        assert party.email == ""

    def test_with_values(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            company_name="Test Sp. z o.o.",
            street="Testowa",
            building_number="1",
            city="Warszawa",
            postal_code="00-001",
            phone="+48123456789",
            email="jan@test.pl",
        )
        assert party.first_name == "Jan"
        assert party.city == "Warszawa"


class TestPayment:
    def test_defaults(self):
        payment = Payment()
        assert payment.payer_type == "SHIPPER"
        assert payment.payment_method == ""

    def test_with_values(self):
        payment = Payment(payment_method="COD", payer_type="RECEIVER", account_id="ACC001")
        assert payment.payment_method == "COD"
        assert payment.payer_type == "RECEIVER"


class TestCreateShipmentRequest:
    def test_create_with_defaults(self):
        req = CreateShipmentRequest(
            credentials=DpdCredentials(login="u", password="p"),
        )
        assert req.command == {}

    def test_create_with_command(self):
        req = CreateShipmentRequest(
            credentials=DpdCredentials(login="u", password="p"),
            command={"sender": {"name": "Sender"}},
        )
        assert "sender" in req.command


class TestLabelRequest:
    def test_create_without_external_id(self):
        req = LabelRequest(
            waybill_numbers=["DPD001"],
            credentials=DpdCredentials(login="u", password="p"),
        )
        assert req.external_id is None

    def test_create_with_external_id(self):
        req = LabelRequest(
            waybill_numbers=["DPD001", "DPD002"],
            credentials=DpdCredentials(login="u", password="p"),
            external_id="EXT-001",
        )
        assert len(req.waybill_numbers) == 2
        assert req.external_id == "EXT-001"


class TestProtocolRequest:
    def test_defaults(self):
        req = ProtocolRequest(
            waybill_numbers=["DPD001"],
            credentials=DpdCredentials(login="u", password="p"),
        )
        assert req.session_type == "DOMESTIC"

    def test_with_session_type(self):
        req = ProtocolRequest(
            waybill_numbers=["DPD001"],
            credentials=DpdCredentials(login="u", password="p"),
            session_type="INTERNATIONAL",
        )
        assert req.session_type == "INTERNATIONAL"


class TestStatusRequest:
    def test_without_info_credentials(self):
        req = StatusRequest(
            credentials=DpdCredentials(login="u", password="p"),
        )
        assert req.info_credentials is None

    def test_with_info_credentials(self):
        req = StatusRequest(
            credentials=DpdCredentials(login="u", password="p"),
            info_credentials=DpdInfoCredentials(login="u", password="p", channel="email"),
        )
        assert req.info_credentials.channel == "email"


class TestRateRequest:
    def test_defaults(self):
        req = RateRequest()
        assert req.sender_country_code == "PL"
        assert req.receiver_country_code == "PL"
        assert req.weight == 0
        assert req.credentials is None

    def test_with_values(self):
        req = RateRequest(
            weight=10.0,
            length=40,
            width=30,
            height=20,
            sender_postal_code="00-001",
            receiver_postal_code="30-001",
        )
        assert req.weight == 10.0


class TestRateProduct:
    def test_create(self):
        product = RateProduct(name="DPD Classic", price=13.50, delivery_days=2)
        assert product.name == "DPD Classic"
        assert product.currency == "PLN"

    def test_serialization(self):
        product = RateProduct(
            name="DPD 9:30",
            price=25.30,
            attributes={"source": "dpd", "service": "guarantee_0930"},
        )
        data = product.model_dump()
        assert data["attributes"]["source"] == "dpd"


class TestStandardizedRateResponse:
    def test_empty(self):
        resp = StandardizedRateResponse(source="dpd")
        assert resp.products == []

    def test_with_products(self):
        resp = StandardizedRateResponse(
            products=[RateProduct(name="DPD Classic", price=13.50)],
            source="dpd",
            raw={"method": "pricing_table"},
        )
        data = resp.model_dump()
        assert len(data["products"]) == 1
        assert data["raw"]["method"] == "pricing_table"


@pytest.mark.parametrize(
    "field,value",
    [
        ("login", "testlogin"),
        ("password", "testpass"),
        ("master_fid", 999),
    ],
)
def test_dpd_credentials_fields(field, value):
    creds = DpdCredentials(login="testlogin", password="testpass", master_fid=999)
    assert getattr(creds, field) == value

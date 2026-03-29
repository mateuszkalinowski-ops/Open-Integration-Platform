"""Tests for FedEx PL integrator — Pydantic schemas."""

from __future__ import annotations

from src.schemas import (
    Address,
    CreateOrderCommand,
    CreateShipmentRequest,
    FedexPlCredentials,
    LabelRequest,
    Parcel,
)


class TestFedexPlCredentials:
    def test_create_with_required_fields(self):
        creds = FedexPlCredentials(api_key="key", client_id="cid")
        assert creds.api_key == "key"
        assert creds.client_id == "cid"
        assert creds.courier_number == ""
        assert creds.account_number == ""

    def test_create_with_all_fields(self):
        creds = FedexPlCredentials(
            api_key="key",
            client_id="cid",
            courier_number="CN001",
            account_number="AN001",
        )
        assert creds.courier_number == "CN001"
        assert creds.account_number == "AN001"

    def test_model_dump(self):
        creds = FedexPlCredentials(api_key="key", client_id="cid")
        data = creds.model_dump()
        assert "api_key" in data
        assert "client_id" in data
        assert data["courier_number"] == ""


class TestAddress:
    def test_defaults(self):
        addr = Address()
        assert addr.first_name == ""
        assert addr.last_name == ""
        assert addr.country_code == "PL"
        assert addr.email == ""

    def test_custom_values(self):
        addr = Address(
            first_name="Jan",
            last_name="Kowalski",
            city="Warszawa",
            postal_code="00-001",
            phone="+48123456789",
        )
        assert addr.first_name == "Jan"
        assert addr.city == "Warszawa"

    def test_model_dump(self):
        addr = Address(first_name="Jan", city="Warszawa")
        data = addr.model_dump()
        assert data["first_name"] == "Jan"
        assert data["country_code"] == "PL"


class TestParcel:
    def test_defaults(self):
        parcel = Parcel()
        assert parcel.parcel_type == "PACKAGE"
        assert parcel.weight == 0
        assert parcel.length == 0
        assert parcel.width == 0
        assert parcel.height == 0

    def test_custom_values(self):
        parcel = Parcel(weight=5.5, length=30, width=20, height=15)
        assert parcel.weight == 5.5
        assert parcel.length == 30


class TestCreateOrderCommand:
    def test_defaults(self):
        cmd = CreateOrderCommand()
        assert cmd.content == ""
        assert cmd.cod is False
        assert cmd.cod_value == 0
        assert cmd.parcels == []
        assert cmd.shipment_date == ""

    def test_with_data(self):
        cmd = CreateOrderCommand(
            shipper=Address(city="Warszawa"),
            receiver=Address(city="Kraków"),
            parcels=[Parcel(weight=5.0)],
            content="Electronics",
            cod=True,
            cod_value=150.0,
        )
        assert len(cmd.parcels) == 1
        assert cmd.content == "Electronics"
        assert cmd.cod_value == 150.0

    def test_model_dump(self):
        cmd = CreateOrderCommand(content="Books")
        data = cmd.model_dump()
        assert data["content"] == "Books"
        assert "shipper" in data
        assert "receiver" in data
        assert "parcels" in data


class TestCreateShipmentRequest:
    def test_create(self):
        req = CreateShipmentRequest(
            credentials=FedexPlCredentials(api_key="k", client_id="c"),
            command=CreateOrderCommand(),
        )
        assert req.credentials.api_key == "k"
        assert req.command.content == ""

    def test_model_dump(self):
        req = CreateShipmentRequest(
            credentials=FedexPlCredentials(api_key="k", client_id="c"),
            command=CreateOrderCommand(content="Fragile"),
        )
        data = req.model_dump()
        assert data["credentials"]["api_key"] == "k"
        assert data["command"]["content"] == "Fragile"


class TestLabelRequest:
    def test_create(self):
        req = LabelRequest(
            credentials=FedexPlCredentials(api_key="k", client_id="c"),
            waybill_numbers=["WB1", "WB2"],
        )
        assert len(req.waybill_numbers) == 2
        assert req.waybill_numbers[0] == "WB1"

    def test_model_dump(self):
        req = LabelRequest(
            credentials=FedexPlCredentials(api_key="k", client_id="c"),
            waybill_numbers=["WB1"],
        )
        data = req.model_dump()
        assert data["waybill_numbers"] == ["WB1"]

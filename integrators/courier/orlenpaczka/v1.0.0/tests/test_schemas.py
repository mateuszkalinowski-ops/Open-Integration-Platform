"""Tests for Orlen Paczka integrator — Pydantic schemas."""

from __future__ import annotations

from src.schemas import (
    CreateOrderCommand,
    CreateOrderRequest,
    CreateOrderResponse,
    DeleteRequest,
    LabelRequest,
    OrlenPaczkaCredentials,
    OrlenPaczkaExtras,
    Parcel,
    PointsRequest,
    ShipmentParty,
    StatusRequest,
    Tracking,
)


class TestOrlenPaczkaCredentials:
    def test_create(self):
        creds = OrlenPaczkaCredentials(partner_id="pid", partner_key="pkey")
        assert creds.partner_id == "pid"
        assert creds.partner_key == "pkey"

    def test_model_dump(self):
        creds = OrlenPaczkaCredentials(partner_id="pid", partner_key="pkey")
        data = creds.model_dump()
        assert data["partner_id"] == "pid"
        assert data["partner_key"] == "pkey"


class TestOrlenPaczkaExtras:
    def test_defaults(self):
        extras = OrlenPaczkaExtras()
        assert extras.return_pack is False
        assert extras.cod_description == ""
        assert extras.insurance is None
        assert extras.custom_attributes == {}

    def test_custom_values(self):
        extras = OrlenPaczkaExtras(
            return_pack=True,
            cod_description="Payment on delivery",
            insurance=500.0,
            custom_attributes={"priority": "high"},
        )
        assert extras.return_pack is True
        assert extras.insurance == 500.0
        assert extras.custom_attributes["priority"] == "high"

    def test_model_dump(self):
        extras = OrlenPaczkaExtras(insurance=250.0)
        data = extras.model_dump()
        assert data["insurance"] == 250.0
        assert data["return_pack"] is False


class TestParcel:
    def test_defaults(self):
        p = Parcel()
        assert p.parcel_type == "A"
        assert p.quantity == 1
        assert p.weight == 0
        assert p.width == 0
        assert p.height == 0
        assert p.length == 0

    def test_custom_values(self):
        p = Parcel(parcel_type="B", quantity=2, weight=3.5, width=20, height=15, length=30)
        assert p.parcel_type == "B"
        assert p.quantity == 2
        assert p.weight == 3.5

    def test_model_dump(self):
        p = Parcel(weight=5.0, parcel_type="C")
        data = p.model_dump()
        assert data["weight"] == 5.0
        assert data["parcel_type"] == "C"


class TestShipmentParty:
    def test_defaults(self):
        party = ShipmentParty()
        assert party.first_name == ""
        assert party.last_name == ""
        assert party.country_code == "PL"
        assert party.email == ""

    def test_custom_values(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            company_name="Test Sp. z o.o.",
            city="Warszawa",
            postal_code="00-001",
            phone="+48123456789",
        )
        assert party.first_name == "Jan"
        assert party.company_name == "Test Sp. z o.o."
        assert party.city == "Warszawa"

    def test_model_dump(self):
        party = ShipmentParty(first_name="Jan", city="Warszawa")
        data = party.model_dump()
        assert data["first_name"] == "Jan"
        assert data["country_code"] == "PL"


class TestCreateOrderCommand:
    def test_defaults(self):
        cmd = CreateOrderCommand()
        assert cmd.content == ""
        assert cmd.cod is False
        assert cmd.cod_value == 0
        assert cmd.parcels == []
        assert cmd.extras == {}

    def test_with_data(self):
        cmd = CreateOrderCommand(
            shipper=ShipmentParty(city="Warszawa"),
            receiver=ShipmentParty(city="Kraków"),
            parcels=[Parcel(weight=3.0)],
            content="Books",
            cod=True,
            cod_value=49.99,
        )
        assert len(cmd.parcels) == 1
        assert cmd.cod_value == 49.99

    def test_model_dump(self):
        cmd = CreateOrderCommand(content="Fragile")
        data = cmd.model_dump()
        assert data["content"] == "Fragile"
        assert "shipper" in data
        assert "receiver" in data
        assert "parcels" in data


class TestCreateOrderRequest:
    def test_create(self):
        req = CreateOrderRequest(
            credentials=OrlenPaczkaCredentials(partner_id="p", partner_key="k"),
            command=CreateOrderCommand(),
        )
        assert req.credentials.partner_id == "p"
        assert req.command.content == ""

    def test_model_dump(self):
        req = CreateOrderRequest(
            credentials=OrlenPaczkaCredentials(partner_id="p", partner_key="k"),
            command=CreateOrderCommand(content="Electronics"),
        )
        data = req.model_dump()
        assert data["credentials"]["partner_id"] == "p"
        assert data["command"]["content"] == "Electronics"


class TestLabelRequest:
    def test_create(self):
        req = LabelRequest(
            waybill_numbers=["WB1", "WB2"],
            credentials=OrlenPaczkaCredentials(partner_id="p", partner_key="k"),
        )
        assert len(req.waybill_numbers) == 2
        assert req.waybill_numbers[0] == "WB1"


class TestStatusRequest:
    def test_create(self):
        req = StatusRequest(
            credentials=OrlenPaczkaCredentials(partner_id="p", partner_key="k"),
            order_id="OP123",
        )
        assert req.order_id == "OP123"


class TestDeleteRequest:
    def test_create(self):
        req = DeleteRequest(
            credentials=OrlenPaczkaCredentials(partner_id="p", partner_key="k"),
            order_id="OP123",
        )
        assert req.order_id == "OP123"


class TestPointsRequest:
    def test_create(self):
        req = PointsRequest(
            credentials=OrlenPaczkaCredentials(partner_id="p", partner_key="k"),
        )
        assert req.credentials.partner_id == "p"

    def test_model_dump(self):
        req = PointsRequest(
            credentials=OrlenPaczkaCredentials(partner_id="p", partner_key="k"),
        )
        data = req.model_dump()
        assert data["credentials"]["partner_id"] == "p"


class TestCreateOrderResponse:
    def test_create_with_required_fields(self):
        resp = CreateOrderResponse(id="OP123", waybill_number="ORLEN-456")
        assert resp.id == "OP123"
        assert resp.waybill_number == "ORLEN-456"
        assert resp.order_status == "CREATED"
        assert resp.shipper == {}
        assert resp.receiver == {}

    def test_create_with_all_fields(self):
        resp = CreateOrderResponse(
            id="OP123",
            waybill_number="ORLEN-456",
            shipper={"city": "Warszawa"},
            receiver={"city": "Kraków"},
            order_status="CONFIRMED",
        )
        assert resp.order_status == "CONFIRMED"
        assert resp.shipper["city"] == "Warszawa"

    def test_model_dump(self):
        resp = CreateOrderResponse(id="OP123", waybill_number="ORLEN-456")
        data = resp.model_dump()
        assert data["id"] == "OP123"
        assert data["order_status"] == "CREATED"


class TestTracking:
    def test_create(self):
        t = Tracking(
            tracking_number="ORLEN-456",
            tracking_url="https://tracking.orlenpaczka.pl/ORLEN-456",
        )
        assert t.tracking_number == "ORLEN-456"
        assert t.tracking_url.startswith("https://")

    def test_model_dump(self):
        t = Tracking(
            tracking_number="ORLEN-456",
            tracking_url="https://tracking.orlenpaczka.pl/ORLEN-456",
        )
        data = t.model_dump()
        assert data["tracking_number"] == "ORLEN-456"
        assert data["tracking_url"] == "https://tracking.orlenpaczka.pl/ORLEN-456"

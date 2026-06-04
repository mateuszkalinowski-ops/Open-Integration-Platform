"""Tests for Geis integrator — Pydantic schemas."""

from __future__ import annotations

from src.schemas import (
    CreateOrderCommand,
    CreateOrderRequest,
    CreateOrderResponse,
    DeleteRequest,
    GeisCredentials,
    GeisExtras,
    LabelRequest,
    OrderDetailRequest,
    Parcel,
    Payment,
    ShipmentParty,
    StatusRequest,
)


class TestGeisCredentials:
    def test_create_with_required_fields(self):
        creds = GeisCredentials(customer_code="CC01", password="pass")
        assert creds.customer_code == "CC01"
        assert creds.password == "pass"
        assert creds.default_language == "PL"

    def test_custom_language(self):
        creds = GeisCredentials(customer_code="CC01", password="pass", default_language="EN")
        assert creds.default_language == "EN"

    def test_model_dump(self):
        creds = GeisCredentials(customer_code="CC01", password="pass")
        data = creds.model_dump()
        assert data["customer_code"] == "CC01"
        assert data["password"] == "pass"
        assert data["default_language"] == "PL"


class TestGeisExtras:
    def test_defaults(self):
        extras = GeisExtras()
        assert extras.geis_export is True
        assert extras.book_courier is False
        assert extras.insurance is False
        assert extras.insurance_value == 0
        assert extras.insurance_curr == "PLN"
        assert extras.pickup_date == ""
        assert extras.pickup_time_from == ""
        assert extras.pickup_time_to == ""

    def test_custom_values(self):
        extras = GeisExtras(
            geis_export=False,
            book_courier=True,
            insurance=True,
            insurance_value=1000.0,
            pickup_date="2026-03-28",
            pickup_time_from="08:00",
            pickup_time_to="16:00",
        )
        assert extras.book_courier is True
        assert extras.insurance_value == 1000.0
        assert extras.pickup_date == "2026-03-28"

    def test_model_dump(self):
        extras = GeisExtras(insurance=True, insurance_value=500.0)
        data = extras.model_dump()
        assert data["insurance"] is True
        assert data["insurance_value"] == 500.0


class TestParcel:
    def test_defaults(self):
        p = Parcel()
        assert p.parcel_type == "KS"
        assert p.quantity == 1
        assert p.weight == 0
        assert p.width == 0
        assert p.height == 0
        assert p.length == 0

    def test_custom_values(self):
        p = Parcel(parcel_type="PP", quantity=3, weight=15.5, width=40, height=30, length=60)
        assert p.parcel_type == "PP"
        assert p.quantity == 3
        assert p.weight == 15.5

    def test_model_dump(self):
        p = Parcel(weight=10.0, quantity=2)
        data = p.model_dump()
        assert data["weight"] == 10.0
        assert data["parcel_type"] == "KS"


class TestPayment:
    def test_defaults(self):
        pay = Payment()
        assert pay.account_id == ""
        assert pay.payment_method == ""
        assert pay.payer_type == ""

    def test_custom_values(self):
        pay = Payment(account_id="ACC-001", payment_method="CASH", payer_type="SENDER")
        assert pay.account_id == "ACC-001"
        assert pay.payment_method == "CASH"

    def test_model_dump(self):
        pay = Payment(payment_method="TRANSFER")
        data = pay.model_dump()
        assert data["payment_method"] == "TRANSFER"


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
            phone="+48123456789",
            email="jan@test.pl",
        )
        assert party.first_name == "Jan"
        assert party.company_name == "Test Sp. z o.o."
        assert party.email == "jan@test.pl"

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
        assert cmd.cod_curr == "PLN"
        assert cmd.parcels == []
        assert cmd.shipment_date == ""

    def test_with_data(self):
        cmd = CreateOrderCommand(
            shipper=ShipmentParty(city="Warszawa"),
            receiver=ShipmentParty(city="Kraków"),
            parcels=[Parcel(weight=5.0)],
            content="Electronics",
            cod=True,
            cod_value=150.0,
        )
        assert len(cmd.parcels) == 1
        assert cmd.cod is True
        assert cmd.cod_value == 150.0

    def test_model_dump(self):
        cmd = CreateOrderCommand(content="Books", shipment_date="2026-03-28")
        data = cmd.model_dump()
        assert data["content"] == "Books"
        assert data["shipment_date"] == "2026-03-28"
        assert "shipper" in data
        assert "receiver" in data


class TestCreateOrderRequest:
    def test_create(self):
        req = CreateOrderRequest(
            credentials=GeisCredentials(customer_code="CC01", password="p"),
            command=CreateOrderCommand(),
        )
        assert req.credentials.customer_code == "CC01"
        assert req.command.content == ""

    def test_model_dump(self):
        req = CreateOrderRequest(
            credentials=GeisCredentials(customer_code="CC01", password="p"),
            command=CreateOrderCommand(content="Fragile"),
        )
        data = req.model_dump()
        assert data["credentials"]["customer_code"] == "CC01"
        assert data["command"]["content"] == "Fragile"


class TestLabelRequest:
    def test_create(self):
        req = LabelRequest(
            waybill_numbers=["WB1", "WB2"],
            credentials=GeisCredentials(customer_code="CC01", password="p"),
        )
        assert len(req.waybill_numbers) == 2


class TestStatusRequest:
    def test_create(self):
        req = StatusRequest(
            credentials=GeisCredentials(customer_code="CC01", password="p"),
            waybill_number="GEIS-456",
        )
        assert req.waybill_number == "GEIS-456"


class TestDeleteRequest:
    def test_create(self):
        req = DeleteRequest(
            credentials=GeisCredentials(customer_code="CC01", password="p"),
            waybill_number="GEIS-456",
        )
        assert req.waybill_number == "GEIS-456"


class TestOrderDetailRequest:
    def test_create(self):
        req = OrderDetailRequest(
            credentials=GeisCredentials(customer_code="CC01", password="p"),
            waybill_number="GEIS-456",
        )
        assert req.waybill_number == "GEIS-456"


class TestCreateOrderResponse:
    def test_create_with_required_fields(self):
        resp = CreateOrderResponse(id="G123", waybill_number="GEIS-456")
        assert resp.id == "G123"
        assert resp.waybill_number == "GEIS-456"
        assert resp.order_status == "CREATED"
        assert resp.shipper == {}
        assert resp.receiver == {}

    def test_create_with_all_fields(self):
        resp = CreateOrderResponse(
            id="G123",
            waybill_number="GEIS-456",
            shipper={"city": "Warszawa"},
            receiver={"city": "Kraków"},
            order_status="CONFIRMED",
        )
        assert resp.order_status == "CONFIRMED"
        assert resp.shipper["city"] == "Warszawa"

    def test_model_dump(self):
        resp = CreateOrderResponse(id="G123", waybill_number="GEIS-456")
        data = resp.model_dump()
        assert data["id"] == "G123"
        assert data["order_status"] == "CREATED"

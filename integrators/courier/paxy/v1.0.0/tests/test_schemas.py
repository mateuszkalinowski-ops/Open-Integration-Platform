"""Tests for Paxy Pydantic schemas."""

from src.schemas import (
    Address,
    CreateOrderCommand,
    CreateShipmentRequest,
    DeleteRequest,
    LabelRequest,
    Parcel,
    PaxyCredentials,
    StatusRequest,
)


class TestPaxyCredentials:
    def test_create_credentials(self):
        creds = PaxyCredentials(api_key="key123", api_token="tok456")
        assert creds.api_key == "key123"
        assert creds.api_token == "tok456"

    def test_credentials_serialization(self):
        creds = PaxyCredentials(api_key="key", api_token="tok")
        data = creds.model_dump()
        assert data["api_key"] == "key"
        assert data["api_token"] == "tok"


class TestParcel:
    def test_parcel_defaults(self):
        parcel = Parcel()
        assert parcel.weight == 0
        assert parcel.length == 0
        assert parcel.width == 0
        assert parcel.height == 0
        assert parcel.quantity == 1
        assert parcel.parcel_type == "PACKAGE"

    def test_parcel_with_values(self):
        parcel = Parcel(weight=12.5, length=40, width=30, height=20, quantity=3)
        assert parcel.weight == 12.5
        assert parcel.quantity == 3

    def test_parcel_serialization(self):
        parcel = Parcel(weight=7.0, parcel_type="PALLET")
        data = parcel.model_dump()
        assert data["weight"] == 7.0
        assert data["parcel_type"] == "PALLET"


class TestAddress:
    def test_address_defaults(self):
        addr = Address()
        assert addr.first_name == ""
        assert addr.country_code == "PL"

    def test_address_with_values(self):
        addr = Address(
            first_name="Jan",
            last_name="Kowalski",
            company_name="ACME",
            street="Testowa",
            building_number="5",
            city="Poznan",
            postal_code="60-001",
            email="jan@test.pl",
            phone="+48111222333",
        )
        assert addr.first_name == "Jan"
        assert addr.company_name == "ACME"
        assert addr.city == "Poznan"

    def test_address_serialization(self):
        addr = Address(first_name="Anna", city="Gdansk")
        data = addr.model_dump()
        assert "first_name" in data
        assert "country_code" in data
        assert data["country_code"] == "PL"


class TestCreateOrderCommand:
    def test_command_defaults(self):
        cmd = CreateOrderCommand()
        assert cmd.service_name == ""
        assert cmd.cod is False
        assert cmd.cod_value == 0
        assert cmd.parcels == []
        assert cmd.doc_id == ""

    def test_command_with_parcels(self):
        cmd = CreateOrderCommand(
            service_name="EXPRESS",
            content="Fragile items",
            parcels=[Parcel(weight=3.0)],
            shipper=Address(first_name="Jan"),
            receiver=Address(first_name="Anna"),
        )
        assert len(cmd.parcels) == 1
        assert cmd.content == "Fragile items"

    def test_command_serialization(self):
        cmd = CreateOrderCommand(cod=True, cod_value=200.0)
        data = cmd.model_dump()
        assert data["cod"] is True
        assert data["cod_value"] == 200.0


class TestCreateShipmentRequest:
    def test_create_request(self):
        req = CreateShipmentRequest(
            credentials=PaxyCredentials(api_key="k", api_token="t"),
            command=CreateOrderCommand(service_name="STANDARD"),
        )
        assert req.credentials.api_key == "k"
        assert req.command.service_name == "STANDARD"


class TestLabelRequest:
    def test_label_request(self):
        req = LabelRequest(
            credentials=PaxyCredentials(api_key="k", api_token="t"),
            waybill_numbers=["WB001", "WB002"],
        )
        assert len(req.waybill_numbers) == 2


class TestDeleteRequest:
    def test_delete_request(self):
        req = DeleteRequest(
            credentials=PaxyCredentials(api_key="k", api_token="t"),
            waybill_number="WB001",
        )
        assert req.waybill_number == "WB001"


class TestStatusRequest:
    def test_status_request(self):
        req = StatusRequest(
            credentials=PaxyCredentials(api_key="k", api_token="t"),
            waybill_number="WB001",
        )
        assert req.waybill_number == "WB001"
        data = req.model_dump()
        assert "credentials" in data
        assert "waybill_number" in data

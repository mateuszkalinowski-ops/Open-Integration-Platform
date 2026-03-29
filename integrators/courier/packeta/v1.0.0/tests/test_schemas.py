"""Tests for Packeta Pydantic schemas."""

from src.schemas import (
    Address,
    CreateOrderCommand,
    CreateShipmentRequest,
    DeleteRequest,
    LabelRequest,
    PacketaCredentials,
    Parcel,
    StatusRequest,
)


class TestPacketaCredentials:
    def test_create_credentials(self):
        creds = PacketaCredentials(api_password="secret123")
        assert creds.api_password == "secret123"
        assert creds.eshop == ""

    def test_create_credentials_with_eshop(self):
        creds = PacketaCredentials(api_password="secret", eshop="my-shop")
        assert creds.eshop == "my-shop"

    def test_credentials_serialization(self):
        creds = PacketaCredentials(api_password="secret", eshop="shop")
        data = creds.model_dump()
        assert data["api_password"] == "secret"
        assert data["eshop"] == "shop"


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
        parcel = Parcel(weight=5.5, length=30, width=20, height=10, quantity=2)
        assert parcel.weight == 5.5
        assert parcel.quantity == 2

    def test_parcel_serialization(self):
        parcel = Parcel(weight=3.0, parcel_type="ENVELOPE")
        data = parcel.model_dump()
        assert data["weight"] == 3.0
        assert data["parcel_type"] == "ENVELOPE"


class TestAddress:
    def test_address_defaults(self):
        addr = Address()
        assert addr.first_name == ""
        assert addr.country_code == "PL"
        assert addr.email == ""

    def test_address_with_values(self):
        addr = Address(
            first_name="Jan",
            last_name="Kowalski",
            street="Marszalkowska",
            building_number="10",
            city="Warszawa",
            postal_code="00-001",
            country_code="CZ",
            phone="+48123456789",
        )
        assert addr.first_name == "Jan"
        assert addr.city == "Warszawa"
        assert addr.country_code == "CZ"

    def test_address_serialization(self):
        addr = Address(first_name="Anna", city="Krakow")
        data = addr.model_dump()
        assert "first_name" in data
        assert "city" in data
        assert "country_code" in data


class TestCreateOrderCommand:
    def test_command_defaults(self):
        cmd = CreateOrderCommand()
        assert cmd.service_name == ""
        assert cmd.cod is False
        assert cmd.cod_value == 0
        assert cmd.parcels == []

    def test_command_with_parcels(self):
        cmd = CreateOrderCommand(
            service_name="STANDARD",
            content="Books",
            parcels=[Parcel(weight=5.0)],
            shipper=Address(first_name="Jan"),
            receiver=Address(first_name="Anna"),
        )
        assert cmd.service_name == "STANDARD"
        assert len(cmd.parcels) == 1
        assert cmd.shipper.first_name == "Jan"

    def test_command_serialization(self):
        cmd = CreateOrderCommand(cod=True, cod_value=150.0, cod_curr="PLN")
        data = cmd.model_dump()
        assert data["cod"] is True
        assert data["cod_value"] == 150.0


class TestCreateShipmentRequest:
    def test_create_request(self):
        req = CreateShipmentRequest(
            credentials=PacketaCredentials(api_password="pass"),
            command=CreateOrderCommand(service_name="EXPRESS"),
        )
        assert req.credentials.api_password == "pass"
        assert req.command.service_name == "EXPRESS"


class TestLabelRequest:
    def test_label_request(self):
        req = LabelRequest(
            credentials=PacketaCredentials(api_password="pass"),
            waybill_numbers=["Z001", "Z002"],
        )
        assert len(req.waybill_numbers) == 2
        assert req.external_id is None

    def test_label_request_with_external_id(self):
        req = LabelRequest(
            credentials=PacketaCredentials(api_password="pass"),
            waybill_numbers=["Z001"],
            external_id="EXT-1",
        )
        assert req.external_id == "EXT-1"


class TestDeleteRequest:
    def test_delete_request(self):
        req = DeleteRequest(
            credentials=PacketaCredentials(api_password="pass"),
            waybill_number="Z001",
        )
        assert req.waybill_number == "Z001"


class TestStatusRequest:
    def test_status_request(self):
        req = StatusRequest(
            credentials=PacketaCredentials(api_password="pass"),
            waybill_number="Z001",
        )
        assert req.waybill_number == "Z001"
        assert req.credentials.api_password == "pass"

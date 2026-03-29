"""Tests for Suus Pydantic schemas."""

from src.schemas import (
    Address,
    CreateOrderCommand,
    CreateShipmentRequest,
    DeleteRequest,
    LabelRequest,
    Parcel,
    StatusRequest,
    SuusCredentials,
)


class TestSuusCredentials:
    def test_create_credentials(self):
        creds = SuusCredentials(login="user", password="pass")
        assert creds.login == "user"
        assert creds.password == "pass"

    def test_credentials_serialization(self):
        creds = SuusCredentials(login="u", password="p")
        data = creds.model_dump()
        assert data["login"] == "u"
        assert data["password"] == "p"


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
        parcel = Parcel(weight=500.0, length=120, width=80, height=100, quantity=2, parcel_type="PALLET")
        assert parcel.weight == 500.0
        assert parcel.parcel_type == "PALLET"

    def test_parcel_serialization(self):
        parcel = Parcel(weight=3.5)
        data = parcel.model_dump()
        assert data["weight"] == 3.5
        assert "parcel_type" in data


class TestAddress:
    def test_address_defaults(self):
        addr = Address()
        assert addr.first_name == ""
        assert addr.country_code == "PL"

    def test_address_with_values(self):
        addr = Address(
            first_name="Jan",
            last_name="Kowalski",
            company_name="Logistics Co",
            street="Transportowa",
            building_number="10",
            city="Lodz",
            postal_code="90-001",
            country_code="PL",
            email="jan@test.pl",
            phone="+48111222333",
            contact_person="Jan K.",
        )
        assert addr.company_name == "Logistics Co"
        assert addr.contact_person == "Jan K."

    def test_address_serialization(self):
        addr = Address(first_name="Anna", city="Katowice")
        data = addr.model_dump()
        assert "first_name" in data
        assert "country_code" in data
        assert "contact_person" in data


class TestCreateOrderCommand:
    def test_command_defaults(self):
        cmd = CreateOrderCommand()
        assert cmd.service_name == ""
        assert cmd.cod is False
        assert cmd.cod_value == 0
        assert cmd.cod_curr == ""
        assert cmd.parcels == []
        assert cmd.doc_id == ""

    def test_command_with_cod(self):
        cmd = CreateOrderCommand(
            service_name="EXPRESS",
            cod=True,
            cod_value=350.0,
            cod_curr="PLN",
        )
        assert cmd.cod is True
        assert cmd.cod_value == 350.0
        assert cmd.cod_curr == "PLN"

    def test_command_with_parcels_and_addresses(self):
        cmd = CreateOrderCommand(
            parcels=[Parcel(weight=100.0), Parcel(weight=200.0)],
            shipper=Address(first_name="Jan"),
            receiver=Address(first_name="Anna"),
        )
        assert len(cmd.parcels) == 2
        assert cmd.shipper.first_name == "Jan"

    def test_command_serialization(self):
        cmd = CreateOrderCommand(content="Industrial parts", doc_id="DOC-123")
        data = cmd.model_dump()
        assert data["content"] == "Industrial parts"
        assert data["doc_id"] == "DOC-123"


class TestCreateShipmentRequest:
    def test_create_request(self):
        req = CreateShipmentRequest(
            credentials=SuusCredentials(login="u", password="p"),
            command=CreateOrderCommand(service_name="STANDARD"),
        )
        assert req.credentials.login == "u"
        assert req.command.service_name == "STANDARD"


class TestLabelRequest:
    def test_label_request(self):
        req = LabelRequest(
            credentials=SuusCredentials(login="u", password="p"),
            waybill_numbers=["SUUS001", "SUUS002"],
        )
        assert len(req.waybill_numbers) == 2


class TestDeleteRequest:
    def test_delete_request(self):
        req = DeleteRequest(
            credentials=SuusCredentials(login="u", password="p"),
            waybill_number="SUUS001",
        )
        assert req.waybill_number == "SUUS001"


class TestStatusRequest:
    def test_status_request(self):
        req = StatusRequest(
            credentials=SuusCredentials(login="u", password="p"),
            waybill_number="SUUS001",
        )
        assert req.waybill_number == "SUUS001"

    def test_status_request_serialization(self):
        req = StatusRequest(
            credentials=SuusCredentials(login="u", password="p"),
            waybill_number="SUUS999",
        )
        data = req.model_dump()
        assert data["waybill_number"] == "SUUS999"
        assert "credentials" in data

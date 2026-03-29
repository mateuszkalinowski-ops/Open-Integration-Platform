"""Tests for Schenker Pydantic schemas."""

from src.schemas import (
    CreateShipmentRequest,
    DeleteOrderRequest,
    LabelRequest,
    Parcel,
    Payment,
    SchenkerCredentials,
    ShipmentParty,
)


class TestSchenkerCredentials:
    def test_create_credentials_required(self):
        creds = SchenkerCredentials(login="user", password="pass")
        assert creds.login == "user"
        assert creds.password == "pass"
        assert creds.credentials_id == ""
        assert creds.login_ext == ""

    def test_create_credentials_full(self):
        creds = SchenkerCredentials(
            login="user",
            password="pass",
            credentials_id="CRED-001",
            login_ext="ext-user",
        )
        assert creds.credentials_id == "CRED-001"
        assert creds.login_ext == "ext-user"

    def test_credentials_serialization(self):
        creds = SchenkerCredentials(login="u", password="p")
        data = creds.model_dump()
        assert data["login"] == "u"
        assert "credentials_id" in data


class TestShipmentParty:
    def test_party_defaults(self):
        party = ShipmentParty()
        assert party.first_name == ""
        assert party.country_code == "PL"
        assert party.tax_number == ""
        assert party.client_id is None

    def test_party_with_values(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            street="Logistyczna",
            building_number="15",
            city="Warszawa",
            postal_code="00-001",
            tax_number="PL1234567890",
            client_id="CLI-001",
        )
        assert party.first_name == "Jan"
        assert party.tax_number == "PL1234567890"
        assert party.client_id == "CLI-001"

    def test_party_serialization(self):
        party = ShipmentParty(first_name="Anna", city="Wroclaw")
        data = party.model_dump()
        assert "first_name" in data
        assert "country_code" in data
        assert "client_id" in data


class TestParcel:
    def test_parcel_defaults(self):
        parcel = Parcel()
        assert parcel.weight == 0
        assert parcel.quantity == 1
        assert parcel.parcel_type == "PACKAGE"

    def test_parcel_pallet(self):
        parcel = Parcel(weight=800.0, length=120, width=80, height=150, parcel_type="PALLET")
        assert parcel.weight == 800.0
        assert parcel.parcel_type == "PALLET"


class TestPayment:
    def test_payment_defaults(self):
        payment = Payment()
        assert payment.payer_type == "SHIPPER"
        assert payment.payment_method == "BANK_TRANSFER"
        assert payment.account_id == ""

    def test_payment_with_values(self):
        payment = Payment(payer_type="RECEIVER", account_id="ACC-001")
        assert payment.payer_type == "RECEIVER"
        assert payment.account_id == "ACC-001"


class TestCreateShipmentRequest:
    def test_create_request_minimal(self):
        req = CreateShipmentRequest(
            credentials=SchenkerCredentials(login="u", password="p"),
        )
        assert req.service_name == "SYSTEM"
        assert req.cod is False
        assert req.content == ""
        assert req.parcels == []

    def test_create_request_full(self):
        req = CreateShipmentRequest(
            credentials=SchenkerCredentials(login="u", password="p"),
            shipper=ShipmentParty(first_name="Jan", city="Warszawa"),
            receiver=ShipmentParty(first_name="Anna", city="Poznan"),
            parcels=[Parcel(weight=500.0)],
            payment=Payment(payer_type="RECEIVER"),
            content="Machinery",
            service_name="EXPRESS",
            cod=True,
            cod_value=2500.0,
        )
        assert req.cod is True
        assert req.cod_value == 2500.0
        assert req.service_name == "EXPRESS"

    def test_create_request_serialization(self):
        req = CreateShipmentRequest(
            credentials=SchenkerCredentials(login="u", password="p"),
        )
        data = req.model_dump()
        assert "credentials" in data
        assert "parcels" in data
        assert "extras" in data


class TestLabelRequest:
    def test_label_request(self):
        req = LabelRequest(
            credentials=SchenkerCredentials(login="u", password="p"),
            waybill_numbers=["SCH001", "SCH002"],
        )
        assert len(req.waybill_numbers) == 2

    def test_label_request_empty(self):
        req = LabelRequest(
            credentials=SchenkerCredentials(login="u", password="p"),
        )
        assert req.waybill_numbers == []


class TestDeleteOrderRequest:
    def test_delete_request(self):
        req = DeleteOrderRequest(
            credentials=SchenkerCredentials(login="u", password="p"),
            waybill_number="SCH001",
        )
        assert req.waybill_number == "SCH001"
        assert req.credentials.login == "u"

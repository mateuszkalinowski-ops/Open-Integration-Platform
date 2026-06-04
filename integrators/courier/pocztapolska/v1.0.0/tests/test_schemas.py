"""Tests for Poczta Polska Pydantic schemas."""

from src.schemas import (
    CreateShipmentRequest,
    LabelRequest,
    Parcel,
    Payment,
    PocztaPolskaCredentials,
    PocztaPolskaExtras,
    PointsRequest,
    ShipmentParty,
)


class TestPocztaPolskaCredentials:
    def test_create_credentials(self):
        creds = PocztaPolskaCredentials(login="user", password="pass")
        assert creds.login == "user"
        assert creds.password == "pass"

    def test_credentials_serialization(self):
        creds = PocztaPolskaCredentials(login="u", password="p")
        data = creds.model_dump()
        assert data["login"] == "u"
        assert data["password"] == "p"


class TestShipmentParty:
    def test_party_defaults(self):
        party = ShipmentParty()
        assert party.first_name == ""
        assert party.country_code == "PL"
        assert party.email == ""

    def test_party_with_values(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            street="Pocztowa",
            building_number="1",
            city="Warszawa",
            postal_code="00-001",
            phone="+48123456789",
        )
        assert party.first_name == "Jan"
        assert party.city == "Warszawa"

    def test_party_serialization(self):
        party = ShipmentParty(first_name="Anna", city="Gdansk")
        data = party.model_dump()
        assert "first_name" in data
        assert "country_code" in data


class TestParcel:
    def test_parcel_defaults(self):
        parcel = Parcel()
        assert parcel.weight == 0
        assert parcel.quantity == 1
        assert parcel.parcel_type == "PACKAGE"

    def test_parcel_with_dimensions(self):
        parcel = Parcel(weight=10.0, length=50, width=30, height=20)
        assert parcel.weight == 10.0
        assert parcel.length == 50


class TestPayment:
    def test_payment_defaults(self):
        payment = Payment()
        assert payment.payer_type == "SHIPPER"
        assert payment.payment_method == "BANK_TRANSFER"
        assert payment.account_id == ""

    def test_payment_with_values(self):
        payment = Payment(
            payer_type="RECEIVER",
            payment_method="COD",
            account_id="ACC-001",
            transfer_title="Invoice 123",
        )
        assert payment.payer_type == "RECEIVER"
        assert payment.transfer_title == "Invoice 123"


class TestPocztaPolskaExtras:
    def test_extras_defaults(self):
        extras = PocztaPolskaExtras()
        assert extras.dispatch_office == ""
        assert extras.not_clear_envelope is False
        assert extras.book_courier is False
        assert extras.insurance is False
        assert extras.delivery9 is False
        assert extras.delivery12 is False

    def test_extras_with_options(self):
        extras = PocztaPolskaExtras(
            book_courier=True,
            insurance=True,
            insurance_value=5000.0,
            delivery_saturday=True,
            rod=True,
        )
        assert extras.book_courier is True
        assert extras.insurance_value == 5000.0
        assert extras.delivery_saturday is True

    def test_extras_serialization(self):
        extras = PocztaPolskaExtras(voivodeship_id="14")
        data = extras.model_dump()
        assert data["voivodeship_id"] == "14"
        assert "insurance" in data


class TestCreateShipmentRequest:
    def test_create_request_minimal(self):
        req = CreateShipmentRequest(
            credentials=PocztaPolskaCredentials(login="u", password="p"),
        )
        assert req.cod is False
        assert req.content == ""
        assert req.parcels == []

    def test_create_request_full(self):
        req = CreateShipmentRequest(
            credentials=PocztaPolskaCredentials(login="u", password="p"),
            shipper=ShipmentParty(first_name="Jan", city="Warszawa"),
            receiver=ShipmentParty(first_name="Anna", city="Krakow"),
            parcels=[Parcel(weight=5.0)],
            content="Documents",
            cod=True,
            cod_value=100.0,
        )
        assert req.cod is True
        assert req.cod_value == 100.0
        assert len(req.parcels) == 1


class TestLabelRequest:
    def test_label_request(self):
        req = LabelRequest(
            credentials=PocztaPolskaCredentials(login="u", password="p"),
            waybill_numbers=["PP001"],
        )
        assert len(req.waybill_numbers) == 1
        assert req.external_id is None

    def test_label_request_with_external_id(self):
        req = LabelRequest(
            credentials=PocztaPolskaCredentials(login="u", password="p"),
            waybill_numbers=["PP001"],
            external_id=["EXT-1"],
        )
        assert req.external_id == ["EXT-1"]


class TestPointsRequest:
    def test_points_request(self):
        req = PointsRequest(
            credentials=PocztaPolskaCredentials(login="u", password="p"),
            voivodeship_id="14",
        )
        assert req.voivodeship_id == "14"

    def test_points_request_defaults(self):
        req = PointsRequest(
            credentials=PocztaPolskaCredentials(login="u", password="p"),
        )
        assert req.voivodeship_id == ""

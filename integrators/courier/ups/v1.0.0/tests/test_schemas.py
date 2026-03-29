"""Tests for UPS Pydantic schemas."""

import pytest
from pydantic import ValidationError
from src.schemas import (
    AddressResponse,
    CreateOrderResponse,
    CreateShipmentRequest,
    LabelRequest,
    LoginRequest,
    Parcel,
    PaymentDetails,
    RateProduct,
    RateRequest,
    ShipmentParty,
    ShipmentPartyResponse,
    StandardizedRateResponse,
    StatusRequest,
    UPS_AVAILABLE_PARCEL_TYPES,
    UPS_AVAILABLE_SERVICES,
    UploadDocumentRequest,
    UpsCredentials,
    UpsExtras,
)


class TestUpsCredentials:
    def test_create_credentials_required(self):
        creds = UpsCredentials(login="client_id", password="secret")
        assert creds.login == "client_id"
        assert creds.password == "secret"
        assert creds.shipper_number == ""
        assert creds.access_token == ""

    def test_create_credentials_full(self):
        creds = UpsCredentials(
            login="cid",
            password="sec",
            shipper_number="ABC123",
            access_token="tok-xyz",
        )
        assert creds.shipper_number == "ABC123"
        assert creds.access_token == "tok-xyz"

    def test_credentials_serialization(self):
        creds = UpsCredentials(login="c", password="p")
        data = creds.model_dump()
        assert "login" in data
        assert "shipper_number" in data


class TestUpsExtras:
    def test_extras_defaults(self):
        extras = UpsExtras()
        assert extras.delivery12 is False
        assert extras.insurance is False
        assert extras.insurance_value == 0
        assert extras.insurance_curr == "PLN"
        assert extras.custom_document_ids == []

    def test_extras_with_values(self):
        extras = UpsExtras(
            delivery12=True,
            insurance=True,
            insurance_value=10000.0,
            custom_document_ids=["DOC-001", "DOC-002"],
        )
        assert extras.delivery12 is True
        assert len(extras.custom_document_ids) == 2


class TestParcel:
    def test_parcel_creation(self):
        parcel = Parcel(height=10.0, length=30.0, weight=5.0, width=20.0)
        assert parcel.height == 10.0
        assert parcel.weight == 5.0
        assert parcel.quantity == 1
        assert parcel.parcel_type == "02"

    def test_parcel_alias(self):
        parcel = Parcel(height=10, length=30, weight=5, width=20, type="03")
        assert parcel.parcel_type == "03"

    def test_parcel_serialization_by_alias(self):
        parcel = Parcel(height=10, length=30, weight=5, width=20)
        data = parcel.model_dump(by_alias=True)
        assert "type" in data
        assert data["type"] == "02"

    def test_parcel_serialization_by_name(self):
        parcel = Parcel(height=10, length=30, weight=5, width=20)
        data = parcel.model_dump()
        assert "parcel_type" in data


class TestShipmentParty:
    def test_party_defaults(self):
        party = ShipmentParty()
        assert party.first_name == ""
        assert party.country_code == "PL"
        assert party.company_name is None
        assert party.province is None

    def test_party_with_alias(self):
        party = ShipmentParty(company="Test Corp")
        assert party.company_name == "Test Corp"

    def test_party_serialization_by_alias(self):
        party = ShipmentParty(first_name="Jan", company="Corp")
        data = party.model_dump(by_alias=True)
        assert "company" in data

    def test_party_full(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            company_name="ACME",
            email="jan@acme.pl",
            phone="+48123456789",
            street="Main St",
            building_number="10",
            city="Warszawa",
            postal_code="00-001",
            province="Mazowieckie",
            tax_number="PL1234567890",
        )
        assert party.province == "Mazowieckie"
        assert party.tax_number == "PL1234567890"


class TestPaymentDetails:
    def test_payment_defaults(self):
        payment = PaymentDetails()
        assert payment.account_id is None
        assert payment.payer_type is None

    def test_payment_with_values(self):
        payment = PaymentDetails(
            account_id="ACC-001",
            payer_type="SHIPPER",
            payment_method="PREPAID",
        )
        assert payment.account_id == "ACC-001"


class TestCreateShipmentRequest:
    def test_create_request(self):
        req = CreateShipmentRequest(
            credentials=UpsCredentials(login="c", password="p"),
            parcels=[Parcel(height=10, length=30, weight=5, width=20)],
            shipper=ShipmentParty(first_name="Jan", city="Warszawa"),
            receiver=ShipmentParty(first_name="Anna", city="Krakow"),
        )
        assert req.service_name == "11"
        assert req.cod is False
        assert len(req.parcels) == 1

    def test_create_request_with_alias(self):
        req = CreateShipmentRequest(
            credentials=UpsCredentials(login="c", password="p"),
            serviceName="03",
            parcels=[Parcel(height=10, length=30, weight=5, width=20)],
            shipper=ShipmentParty(),
            receiver=ShipmentParty(),
        )
        assert req.service_name == "03"

    def test_create_request_serialization_by_alias(self):
        req = CreateShipmentRequest(
            credentials=UpsCredentials(login="c", password="p"),
            parcels=[Parcel(height=10, length=30, weight=5, width=20)],
            shipper=ShipmentParty(),
            receiver=ShipmentParty(),
        )
        data = req.model_dump(by_alias=True)
        assert "serviceName" in data
        assert "codValue" in data


class TestLabelRequest:
    def test_label_request(self):
        req = LabelRequest(
            credentials=UpsCredentials(login="c", password="p"),
            waybill_numbers=["1Z999AA10123456784"],
        )
        assert len(req.waybill_numbers) == 1


class TestStatusRequest:
    def test_status_request(self):
        req = StatusRequest(credentials=UpsCredentials(login="c", password="p"))
        assert req.credentials.login == "c"


class TestLoginRequest:
    def test_login_request(self):
        req = LoginRequest(credentials=UpsCredentials(login="cid", password="sec"))
        assert req.credentials.login == "cid"


class TestUploadDocumentRequest:
    def test_upload_request(self):
        req = UploadDocumentRequest(
            credentials=UpsCredentials(login="c", password="p"),
            waybill="1Z999",
            filename="invoice.pdf",
            file="base64content==",
        )
        assert req.document_type == "001"

    def test_upload_request_with_type_alias(self):
        req = UploadDocumentRequest(
            credentials=UpsCredentials(login="c", password="p"),
            waybill="1Z999",
            filename="doc.pdf",
            file="base64==",
            type="002",
        )
        assert req.document_type == "002"

    def test_upload_request_serialization_by_alias(self):
        req = UploadDocumentRequest(
            credentials=UpsCredentials(login="c", password="p"),
            waybill="1Z",
            filename="f.pdf",
            file="b64",
        )
        data = req.model_dump(by_alias=True)
        assert "type" in data


class TestRateRequest:
    def test_rate_request_defaults(self):
        req = RateRequest()
        assert req.sender_postal_code == ""
        assert req.sender_country_code == "PL"
        assert req.receiver_country_code == "PL"
        assert req.weight == 0

    def test_rate_request_with_alias(self):
        req = RateRequest(
            senderPostalCode="00-001",
            senderCity="Warszawa",
            receiverPostalCode="30-001",
            receiverCity="Krakow",
            weight=5.0,
        )
        assert req.sender_postal_code == "00-001"
        assert req.receiver_city == "Krakow"

    def test_rate_request_serialization_by_alias(self):
        req = RateRequest(weight=10.0)
        data = req.model_dump(by_alias=True)
        assert "senderPostalCode" in data
        assert "receiverCountryCode" in data


class TestRateProduct:
    def test_rate_product(self):
        product = RateProduct(name="UPS Express", price=45.99)
        assert product.currency == "PLN"
        assert product.delivery_days is None
        assert product.delivery_date == ""

    def test_rate_product_full(self):
        product = RateProduct(
            name="UPS Standard",
            price=25.50,
            currency="EUR",
            delivery_days=3,
            delivery_date="2026-04-01",
            attributes={"guaranteed": True},
        )
        assert product.delivery_days == 3
        assert product.attributes["guaranteed"] is True


class TestStandardizedRateResponse:
    def test_rate_response_empty(self):
        resp = StandardizedRateResponse()
        assert resp.products == []
        assert resp.source == ""
        assert resp.raw == {}

    def test_rate_response_with_products(self):
        resp = StandardizedRateResponse(
            products=[RateProduct(name="Express", price=50.0)],
            source="ups",
        )
        assert len(resp.products) == 1
        assert resp.source == "ups"


class TestResponseSchemas:
    def test_address_response_defaults(self):
        addr = AddressResponse()
        assert addr.building_number == ""
        assert addr.country_code == "PL"

    def test_shipment_party_response(self):
        party = ShipmentPartyResponse(first_name="Jan", last_name="Kowalski")
        assert party.contact_person is None
        assert party.address.city == ""

    def test_create_order_response(self):
        resp = CreateOrderResponse(
            id="UPS-001",
            waybill_number="1Z999",
            shipper=ShipmentPartyResponse(),
            receiver=ShipmentPartyResponse(),
        )
        assert resp.order_status == "CREATED"

    def test_create_order_response_alias_serialization(self):
        resp = CreateOrderResponse(
            id="UPS-001",
            waybill_number="1Z999",
            shipper=ShipmentPartyResponse(),
            receiver=ShipmentPartyResponse(),
        )
        data = resp.model_dump(by_alias=True)
        assert "orderStatus" in data


class TestConstants:
    def test_available_services_not_empty(self):
        assert len(UPS_AVAILABLE_SERVICES) > 0
        assert "11" in UPS_AVAILABLE_SERVICES

    def test_available_parcel_types_not_empty(self):
        assert len(UPS_AVAILABLE_PARCEL_TYPES) > 0
        assert "02" in UPS_AVAILABLE_PARCEL_TYPES

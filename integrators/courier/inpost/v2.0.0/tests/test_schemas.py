"""Tests for InPost International 2024 integrator v2.0.0 — Pydantic schemas."""

from __future__ import annotations

import pytest
from src.schemas import (
    AddressDto,
    ContactInfoDto,
    CreateShipmentRequest,
    DimensionsDto,
    InpostCredentials,
    LabelRequest,
    Parcel,
    ParcelDto,
    PhoneNumberDto,
    PickupHoursRequest,
    PickupRequest,
    PointsQuery,
    ShipmentParty,
    ShipmentTypeEnum,
    Tracking,
    WeightDto,
)


class TestInpostCredentials:
    def test_create_with_required_fields(self):
        creds = InpostCredentials(organization_id="org-1", client_secret="secret")
        assert creds.organization_id == "org-1"
        assert creds.client_secret == "secret"
        assert creds.access_token is None
        assert creds.sandbox_mode is False

    def test_create_with_all_fields(self):
        creds = InpostCredentials(
            organization_id="org-1",
            client_secret="secret",
            access_token="tok-xyz",
            sandbox_mode=True,
        )
        assert creds.access_token == "tok-xyz"
        assert creds.sandbox_mode is True


class TestPhoneNumberDto:
    def test_create(self):
        phone = PhoneNumberDto(prefix="+48", number="123456789")
        assert phone.prefix == "+48"
        assert phone.number == "123456789"

    def test_from_phone_string_with_prefix(self):
        phone = PhoneNumberDto.from_phone_string("+48 123456789")
        assert phone.prefix == "+48"
        assert phone.number == "123456789"

    def test_from_phone_string_without_prefix(self):
        phone = PhoneNumberDto.from_phone_string("123456789")
        assert phone.prefix == "+48"
        assert phone.number == "123456789"

    def test_from_phone_string_international(self):
        phone = PhoneNumberDto.from_phone_string("+49 170123456")
        assert phone.prefix == "+49"
        assert phone.number == "170123456"


class TestContactInfoDto:
    def test_create_with_aliases(self):
        contact = ContactInfoDto(
            firstName="Jan",
            lastName="Kowalski",
            email="jan@test.pl",
            phone=PhoneNumberDto(prefix="+48", number="123456789"),
        )
        assert contact.first_name == "Jan"
        assert contact.last_name == "Kowalski"

    def test_serialization_by_alias(self):
        contact = ContactInfoDto(
            firstName="Jan",
            lastName="Kowalski",
            email="jan@test.pl",
            phone=PhoneNumberDto(prefix="+48", number="123456789"),
            companyName="Test Co",
        )
        data = contact.model_dump(by_alias=True)
        assert "firstName" in data
        assert "lastName" in data
        assert "companyName" in data


class TestAddressDto:
    def test_create_with_aliases(self):
        addr = AddressDto(
            street="Marszalkowska",
            houseNumber="4",
            postalCode="00-850",
            city="Warszawa",
            countryCode="PL",
        )
        assert addr.house_number == "4"
        assert addr.postal_code == "00-850"
        assert addr.country_code == "PL"

    def test_serialization_by_alias(self):
        addr = AddressDto(
            street="Testowa",
            houseNumber="1",
            postalCode="00-001",
            city="Warszawa",
            countryCode="PL",
        )
        data = addr.model_dump(by_alias=True)
        assert "houseNumber" in data
        assert "postalCode" in data
        assert "countryCode" in data


class TestDimensionsDto:
    def test_create(self):
        dims = DimensionsDto(length="30", width="20", height="15", unit="CM")
        assert dims.length == "30"
        assert dims.unit == "CM"


class TestWeightDto:
    def test_create(self):
        weight = WeightDto(amount="5", unit="KG")
        assert weight.amount == "5"
        assert weight.unit == "KG"


class TestParcelDto:
    def test_create_standard(self):
        parcel = ParcelDto(
            dimensions=DimensionsDto(length="30", width="20", height="15", unit="CM"),
            weight=WeightDto(amount="5", unit="KG"),
        )
        assert parcel.type == "STANDARD"

    def test_serialization(self):
        parcel = ParcelDto(
            dimensions=DimensionsDto(length="30", width="20", height="15", unit="CM"),
            weight=WeightDto(amount="5", unit="KG"),
        )
        data = parcel.model_dump()
        assert "dimensions" in data
        assert "weight" in data


class TestShipmentTypeEnum:
    @pytest.mark.parametrize(
        "enum_member,expected_value",
        [
            (ShipmentTypeEnum.POINT_TO_POINT, "/shipments/point-to-point"),
            (ShipmentTypeEnum.POINT_TO_ADDRESS, "/shipments/point-to-address"),
            (ShipmentTypeEnum.ADDRESS_TO_POINT, "/shipments/address-to-point"),
            (ShipmentTypeEnum.ADDRESS_TO_ADDRESS, "/shipments/address-to-address"),
        ],
    )
    def test_enum_values(self, enum_member, expected_value):
        assert enum_member.value == expected_value


class TestShipmentParty:
    def test_create_with_required_fields(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            building_number="10",
            city="Warszawa",
            postal_code="00-001",
            street="Testowa",
        )
        assert party.country_code == "PL"
        assert party.company_name is None

    def test_alias_serialization(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="K",
            building_number="1",
            city="W",
            postal_code="00-001",
            street="S",
            company="Test Co",
        )
        data = party.model_dump(by_alias=True)
        assert "company" in data


class TestParcel:
    def test_create(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15)
        assert parcel.height == 20
        assert parcel.quantity == 1

    def test_with_type_alias(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15, type="small")
        assert parcel.parcel_type == "small"

    def test_serialization_by_alias(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15, type="medium")
        data = parcel.model_dump(by_alias=True)
        assert "type" in data


class TestCreateShipmentRequest:
    def test_create_full(self):
        req = CreateShipmentRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            serviceName="inpost_international",
            parcels=[Parcel(height=20, length=30, weight=5.0, width=15)],
            shipper=ShipmentParty(
                first_name="J", last_name="K", building_number="1",
                city="W", postal_code="00-001", street="S",
            ),
            receiver=ShipmentParty(
                first_name="A", last_name="N", building_number="2",
                city="K", postal_code="30-001", street="R",
            ),
        )
        assert req.service_name == "inpost_international"
        assert req.cod is False


class TestLabelRequest:
    def test_create_with_alias(self):
        req = LabelRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            shipmentUuid="abc-123",
        )
        assert req.shipment_uuid == "abc-123"

    def test_serialization_by_alias(self):
        req = LabelRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            shipmentUuid="abc-123",
        )
        data = req.model_dump(by_alias=True)
        assert "shipmentUuid" in data


class TestPointsQuery:
    def test_defaults(self):
        query = PointsQuery(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
        )
        assert query.city is None
        assert query.extras == {}


class TestPickupRequest:
    def test_create(self):
        req = PickupRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            shipper=ShipmentParty(
                first_name="J", last_name="K", building_number="1",
                city="W", postal_code="00-001", street="S",
            ),
            parcels=[Parcel(height=20, length=30, weight=5.0, width=15)],
        )
        assert req.content is None
        assert req.extras == {}


class TestPickupHoursRequest:
    def test_create(self):
        req = PickupHoursRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            postcode="00-001",
        )
        assert req.country_code == "PL"

    def test_alias_serialization(self):
        req = PickupHoursRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            postcode="00-001",
            countryCode="DE",
        )
        data = req.model_dump(by_alias=True)
        assert "countryCode" in data
        assert data["countryCode"] == "DE"


class TestTracking:
    def test_defaults(self):
        tracking = Tracking()
        assert tracking.tracking_number is None
        assert tracking.tracking_url is None

    def test_serialization(self):
        tracking = Tracking(tracking_number="INT620000001")
        data = tracking.model_dump()
        assert data["tracking_number"] == "INT620000001"

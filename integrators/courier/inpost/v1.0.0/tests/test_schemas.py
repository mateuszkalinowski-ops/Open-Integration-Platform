"""Tests for InPost Courier integrator v1.0.0 — Pydantic schemas."""

from __future__ import annotations

import pytest
from src.schemas import (
    CreateShipmentRequest,
    InpostCredentials,
    InpostExtras,
    LabelRequest,
    Parcel,
    PointsQuery,
    ShipmentParty,
    Tracking,
)


class TestInpostCredentials:
    def test_create_with_required_fields(self):
        creds = InpostCredentials(organization_id="org-1", api_token="tok-abc")
        assert creds.organization_id == "org-1"
        assert creds.api_token == "tok-abc"
        assert creds.sandbox_mode is False

    def test_create_with_sandbox_mode(self):
        creds = InpostCredentials(
            organization_id="org-1",
            api_token="tok-abc",
            sandbox_mode=True,
        )
        assert creds.sandbox_mode is True

    def test_serialization(self):
        creds = InpostCredentials(organization_id="org-1", api_token="tok-abc")
        data = creds.model_dump()
        assert "organization_id" in data
        assert "api_token" in data
        assert "sandbox_mode" in data


class TestInpostExtras:
    def test_defaults(self):
        extras = InpostExtras()
        assert extras.delivery_saturday is False
        assert extras.insurance is False
        assert extras.insurance_value == 0
        assert extras.rod is False
        assert extras.return_pack is False
        assert extras.custom_attributes == {}

    def test_with_values(self):
        extras = InpostExtras(
            delivery_saturday=True,
            insurance=True,
            insurance_value=2000.0,
            delivery_sms=True,
            delivery_email=True,
        )
        assert extras.delivery_saturday is True
        assert extras.insurance_value == 2000.0
        assert extras.delivery_sms is True


class TestParcel:
    def test_create_parcel(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15)
        assert parcel.height == 20
        assert parcel.length == 30
        assert parcel.weight == 5.0
        assert parcel.quantity == 1

    def test_parcel_with_type_alias(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15, type="small")
        assert parcel.parcel_type == "small"

    def test_parcel_serialization_by_alias(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15, type="small")
        data = parcel.model_dump(by_alias=True)
        assert "type" in data


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
        assert party.first_name == "Jan"
        assert party.country_code == "PL"
        assert party.company_name is None

    def test_create_with_all_fields(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            building_number="10",
            city="Warszawa",
            postal_code="00-001",
            street="Testowa",
            email="jan@test.pl",
            phone="+48123456789",
            company="Test Sp. z o.o.",
            contact_person="Jan K.",
            tax_number="PL1234567890",
            client_id="CL-001",
            province="mazowieckie",
        )
        assert party.company_name == "Test Sp. z o.o."
        assert party.tax_number == "PL1234567890"

    def test_alias_serialization(self):
        party = ShipmentParty(
            first_name="Jan",
            last_name="Kowalski",
            building_number="10",
            city="Warszawa",
            postal_code="00-001",
            street="Testowa",
            company="Test Co",
        )
        data = party.model_dump(by_alias=True)
        assert "company" in data


class TestCreateShipmentRequest:
    def test_create_full_request(self):
        req = CreateShipmentRequest(
            credentials=InpostCredentials(organization_id="org-1", api_token="tok"),
            serviceName="inpost_locker_standard",
            parcels=[Parcel(height=20, length=30, weight=5.0, width=15)],
            shipper=ShipmentParty(
                first_name="Jan",
                last_name="K",
                building_number="1",
                city="W",
                postal_code="00-001",
                street="S",
            ),
            receiver=ShipmentParty(
                first_name="Anna",
                last_name="N",
                building_number="2",
                city="K",
                postal_code="30-001",
                street="R",
            ),
        )
        assert req.service_name == "inpost_locker_standard"
        assert req.cod is False
        assert req.cod_value is None
        assert len(req.parcels) == 1

    def test_populate_by_name(self):
        req = CreateShipmentRequest(
            credentials=InpostCredentials(organization_id="org-1", api_token="tok"),
            service_name="inpost_courier",
            parcels=[Parcel(height=20, length=30, weight=5.0, width=15)],
            shipper=ShipmentParty(
                first_name="J",
                last_name="K",
                building_number="1",
                city="W",
                postal_code="00-001",
                street="S",
            ),
            receiver=ShipmentParty(
                first_name="A",
                last_name="N",
                building_number="2",
                city="K",
                postal_code="30-001",
                street="R",
            ),
        )
        assert req.service_name == "inpost_courier"

    def test_serialization_by_alias(self):
        req = CreateShipmentRequest(
            credentials=InpostCredentials(organization_id="org-1", api_token="tok"),
            serviceName="inpost_locker_standard",
            parcels=[Parcel(height=20, length=30, weight=5.0, width=15)],
            shipper=ShipmentParty(
                first_name="J",
                last_name="K",
                building_number="1",
                city="W",
                postal_code="00-001",
                street="S",
            ),
            receiver=ShipmentParty(
                first_name="A",
                last_name="N",
                building_number="2",
                city="K",
                postal_code="30-001",
                street="R",
            ),
        )
        data = req.model_dump(by_alias=True)
        assert "serviceName" in data
        assert "codValue" in data or "cod_value" not in data


class TestLabelRequest:
    def test_create_label_request(self):
        req = LabelRequest(
            waybill_numbers=["620000000001", "620000000002"],
            credentials=InpostCredentials(organization_id="org-1", api_token="tok"),
        )
        assert len(req.waybill_numbers) == 2


class TestPointsQuery:
    def test_defaults(self):
        query = PointsQuery(
            credentials=InpostCredentials(organization_id="org-1", api_token="tok"),
        )
        assert query.city is None
        assert query.postcode is None
        assert query.extras == {}

    def test_with_values(self):
        query = PointsQuery(
            credentials=InpostCredentials(organization_id="org-1", api_token="tok"),
            city="Warszawa",
            postcode="00-001",
            extras={"type": "parcel_locker"},
        )
        assert query.city == "Warszawa"
        assert query.extras["type"] == "parcel_locker"


class TestTracking:
    def test_defaults(self):
        tracking = Tracking()
        assert tracking.tracking_number is None
        assert tracking.tracking_url is None

    def test_with_values(self):
        tracking = Tracking(
            tracking_number="620000000001",
            tracking_url="https://inpost.pl/tracking/620000000001",
        )
        assert tracking.tracking_number == "620000000001"

    def test_serialization(self):
        tracking = Tracking(tracking_number="620000000001")
        data = tracking.model_dump()
        assert data["tracking_number"] == "620000000001"
        assert data["tracking_url"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("organization_id", "org-test"),
        ("api_token", "token-test"),
        ("sandbox_mode", True),
    ],
)
def test_credentials_fields(field, value):
    creds = InpostCredentials(
        organization_id="org-test",
        api_token="token-test",
        sandbox_mode=True,
    )
    assert getattr(creds, field) == value

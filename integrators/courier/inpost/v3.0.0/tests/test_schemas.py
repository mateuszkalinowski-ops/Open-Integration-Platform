"""Tests for InPost International 2025 integrator v3.0.0 — Pydantic schemas."""

from __future__ import annotations

from src.schemas import (
    AnyPoint,
    CreateShipmentRequest,
    DestinationPoint,
    InpostCredentials,
    LabelRequest,
    Parcel,
    PickupAddress,
    PickupContactInfo,
    PickupHoursRequest,
    PickupPhoneNumber,
    PickupRequest,
    PointsQuery,
    RateProduct,
    RateRequest,
    ReturnsContactInfo,
    ReturnsCreateShipmentDto,
    ReturnsShipmentRequest,
    ShipmentParty,
    ShippingAddress,
    ShippingContactInfo,
    ShippingDimensions,
    ShippingWeight,
    StandardizedRateResponse,
    StandardParcel,
    Tracking,
)


class TestInpostCredentials:
    def test_create_with_required_fields(self):
        creds = InpostCredentials(organization_id="org-1", client_secret="sec")
        assert creds.organization_id == "org-1"
        assert creds.client_secret == "sec"
        assert creds.access_token is None
        assert creds.sandbox_mode is False

    def test_create_with_all_fields(self):
        creds = InpostCredentials(
            organization_id="org-1",
            client_secret="sec",
            access_token="tok-xyz",
            sandbox_mode=True,
        )
        assert creds.access_token == "tok-xyz"
        assert creds.sandbox_mode is True

    def test_serialization(self):
        creds = InpostCredentials(organization_id="org-1", client_secret="sec")
        data = creds.model_dump()
        assert "organization_id" in data
        assert "client_secret" in data


class TestShippingContactInfo:
    def test_create_with_aliases(self):
        contact = ShippingContactInfo(
            firstName="Jan",
            lastName="Kowalski",
            phone="+48123456789",
            email="jan@test.pl",
        )
        assert contact.first_name == "Jan"
        assert contact.last_name == "Kowalski"

    def test_with_company(self):
        contact = ShippingContactInfo(
            firstName="Jan",
            lastName="K",
            phone="123",
            email="j@t.pl",
            companyName="Test Co",
        )
        assert contact.company_name == "Test Co"

    def test_serialization_by_alias(self):
        contact = ShippingContactInfo(
            firstName="Jan",
            lastName="K",
            phone="123",
            email="j@t.pl",
        )
        data = contact.model_dump(by_alias=True)
        assert "firstName" in data
        assert "lastName" in data


class TestShippingAddress:
    def test_create(self):
        addr = ShippingAddress(
            countryCode="PL",
            street="Marszalkowska",
            houseNumber="4",
            city="Warszawa",
            postalCode="00-850",
        )
        assert addr.country_code == "PL"
        assert addr.postal_code == "00-850"

    def test_serialization_by_alias(self):
        addr = ShippingAddress(
            countryCode="PL",
            street="Test",
            city="W",
            postalCode="00-001",
        )
        data = addr.model_dump(by_alias=True)
        assert "countryCode" in data
        assert "postalCode" in data


class TestAnyPoint:
    def test_create(self):
        point = AnyPoint(countryCode="PL", shippingMethod="APM")
        assert point.country_code == "PL"
        assert point.shipping_method == "APM"

    def test_serialization_by_alias(self):
        point = AnyPoint(countryCode="PL", shippingMethod="PUDO")
        data = point.model_dump(by_alias=True)
        assert "countryCode" in data
        assert "shippingMethod" in data


class TestDestinationPoint:
    def test_create(self):
        dest = DestinationPoint(countryCode="PL", pointId="KRA108")
        assert dest.country_code == "PL"
        assert dest.point_id == "KRA108"


class TestShippingDimensions:
    def test_create(self):
        dims = ShippingDimensions(length=30.0, width=20.0, height=15.0, unit="CM")
        assert dims.length == 30.0
        assert dims.unit == "CM"


class TestShippingWeight:
    def test_create(self):
        weight = ShippingWeight(amount=5.0, unit="KG")
        assert weight.amount == 5.0
        assert weight.unit == "KG"


class TestStandardParcel:
    def test_create(self):
        parcel = StandardParcel(
            dimensions=ShippingDimensions(length=30, width=20, height=15, unit="CM"),
            weight=ShippingWeight(amount=5.0, unit="KG"),
        )
        assert parcel.type_ == "STANDARD"

    def test_serialization_by_alias(self):
        parcel = StandardParcel(
            dimensions=ShippingDimensions(length=30, width=20, height=15, unit="CM"),
            weight=ShippingWeight(amount=5.0, unit="KG"),
        )
        data = parcel.model_dump(by_alias=True)
        assert "type" in data
        assert data["type"] == "STANDARD"


class TestReturnsContactInfo:
    def test_create(self):
        contact = ReturnsContactInfo(
            firstName="Jan",
            lastName="K",
            phone="+48123456789",
            email="jan@test.pl",
        )
        assert contact.first_name == "Jan"

    def test_optional_name_fields(self):
        contact = ReturnsContactInfo(phone="+48123456789", email="jan@test.pl")
        assert contact.first_name is None
        assert contact.last_name is None


class TestReturnsCreateShipmentDto:
    def test_minimal(self):
        dto = ReturnsCreateShipmentDto(
            sender=ReturnsContactInfo(phone="+48123456789", email="jan@test.pl"),
        )
        assert dto.recipient is None
        assert dto.origin is None
        assert dto.parcels is None


class TestShipmentParty:
    def test_create(self):
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
            first_name="J",
            last_name="K",
            building_number="1",
            city="W",
            postal_code="00-001",
            street="S",
            company="Co",
        )
        data = party.model_dump(by_alias=True)
        assert "company" in data


class TestParcel:
    def test_create(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15)
        assert parcel.height == 20
        assert parcel.quantity == 1

    def test_with_alias(self):
        parcel = Parcel(height=20, length=30, weight=5.0, width=15, type="small")
        assert parcel.parcel_type == "small"
        data = parcel.model_dump(by_alias=True)
        assert "type" in data


class TestCreateShipmentRequest:
    def test_create(self):
        req = CreateShipmentRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            serviceName="inpost_international",
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
        assert req.service_name == "inpost_international"
        assert req.cod is False


class TestLabelRequest:
    def test_create(self):
        req = LabelRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            trackingNumber="620000000001",
        )
        assert req.tracking_number == "620000000001"

    def test_serialization_by_alias(self):
        req = LabelRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            trackingNumber="620000000001",
        )
        data = req.model_dump(by_alias=True)
        assert "trackingNumber" in data


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
                first_name="J",
                last_name="K",
                building_number="1",
                city="W",
                postal_code="00-001",
                street="S",
            ),
            parcels=[Parcel(height=20, length=30, weight=5.0, width=15)],
        )
        assert req.tracking_numbers is None
        assert req.content is None

    def test_with_tracking_numbers(self):
        req = PickupRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            shipper=ShipmentParty(
                first_name="J",
                last_name="K",
                building_number="1",
                city="W",
                postal_code="00-001",
                street="S",
            ),
            parcels=[Parcel(height=20, length=30, weight=5.0, width=15)],
            trackingNumbers=["TN001", "TN002"],
        )
        assert req.tracking_numbers == ["TN001", "TN002"]


class TestReturnsShipmentRequest:
    def test_create(self):
        req = ReturnsShipmentRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            senderPhone="+48123456789",
            senderEmail="sender@test.pl",
        )
        assert req.sender_phone == "+48123456789"
        assert req.sender_email == "sender@test.pl"
        assert req.sender_first_name is None

    def test_serialization_by_alias(self):
        req = ReturnsShipmentRequest(
            credentials=InpostCredentials(organization_id="org-1", client_secret="sec"),
            senderPhone="+48123456789",
            senderEmail="sender@test.pl",
            senderFirstName="Jan",
            senderLastName="K",
        )
        data = req.model_dump(by_alias=True)
        assert "senderPhone" in data
        assert "senderEmail" in data
        assert "senderFirstName" in data


class TestRateRequest:
    def test_defaults(self):
        req = RateRequest()
        assert req.sender_country_code == "PL"
        assert req.receiver_country_code == "PL"
        assert req.weight == 0

    def test_alias_serialization(self):
        req = RateRequest(
            senderCountryCode="PL",
            receiverCountryCode="DE",
            weight=5.0,
        )
        data = req.model_dump(by_alias=True)
        assert "senderCountryCode" in data
        assert "receiverCountryCode" in data


class TestRateProduct:
    def test_create(self):
        product = RateProduct(name="InPost Paczkomat (A)", price=12.99, delivery_days=2)
        assert product.name == "InPost Paczkomat (A)"
        assert product.currency == "PLN"

    def test_serialization(self):
        product = RateProduct(
            name="Test",
            price=10.0,
            attributes={"source": "inpost", "service": "paczkomat"},
        )
        data = product.model_dump()
        assert data["attributes"]["source"] == "inpost"


class TestStandardizedRateResponse:
    def test_empty(self):
        resp = StandardizedRateResponse(source="inpost")
        assert resp.products == []

    def test_with_products(self):
        resp = StandardizedRateResponse(
            products=[RateProduct(name="Test", price=12.99)],
            source="inpost",
            raw={"method": "pricing_table"},
        )
        data = resp.model_dump()
        assert len(data["products"]) == 1


class TestTracking:
    def test_defaults(self):
        t = Tracking()
        assert t.tracking_number is None

    def test_with_values(self):
        t = Tracking(tracking_number="620000000001", tracking_url="https://inpost.pl")
        assert t.tracking_number == "620000000001"


class TestPickupContactInfo:
    def test_create(self):
        phone = PickupPhoneNumber(prefix="+48", number="123456789")
        contact = PickupContactInfo(
            firstName="Jan",
            lastName="K",
            phone=phone,
            email="jan@test.pl",
        )
        assert contact.first_name == "Jan"
        data = contact.model_dump()
        assert data["phone"]["prefix"] == "+48"


class TestPickupAddress:
    def test_create(self):
        addr = PickupAddress(
            countryCode="PL",
            street="Testowa",
            houseNumber="1",
            city="Warszawa",
            postalCode="00-001",
        )
        assert addr.country_code == "PL"
        assert addr.location_description is None

    def test_serialization_by_alias(self):
        addr = PickupAddress(
            countryCode="PL",
            street="T",
            houseNumber="1",
            city="W",
            postalCode="00-001",
        )
        data = addr.model_dump(by_alias=True)
        assert "countryCode" in data
        assert "houseNumber" in data
        assert "postalCode" in data


class TestPickupHoursRequest:
    def test_defaults(self):
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
        assert data["countryCode"] == "DE"

"""Tests for DHL Express Courier integrator — Pydantic schemas."""

from __future__ import annotations

import pytest
from src.schemas import (
    Address,
    Contact,
    CreateShipmentRequest,
    Dimensions,
    ExportDeclaration,
    LineItem,
    Package,
    Party,
    PickupRequest,
    RateProduct,
    RateRequest,
    RegistrationNumber,
    ShipmentContent,
    ShipmentOutput,
    StandardizedRateResponse,
    TrackingQuery,
    ValueAddedService,
)


class TestAddress:
    def test_create_with_required_fields(self):
        addr = Address(streetLine1="Testowa 1", city="Warszawa", countryCode="PL")
        assert addr.street_line1 == "Testowa 1"
        assert addr.city == "Warszawa"
        assert addr.country_code == "PL"
        assert addr.street_line2 == ""
        assert addr.postal_code == ""

    def test_create_with_all_fields(self):
        addr = Address(
            streetLine1="Testowa 1",
            streetLine2="Floor 3",
            streetLine3="Suite 5",
            city="Warszawa",
            postalCode="00-001",
            provinceCode="MZ",
            countryCode="PL",
        )
        assert addr.street_line2 == "Floor 3"
        assert addr.province_code == "MZ"

    def test_serialization_by_alias(self):
        addr = Address(streetLine1="Test", city="W", countryCode="PL")
        data = addr.model_dump(by_alias=True)
        assert "streetLine1" in data
        assert "countryCode" in data
        assert "postalCode" in data


class TestContact:
    def test_create(self):
        contact = Contact(
            companyName="Test Co",
            fullName="Jan Kowalski",
            phone="+48123456789",
        )
        assert contact.company_name == "Test Co"
        assert contact.full_name == "Jan Kowalski"
        assert contact.email == ""

    def test_serialization_by_alias(self):
        contact = Contact(
            companyName="C",
            fullName="F",
            phone="1",
            email="e@t.pl",
        )
        data = contact.model_dump(by_alias=True)
        assert "companyName" in data
        assert "fullName" in data


class TestParty:
    def test_create(self):
        party = Party(
            address=Address(streetLine1="T", city="W", countryCode="PL"),
            contact=Contact(companyName="C", fullName="F", phone="1"),
        )
        assert party.address.city == "W"
        assert party.contact.company_name == "C"


class TestRegistrationNumber:
    def test_create(self):
        reg = RegistrationNumber(
            typeCode="VAT",
            number="PL1234567890",
            issuerCountryCode="PL",
        )
        assert reg.type_code == "VAT"
        assert reg.number == "PL1234567890"

    def test_serialization_by_alias(self):
        reg = RegistrationNumber(typeCode="EOR", number="123", issuerCountryCode="DE")
        data = reg.model_dump(by_alias=True)
        assert "typeCode" in data
        assert "issuerCountryCode" in data


class TestDimensions:
    def test_create(self):
        dims = Dimensions(length=30, width=20, height=15)
        assert dims.length == 30


class TestPackage:
    def test_create_minimal(self):
        pkg = Package(weight=5.0)
        assert pkg.weight == 5.0
        assert pkg.dimensions is None
        assert pkg.description == ""

    def test_create_with_dimensions(self):
        pkg = Package(
            weight=5.0,
            dimensions=Dimensions(length=30, width=20, height=15),
            description="Electronics",
        )
        assert pkg.dimensions.length == 30
        assert pkg.description == "Electronics"


class TestLineItem:
    def test_defaults(self):
        item = LineItem(description="Books", price=25.0)
        assert item.number == 1
        assert item.quantity == 1
        assert item.quantity_type == "PCS"
        assert item.manufacturing_country_code == "PL"

    def test_with_values(self):
        item = LineItem(
            number=2,
            description="Electronics",
            price=500.0,
            quantity=3,
            hsCode="8471.30",
            manufacturingCountryCode="CN",
        )
        assert item.hs_code == "8471.30"
        assert item.manufacturing_country_code == "CN"

    def test_serialization_by_alias(self):
        item = LineItem(description="Test", price=10.0)
        data = item.model_dump(by_alias=True)
        assert "quantityType" in data
        assert "manufacturingCountryCode" in data


class TestExportDeclaration:
    def test_defaults(self):
        decl = ExportDeclaration()
        assert decl.line_items == []
        assert decl.export_reason == "SALE"
        assert decl.export_reason_type == "permanent"

    def test_with_items(self):
        decl = ExportDeclaration(
            lineItems=[LineItem(description="Books", price=25.0)],
            invoiceNumber="INV-001",
            invoiceDate="2026-04-01",
        )
        assert len(decl.line_items) == 1
        assert decl.invoice_number == "INV-001"


class TestValueAddedService:
    def test_create(self):
        vas = ValueAddedService(serviceCode="II", value=5000.0, currency="EUR")
        assert vas.service_code == "II"
        assert vas.value == 5000.0

    def test_serialization_by_alias(self):
        vas = ValueAddedService(serviceCode="PT")
        data = vas.model_dump(by_alias=True)
        assert "serviceCode" in data


class TestShipmentContent:
    def test_create_minimal(self):
        content = ShipmentContent(packages=[Package(weight=5.0)])
        assert len(content.packages) == 1
        assert content.is_custom_declarable is True
        assert content.unit_of_measurement == "metric"

    def test_serialization_by_alias(self):
        content = ShipmentContent(packages=[Package(weight=5.0)])
        data = content.model_dump(by_alias=True)
        assert "isCustomsDeclarable" in data
        assert "unitOfMeasurement" in data
        assert "declaredValueCurrency" in data


class TestShipmentOutput:
    def test_defaults(self):
        output = ShipmentOutput()
        assert output.dhl_custom_invoice is False
        assert output.image_format == "PDF"
        assert output.label_type == "PDF"


class TestCreateShipmentRequest:
    def test_create_full(self):
        req = CreateShipmentRequest(
            plannedShippingDateAndTime="2026-04-01T10:00:00Z",
            productCode="P",
            shipper=Party(
                address=Address(streetLine1="T", city="W", countryCode="PL"),
                contact=Contact(companyName="S", fullName="J", phone="1"),
            ),
            receiver=Party(
                address=Address(streetLine1="R", city="B", countryCode="DE"),
                contact=Contact(companyName="R", fullName="H", phone="2"),
            ),
            content=ShipmentContent(packages=[Package(weight=5.0)]),
        )
        assert req.product_code == "P"
        assert req.accounts == []

    def test_serialization_by_alias(self):
        req = CreateShipmentRequest(
            plannedShippingDateAndTime="2026-04-01T10:00:00Z",
            shipper=Party(
                address=Address(streetLine1="T", city="W", countryCode="PL"),
                contact=Contact(companyName="S", fullName="J", phone="1"),
            ),
            receiver=Party(
                address=Address(streetLine1="R", city="B", countryCode="DE"),
                contact=Contact(companyName="R", fullName="H", phone="2"),
            ),
            content=ShipmentContent(packages=[Package(weight=5.0)]),
        )
        data = req.model_dump(by_alias=True)
        assert "plannedShippingDateAndTime" in data
        assert "productCode" in data
        assert "outputImageProperties" in data
        assert "valueAddedServices" in data
        assert "customerReferences" in data


class TestRateRequest:
    def test_defaults(self):
        req = RateRequest()
        assert req.shipper_country_code == "PL"
        assert req.receiver_country_code == "PL"
        assert req.unit_of_measurement == "metric"
        assert req.is_customs_declarable is False

    def test_with_values(self):
        req = RateRequest(
            shipperCountryCode="PL",
            shipperPostalCode="00-001",
            shipperCity="Warszawa",
            receiverCountryCode="DE",
            receiverPostalCode="10115",
            receiverCity="Berlin",
            weight=5.0,
            length=30,
            width=20,
            height=15,
        )
        assert req.shipper_city == "Warszawa"
        assert req.receiver_city == "Berlin"

    def test_serialization_by_alias(self):
        req = RateRequest(shipperCountryCode="PL", receiverCountryCode="DE")
        data = req.model_dump(by_alias=True)
        assert "shipperCountryCode" in data
        assert "receiverCountryCode" in data
        assert "unitOfMeasurement" in data
        assert "isCustomsDeclarable" in data


class TestPickupRequest:
    def test_create(self):
        req = PickupRequest(
            plannedPickupDateAndTime="2026-04-01T10:00:00Z",
            closeTime="18:00",
        )
        assert req.location == ""
        assert req.location_type == "business"
        assert req.accounts == []
        assert req.special_instructions == []

    def test_serialization_by_alias(self):
        req = PickupRequest(
            plannedPickupDateAndTime="2026-04-01T10:00:00Z",
            closeTime="18:00",
            locationType="residence",
        )
        data = req.model_dump(by_alias=True)
        assert "plannedPickupDateAndTime" in data
        assert "closeTime" in data
        assert "locationType" in data
        assert "specialInstructions" in data
        assert "shipmentInfo" in data


class TestTrackingQuery:
    def test_defaults(self):
        query = TrackingQuery(tracking_number="1234567890")
        assert query.tracking_view == "all-checkpoints"
        assert query.level_of_detail == "all"

    def test_with_values(self):
        query = TrackingQuery(
            tracking_number="1234567890",
            tracking_view="last-checkpoint",
            level_of_detail="shipment",
        )
        assert query.tracking_view == "last-checkpoint"


class TestRateProduct:
    def test_create(self):
        product = RateProduct(name="EXPRESS WORLDWIDE", price=150.0, currency="EUR")
        assert product.name == "EXPRESS WORLDWIDE"
        assert product.delivery_days is None
        assert product.delivery_date == ""
        assert product.attributes == {}

    def test_serialization(self):
        product = RateProduct(
            name="Test",
            price=100.0,
            attributes={"source": "dhl-express", "product_code": "P"},
        )
        data = product.model_dump()
        assert data["attributes"]["source"] == "dhl-express"


class TestStandardizedRateResponse:
    def test_empty(self):
        resp = StandardizedRateResponse(source="dhl-express")
        assert resp.products == []
        assert resp.raw == {}

    def test_with_products(self):
        products = [
            RateProduct(name="EXPRESS WORLDWIDE", price=150.0, currency="EUR"),
            RateProduct(name="EXPRESS 9:00", price=300.0, currency="EUR"),
        ]
        resp = StandardizedRateResponse(
            products=products,
            source="dhl-express",
            raw={"key": "value"},
        )
        data = resp.model_dump()
        assert len(data["products"]) == 2
        assert data["source"] == "dhl-express"


@pytest.mark.parametrize(
    "field,expected",
    [
        ("shipper_country_code", "PL"),
        ("receiver_country_code", "PL"),
        ("unit_of_measurement", "metric"),
        ("is_customs_declarable", False),
        ("weight", 0),
    ],
)
def test_rate_request_defaults(field, expected):
    req = RateRequest()
    assert getattr(req, field) == expected

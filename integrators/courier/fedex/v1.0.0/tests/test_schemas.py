"""Tests for FedEx integrator — Pydantic schemas."""

from __future__ import annotations

from src.schemas import (
    CreateShipmentRequest,
    DeleteShipmentRequest,
    FedexCredentials,
    FedexExtras,
    LabelRequest,
    PointsRequest,
    RateProduct,
    RateRequest,
    StandardizedRateResponse,
)


class TestFedexCredentials:
    def test_create_with_required_fields(self):
        creds = FedexCredentials(client_id="cid", client_secret="csecret")
        assert creds.client_id == "cid"
        assert creds.client_secret == "csecret"

    def test_model_dump(self):
        creds = FedexCredentials(client_id="cid", client_secret="csecret")
        data = creds.model_dump()
        assert data["client_id"] == "cid"
        assert data["client_secret"] == "csecret"


class TestFedexExtras:
    def test_defaults(self):
        extras = FedexExtras()
        assert extras.service_type == "FEDEX_INTERNATIONAL_PRIORITY"
        assert extras.packaging_type == "YOUR_PACKAGING"
        assert extras.account_id == ""

    def test_custom_values(self):
        extras = FedexExtras(
            service_type="FEDEX_GROUND",
            packaging_type="FEDEX_BOX",
            account_id="ACC-123",
        )
        assert extras.service_type == "FEDEX_GROUND"
        assert extras.packaging_type == "FEDEX_BOX"
        assert extras.account_id == "ACC-123"


class TestCreateShipmentRequest:
    def test_create_with_defaults(self):
        req = CreateShipmentRequest(
            credentials=FedexCredentials(client_id="cid", client_secret="cs"),
        )
        assert req.command == {}

    def test_create_with_command(self):
        req = CreateShipmentRequest(
            credentials=FedexCredentials(client_id="cid", client_secret="cs"),
            command={"shipper": {"city": "Warszawa"}},
        )
        assert req.command["shipper"]["city"] == "Warszawa"


class TestDeleteShipmentRequest:
    def test_create_with_defaults(self):
        req = DeleteShipmentRequest(
            credentials=FedexCredentials(client_id="cid", client_secret="cs"),
        )
        assert req.extras == {}

    def test_model_dump(self):
        req = DeleteShipmentRequest(
            credentials=FedexCredentials(client_id="cid", client_secret="cs"),
            extras={"reason": "customer_request"},
        )
        data = req.model_dump()
        assert data["extras"]["reason"] == "customer_request"


class TestLabelRequest:
    def test_create(self):
        req = LabelRequest(
            credentials=FedexCredentials(client_id="cid", client_secret="cs"),
            waybill_numbers=["FX123", "FX456"],
        )
        assert len(req.waybill_numbers) == 2
        assert req.waybill_numbers[0] == "FX123"


class TestPointsRequest:
    def test_defaults(self):
        req = PointsRequest(
            credentials=FedexCredentials(client_id="cid", client_secret="cs"),
        )
        assert req.city == ""
        assert req.postcode == ""

    def test_with_location(self):
        req = PointsRequest(
            credentials=FedexCredentials(client_id="cid", client_secret="cs"),
            city="Kraków",
            postcode="30-001",
        )
        assert req.city == "Kraków"
        assert req.postcode == "30-001"


class TestRateRequest:
    def test_defaults(self):
        req = RateRequest()
        assert req.credentials is None
        assert req.sender_country_code == "PL"
        assert req.receiver_country_code == "PL"
        assert req.weight == 0

    def test_with_values(self):
        req = RateRequest(
            sender_postal_code="00-001",
            receiver_postal_code="30-001",
            weight=5.5,
            length=30,
            width=20,
            height=15,
            account_id="ACC-001",
        )
        assert req.weight == 5.5
        assert req.length == 30
        assert req.account_id == "ACC-001"

    def test_model_dump(self):
        req = RateRequest(weight=3.0)
        data = req.model_dump()
        assert data["weight"] == 3.0
        assert data["sender_country_code"] == "PL"


class TestRateProduct:
    def test_create_with_required_fields(self):
        product = RateProduct(name="FedEx Priority", price=45.99)
        assert product.name == "FedEx Priority"
        assert product.price == 45.99
        assert product.currency == "PLN"
        assert product.delivery_days is None
        assert product.delivery_date == ""

    def test_create_with_all_fields(self):
        product = RateProduct(
            name="FedEx Economy",
            price=29.99,
            currency="EUR",
            delivery_days=3,
            delivery_date="2026-04-01",
            attributes={"source": "fedex"},
        )
        assert product.delivery_days == 3
        assert product.currency == "EUR"

    def test_model_dump(self):
        product = RateProduct(
            name="FedEx Economy",
            price=29.99,
            delivery_days=3,
            attributes={"source": "fedex"},
        )
        data = product.model_dump()
        assert data["delivery_days"] == 3
        assert data["attributes"]["source"] == "fedex"


class TestStandardizedRateResponse:
    def test_defaults(self):
        resp = StandardizedRateResponse()
        assert resp.products == []
        assert resp.source == ""
        assert resp.raw == {}

    def test_with_products(self):
        resp = StandardizedRateResponse(
            products=[RateProduct(name="FedEx Priority", price=45.0)],
            source="fedex",
            raw={"method": "api"},
        )
        assert len(resp.products) == 1
        assert resp.source == "fedex"

    def test_model_dump(self):
        resp = StandardizedRateResponse(
            products=[RateProduct(name="FedEx Priority", price=45.0)],
            source="fedex",
        )
        data = resp.model_dump()
        assert data["products"][0]["name"] == "FedEx Priority"
        assert data["source"] == "fedex"

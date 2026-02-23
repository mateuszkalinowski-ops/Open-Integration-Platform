"""Tests for Raben Group integrator — Pydantic schemas."""

from __future__ import annotations

import pytest

from src.schemas import (
    Address,
    ClaimType,
    ContactInfo,
    CreateShipmentRequest,
    Package,
    PackageDimensions,
    PackageType,
    RabenCredentials,
    ServiceType,
    ShipmentParty,
    ShipmentStatus,
)


class TestRabenCredentials:
    def test_create_credentials_with_required_fields(self):
        creds = RabenCredentials(username="user", password="pass")
        assert creds.username == "user"
        assert creds.password == "pass"
        assert creds.customer_number is None
        assert creds.access_token is None
        assert creds.sandbox_mode is False

    def test_create_credentials_with_all_fields(self):
        creds = RabenCredentials(
            username="user",
            password="pass",
            customer_number="CUST-001",
            access_token="jwt-token",
            sandbox_mode=True,
        )
        assert creds.customer_number == "CUST-001"
        assert creds.access_token == "jwt-token"
        assert creds.sandbox_mode is True


class TestAddress:
    def test_create_address(self):
        addr = Address(
            street="Testowa 1",
            city="Warszawa",
            postalCode="00-001",
            countryCode="PL",
        )
        assert addr.street == "Testowa 1"
        assert addr.city == "Warszawa"
        assert addr.postal_code == "00-001"
        assert addr.country_code == "PL"

    def test_address_serialization_uses_aliases(self):
        addr = Address(
            street="Testowa 1",
            city="Warszawa",
            postalCode="00-001",
        )
        dumped = addr.model_dump(by_alias=True)
        assert "postalCode" in dumped
        assert "countryCode" in dumped


class TestPackage:
    def test_create_pallet_package(self):
        pkg = Package(
            packageType=PackageType.PALLET,
            quantity=2,
            weight=800.0,
            dimensions=PackageDimensions(length=120, width=80, height=150),
        )
        assert pkg.package_type == PackageType.PALLET
        assert pkg.quantity == 2
        assert pkg.weight == 800.0
        assert pkg.dimensions.length == 120

    def test_create_package_with_ldm(self):
        pkg = Package(weight=500.0, ldm=1.5)
        assert pkg.ldm == 1.5
        assert pkg.is_stackable is True


class TestServiceType:
    def test_all_service_types_exist(self):
        assert ServiceType.CARGO_CLASSIC == "cargo_classic"
        assert ServiceType.CARGO_PREMIUM == "cargo_premium"
        assert ServiceType.CARGO_PREMIUM_08 == "cargo_premium_08"
        assert ServiceType.CARGO_PREMIUM_10 == "cargo_premium_10"
        assert ServiceType.CARGO_PREMIUM_12 == "cargo_premium_12"
        assert ServiceType.CARGO_PREMIUM_16 == "cargo_premium_16"


class TestShipmentStatus:
    def test_all_statuses_exist(self):
        assert ShipmentStatus.CREATED == "created"
        assert ShipmentStatus.PICKED_UP == "picked_up"
        assert ShipmentStatus.IN_TRANSIT == "in_transit"
        assert ShipmentStatus.AT_TERMINAL == "at_terminal"
        assert ShipmentStatus.OUT_FOR_DELIVERY == "out_for_delivery"
        assert ShipmentStatus.DELIVERED == "delivered"
        assert ShipmentStatus.CANCELLED == "cancelled"
        assert ShipmentStatus.EXCEPTION == "exception"
        assert ShipmentStatus.RETURNED == "returned"


class TestClaimType:
    def test_all_claim_types_exist(self):
        assert ClaimType.DAMAGE == "damage"
        assert ClaimType.LOSS == "loss"
        assert ClaimType.DELAY == "delay"
        assert ClaimType.OTHER == "other"


class TestCreateShipmentRequest:
    def test_create_full_shipment_request(self):
        request = CreateShipmentRequest(
            credentials=RabenCredentials(username="user", password="pass"),
            sender=ShipmentParty(
                companyName="Sender Co",
                contactPerson="Jan",
                phone="+48123456789",
                street="Testowa 1",
                city="Warszawa",
                postalCode="00-001",
            ),
            receiver=ShipmentParty(
                companyName="Receiver Co",
                contactPerson="Anna",
                phone="+48987654321",
                street="Odbiorcza 2",
                city="Krakow",
                postalCode="30-001",
            ),
            packages=[Package(weight=500.0)],
            serviceType=ServiceType.CARGO_PREMIUM_10,
            pcdEnabled=True,
            emailNotification=True,
        )
        assert request.service_type == ServiceType.CARGO_PREMIUM_10
        assert request.pcd_enabled is True
        assert request.email_notification is True

    def test_create_minimal_shipment_request(self):
        request = CreateShipmentRequest(
            credentials=RabenCredentials(username="u", password="p"),
            sender=ShipmentParty(
                companyName="S", contactPerson="J", phone="1",
                street="S", city="W", postalCode="00-001",
            ),
            receiver=ShipmentParty(
                companyName="R", contactPerson="A", phone="2",
                street="R", city="K", postalCode="30-001",
            ),
            packages=[Package(weight=100.0)],
        )
        assert request.service_type == ServiceType.CARGO_CLASSIC
        assert request.cod is False
        assert request.pcd_enabled is False

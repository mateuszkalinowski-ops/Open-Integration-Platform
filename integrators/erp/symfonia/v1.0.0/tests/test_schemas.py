"""Tests for Pydantic schemas."""

from src.models.schemas import (
    Contractor,
    ContractorCreate,
    ContractorUpdate,
    ProductCreate,
    ProductUpdate,
)


class TestContractorCreate:
    def test_to_symfonia_payload_minimal(self):
        c = ContractorCreate(code="K001", name="Test Company")
        payload = c.to_symfonia_payload()

        assert payload == {"Code": "K001", "Name": "Test Company"}

    def test_to_symfonia_payload_full(self):
        c = ContractorCreate(
            code="K002",
            name="Full Company",
            short_name="FC",
            nip="1234567890",
            regon="123456789",
            street="ul. Testowa 1",
            city="Warszawa",
            postal_code="00-001",
            country="PL",
            phone="+48123456789",
            email="test@example.com",
        )
        payload = c.to_symfonia_payload()

        assert payload["Code"] == "K002"
        assert payload["Name"] == "Full Company"
        assert payload["ShortName"] == "FC"
        assert payload["Nip"] == "1234567890"
        assert payload["Street"] == "ul. Testowa 1"
        assert payload["City"] == "Warszawa"
        assert payload["PostalCode"] == "00-001"
        assert payload["Country"] == "PL"
        assert payload["Phone"] == "+48123456789"
        assert payload["Email"] == "test@example.com"


class TestContractorUpdate:
    def test_to_symfonia_payload_only_changed_fields(self):
        c = ContractorUpdate(id=1, name="Updated Name")
        payload = c.to_symfonia_payload()

        assert payload == {"Id": 1, "Name": "Updated Name"}
        assert "Code" not in payload

    def test_to_symfonia_payload_empty_gives_empty(self):
        c = ContractorUpdate()
        payload = c.to_symfonia_payload()
        assert payload == {}


class TestProductCreate:
    def test_to_symfonia_payload_minimal(self):
        p = ProductCreate(code="P001", name="Test Product")
        payload = p.to_symfonia_payload()

        assert payload == {"Code": "P001", "Name": "Test Product"}

    def test_to_symfonia_payload_with_optional_fields(self):
        p = ProductCreate(
            code="P002",
            name="Full Product",
            ean="5901234567890",
            vat_rate="23%",
            unit="szt",
            weight=1.5,
        )
        payload = p.to_symfonia_payload()

        assert payload["EAN"] == "5901234567890"
        assert payload["VatRate"] == "23%"
        assert payload["BaseUnitOfMeasure"] == "szt"
        assert payload["Weight"] == 1.5


class TestProductUpdate:
    def test_to_symfonia_payload_only_changed(self):
        p = ProductUpdate(id=1, name="Updated Product")
        payload = p.to_symfonia_payload()

        assert payload == {"Id": 1, "Name": "Updated Product"}


class TestContractorModel:
    def test_from_symfonia_response(self):
        data = {
            "Code": "K001",
            "Name": "Test sp. z o.o.",
            "Nip": "1234567890",
            "City": "Kraków",
        }
        c = Contractor(**data)

        assert c.code == "K001"
        assert c.name == "Test sp. z o.o."
        assert c.nip == "1234567890"
        assert c.city == "Kraków"

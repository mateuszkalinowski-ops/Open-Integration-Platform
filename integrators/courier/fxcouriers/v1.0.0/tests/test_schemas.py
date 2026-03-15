"""Tests for FX Couriers Pydantic schemas."""

from src.schemas import (
    CreateOrderApiRequest,
    CreatePickupApiRequest,
    FxAddress,
    FxCouriersCredentials,
    FxCreateOrderRequest,
    FxCreateShipmentRequest,
    FxItem,
    FxService,
    LabelRequest,
    OrderStatus,
    PaymentMethod,
)


def test_credentials_minimal():
    creds = FxCouriersCredentials(api_token="test-token-123")
    assert creds.api_token == "test-token-123"
    assert creds.company_id is None


def test_credentials_with_company_id():
    creds = FxCouriersCredentials(api_token="tok", company_id=42)
    assert creds.company_id == 42


def test_fx_address_serialization():
    addr = FxAddress(
        name="Test Sp. z o.o.",
        country="PL",
        city="Warszawa",
        postal_code="00-401",
        street="Marszalkowska",
        house_number="12",
        contact_person="Jan Kowalski",
        contact_phone="+48123456789",
        contact_email="jan@test.pl",
    )
    data = addr.model_dump()
    assert data["name"] == "Test Sp. z o.o."
    assert data["country"] == "PL"
    assert data["postal_code"] == "00-401"


def test_fx_item_defaults():
    item = FxItem(weight=20)
    assert item.package_type == "BOX"
    assert item.quantity == 1
    assert item.content == ""
    assert item.weight == 20


def test_fx_item_full():
    item = FxItem(
        content="Electronics",
        package_type="BOX",
        quantity=2,
        weight=15.5,
        width=30,
        height=20,
        length=40,
        comment="Fragile",
    )
    data = item.model_dump()
    assert data["weight"] == 15.5
    assert data["quantity"] == 2


def test_fx_service():
    svc = FxService(code="UBEZPIECZENIE", value="1400", quantity=1)
    assert svc.code == "UBEZPIECZENIE"
    assert svc.value == "1400"


def test_create_order_request_serialization():
    req = FxCreateOrderRequest(
        company_id=1,
        service_code="STANDARD",
        payment_method=PaymentMethod.TRANSFER,
        sender=FxAddress(
            name="Sender",
            city="Warszawa",
            postal_code="00-401",
            street="Marszalkowska",
            house_number="12",
        ),
        recipient=FxAddress(
            name="Recipient",
            city="Krakow",
            postal_code="30-001",
            street="Florianska",
            house_number="5",
        ),
        items=[FxItem(weight=10, content="Books")],
        services=[FxService(code="UBEZPIECZENIE", value="500")],
    )
    data = req.model_dump(exclude_none=True)
    assert data["company_id"] == 1
    assert data["service_code"] == "STANDARD"
    assert len(data["items"]) == 1
    assert len(data["services"]) == 1


def test_create_shipment_request():
    req = FxCreateShipmentRequest(
        pickup_date="2026-03-01",
        pickup_time_from="10:00",
        pickup_time_to="14:00",
        order_id_list=[1, 2, 3],
    )
    data = req.model_dump()
    assert data["pickup_date"] == "2026-03-01"
    assert data["order_id_list"] == [1, 2, 3]


def test_label_request():
    req = LabelRequest(
        credentials=FxCouriersCredentials(api_token="tok"),
        order_id=42,
    )
    assert req.order_id == 42


def test_order_status_enum():
    assert OrderStatus.NEW == "NEW"
    assert OrderStatus.CLOSED == "CLOSED"
    assert OrderStatus.CANCELLED == "CANCELLED"


def test_payment_method_enum():
    assert PaymentMethod.CASH == "CASH"
    assert PaymentMethod.TRANSFER == "TRANSFER"


def test_create_order_api_request():
    req = CreateOrderApiRequest(
        credentials=FxCouriersCredentials(api_token="tok"),
        company_id=1,
        service_code="STANDARD",
        sender=FxAddress(
            name="A",
            city="W",
            postal_code="00-001",
            street="S",
            house_number="1",
        ),
        recipient=FxAddress(
            name="B",
            city="K",
            postal_code="30-001",
            street="F",
            house_number="2",
        ),
        items=[FxItem(weight=5)],
    )
    assert req.credentials.api_token == "tok"
    assert req.company_id == 1


def test_create_pickup_api_request():
    req = CreatePickupApiRequest(
        credentials=FxCouriersCredentials(api_token="tok"),
        pickup_date="2026-03-01",
        pickup_time_from="09:00",
        pickup_time_to="12:00",
        order_id_list=[10, 20],
    )
    assert req.order_id_list == [10, 20]

"""Shared test fixtures for BaseLinker integrator tests."""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("BASELINKER_SCRAPING_ENABLED", "false")
os.environ.setdefault("KAFKA_ENABLED", "false")


@pytest.fixture
def sample_bl_order() -> dict:
    return {
        "order_id": 77001,
        "shop_order_id": 0,
        "external_order_id": "",
        "order_source": "personal",
        "order_source_id": 0,
        "order_source_info": "",
        "order_status_id": 12345,
        "confirmed": True,
        "date_add": 1708000000,
        "date_confirmed": 1708000100,
        "date_in_status": 1708000200,
        "user_login": "jan.kowalski",
        "phone": "+48123456789",
        "email": "jan.kowalski@example.com",
        "user_comments": "Prosze o szybka wysylke",
        "admin_comments": "",
        "currency": "PLN",
        "payment_method": "Przelew",
        "payment_method_cod": "",
        "payment_done": 199.99,
        "delivery_method": "InPost Paczkomaty",
        "delivery_price": 12.99,
        "delivery_fullname": "Jan Kowalski",
        "delivery_company": "",
        "delivery_address": "ul. Marszalkowska 1/5",
        "delivery_city": "Warszawa",
        "delivery_postcode": "00-001",
        "delivery_country_code": "PL",
        "delivery_point_id": "WAW01M",
        "delivery_point_name": "Paczkomat Warszawa 01",
        "delivery_point_address": "ul. Nowy Swiat 10",
        "delivery_point_postcode": "00-002",
        "delivery_point_city": "Warszawa",
        "invoice_fullname": "Jan Kowalski",
        "invoice_company": "Firma Sp. z o.o.",
        "invoice_nip": "1234567890",
        "invoice_address": "ul. Marszalkowska 1/5",
        "invoice_city": "Warszawa",
        "invoice_postcode": "00-001",
        "invoice_country_code": "PL",
        "want_invoice": "1",
        "extra_field_1": "",
        "extra_field_2": "",
        "products": [
            {
                "storage": "db",
                "storage_id": 0,
                "order_product_id": 90001,
                "product_id": "5001",
                "variant_id": 0,
                "name": "Koszulka polo niebieska",
                "sku": "POLO-BLU-001",
                "ean": "5901234123457",
                "location": "",
                "warehouse_id": 1,
                "attributes": "Rozmiar: L",
                "price_brutto": 89.99,
                "tax_rate": 23,
                "quantity": 2,
                "weight": 0.3,
            },
            {
                "storage": "db",
                "storage_id": 0,
                "order_product_id": 90002,
                "product_id": "5002",
                "variant_id": 0,
                "name": "Czapka z daszkiem",
                "sku": "CAP-BLK-001",
                "ean": "5901234123458",
                "location": "",
                "warehouse_id": 1,
                "attributes": "",
                "price_brutto": 29.99,
                "tax_rate": 23,
                "quantity": 1,
                "weight": 0.1,
            },
        ],
    }


@pytest.fixture
def sample_bl_status_defs() -> dict[int, str]:
    return {
        12345: "Nowe zamowienie",
        12346: "W realizacji",
        12347: "Gotowe do wysylki",
        12348: "Wyslane",
        12349: "Dostarczone",
        12350: "Anulowane",
        12351: "Zwrot",
    }


@pytest.fixture
def sample_bl_product() -> dict:
    return {
        "id": 5001,
        "ean": "5901234123457",
        "sku": "POLO-BLU-001",
        "name": "Koszulka polo niebieska",
        "prices": {"1": 89.99, "2": 79.99},
        "stock": {"1": 150.0, "2": 50.0},
        "category_id": 10,
        "text_fields": {
            "name": "Koszulka polo niebieska",
            "description": "Elegancka koszulka polo w kolorze niebieskim",
        },
        "weight": 0.3,
        "tax_rate": 23,
    }

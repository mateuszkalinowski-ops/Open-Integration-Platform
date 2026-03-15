"""Shared test fixtures for Shoper integrator tests."""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SHOPER_SCRAPING_ENABLED", "false")
os.environ.setdefault("KAFKA_ENABLED", "false")


@pytest.fixture
def sample_shoper_order() -> dict:
    return {
        "order_id": 12345,
        "user_id": 100,
        "date": "2026-02-20 10:30:00",
        "status_id": "2",
        "sum": 199.99,
        "payment_id": 1,
        "shipping_id": 5,
        "shipping_cost": 15.00,
        "email": "jan.kowalski@example.com",
        "code": "ZAM/2026/12345",
        "notes": "Prosze o szybka wysylke",
        "billing_address": {
            "firstname": "Jan",
            "lastname": "Kowalski",
            "company": "Firma Sp. z o.o.",
            "city": "Warszawa",
            "postcode": "00-001",
            "street1": "ul. Marszalkowska 1",
            "country_code": "PL",
            "phone": "+48123456789",
        },
        "delivery_address": {
            "firstname": "Jan",
            "lastname": "Kowalski",
            "city": "Warszawa",
            "postcode": "00-001",
            "street1": "ul. Marszalkowska 1",
            "country_code": "PL",
            "phone": "+48123456789",
        },
    }


@pytest.fixture
def sample_order_products() -> list[dict]:
    return [
        {
            "id": 1,
            "order_id": 12345,
            "product_id": 500,
            "price": 99.99,
            "quantity": 2.0,
            "name": "Koszulka polo",
            "code": "POLO-001",
            "unit": "szt.",
            "weight": 0.3,
        },
    ]


@pytest.fixture
def sample_shoper_product() -> dict:
    return {
        "product_id": 500,
        "code": "POLO-001",
        "ean": "5901234123457",
        "category_id": 10,
        "unit_id": 1,
        "dimension_w": 30.0,
        "dimension_h": 5.0,
        "dimension_l": 40.0,
        "vol_weight": 0.3,
        "stock": {
            "stock_id": 500,
            "product_id": 500,
            "price": 99.99,
            "stock": 150.0,
            "ean": "5901234123457",
        },
        "translations": {
            "pl_PL": {
                "name": "Koszulka polo",
                "description": "Elegancka koszulka polo",
                "active": True,
            },
        },
    }


@pytest.fixture
def sample_auth_response() -> dict:
    return {
        "access_token": "test_token_abc123",
        "expires_in": 3600,
        "token_type": "bearer",
    }

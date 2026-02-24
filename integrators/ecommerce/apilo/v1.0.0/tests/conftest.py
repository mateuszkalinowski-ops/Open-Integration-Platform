"""Shared test fixtures for Apilo integrator tests."""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("APILO_SCRAPING_ENABLED", "false")
os.environ.setdefault("KAFKA_ENABLED", "false")


@pytest.fixture
def sample_apilo_order() -> dict:
    return {
        "id": "AL231100017",
        "status": 3,
        "idExternal": "WWW/341/2023",
        "isInvoice": True,
        "customerLogin": "user123",
        "paymentStatus": 2,
        "paymentType": 2,
        "originalCurrency": "PLN",
        "originalAmountTotalWithoutTax": 1024.37,
        "originalAmountTotalWithTax": 1259.98,
        "originalAmountTotalPaid": 1259.98,
        "isEncrypted": False,
        "createdAt": "2022-06-09T10:59:12Z",
        "updatedAt": "2022-06-09T10:59:12Z",
        "orderedAt": "2022-06-09T10:59:12+0100",
        "orderItems": [
            {
                "id": 1,
                "idExternal": "359",
                "ean": "400638133393",
                "sku": "P44/3-T1.2",
                "originalName": "Samsung Galaxy S20 Plus Black 128GB 5G",
                "originalCode": "PHONE-S20-128GB-B",
                "originalPriceWithTax": "2799.99",
                "originalPriceWithoutTax": "2799.99",
                "media": None,
                "quantity": 2,
                "tax": "23.00",
                "productSet": None,
                "status": 1,
                "unit": "Szt.",
                "type": 1,
                "productId": 12345,
            },
            {
                "id": 2,
                "idExternal": None,
                "ean": None,
                "sku": "ship-pp",
                "originalName": "Wysyłka - Poczta Polska - Pocztex",
                "originalCode": None,
                "originalPriceWithTax": "10.00",
                "originalPriceWithoutTax": "10.00",
                "media": None,
                "quantity": 1,
                "tax": None,
                "productSet": None,
                "status": 1,
                "unit": None,
                "type": 2,
                "productId": None,
            },
        ],
        "addressCustomer": {
            "id": 123,
            "name": "Jan Kowalski",
            "phone": "+48 500 000 000",
            "email": "jan.kowalski@apilo.com",
            "streetName": "Testowa",
            "streetNumber": "4b/12",
            "city": "Kraków",
            "zipCode": "31-154",
            "country": "PL",
            "department": "",
            "parcelIdExternal": "KRA32B",
            "parcelName": "Paczkomat, ul. Testowa 12 (obok sklepu)",
            "companyTaxNumber": "937-271-51-54",
            "companyName": "Apilo Sp. z o.o.",
        },
        "addressDelivery": {
            "id": 123,
            "name": "Jan Kowalski",
            "phone": "+48 500 000 000",
            "email": "jan.kowalski@apilo.com",
            "streetName": "Testowa",
            "streetNumber": "4b/12",
            "city": "Kraków",
            "zipCode": "31-154",
            "country": "PL",
            "department": "",
        },
        "addressInvoice": {
            "id": 123,
            "name": "Jan Kowalski",
            "phone": "+48 500 000 000",
            "email": "jan.kowalski@apilo.com",
            "streetName": "Testowa",
            "streetNumber": "4b/12",
            "city": "Kraków",
            "zipCode": "31-154",
            "country": "PL",
            "companyTaxNumber": "937-271-51-54",
            "companyName": "Apilo Sp. z o.o.",
        },
        "carrierAccount": 1,
        "orderNotes": [
            {
                "id": 221,
                "type": 2,
                "createdAt": "2024-01-23T09:29:30+0100",
                "comment": "Prosze o dostawe w przyszlym tygodniu",
            }
        ],
        "platformId": 1,
        "isCanceledByBuyer": False,
        "carrierId": 1,
        "platformAccountId": 1,
    }


@pytest.fixture
def sample_apilo_product() -> dict:
    return {
        "id": 1234,
        "name": "Samsung Galaxy S20 Plus Black 128GB",
        "groupName": "Samsung Galaxy S20 Plus",
        "productGroupId": 123456,
        "sku": "HG-331/P",
        "ean": "4006381333931",
        "originalCode": "p12345",
        "quantity": 15,
        "priceWithTax": 123.0,
        "priceWithoutTax": 100.0,
        "tax": "23.00",
        "status": 1,
        "unit": "Szt.",
        "weight": 1.12,
        "categories": [12, 44, 149],
    }


@pytest.fixture
def sample_apilo_status_map() -> list[dict]:
    return [
        {"id": 7, "key": "STATUS_7", "name": "Nowy", "description": "Nowy"},
        {"id": 8, "key": "STATUS_8", "name": "Niepotwierdzone", "description": "Niepotwierdzone"},
        {"id": 9, "key": "STATUS_9", "name": "W realizacji", "description": "W realizacji"},
        {"id": 10, "key": "STATUS_10", "name": "Do wysyłki", "description": "Do wysyłki"},
        {"id": 11, "key": "STATUS_11", "name": "Wysłane", "description": "Wysłane"},
        {"id": 12, "key": "STATUS_12", "name": "Dostarczone", "description": "Dostarczone"},
        {"id": 13, "key": "STATUS_13", "name": "Anulowane", "description": "Anulowane"},
        {"id": 14, "key": "STATUS_14", "name": "Zwrot", "description": "Zwrot"},
    ]

"""Shared test fixtures for Amazon integrator tests."""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("AMAZON_SCRAPING_ENABLED", "false")
os.environ.setdefault("KAFKA_ENABLED", "false")


@pytest.fixture
def sample_amazon_order() -> dict:
    return {
        "AmazonOrderId": "114-1234567-8901234",
        "SellerOrderId": "114-1234567-8901234",
        "PurchaseDate": "2026-02-20T14:30:00Z",
        "LastUpdateDate": "2026-02-20T15:00:00Z",
        "OrderStatus": "Unshipped",
        "FulfillmentChannel": "MFN",
        "SalesChannel": "Amazon.de",
        "ShipServiceLevel": "Std DE Dom",
        "OrderTotal": {"CurrencyCode": "EUR", "Amount": "59.98"},
        "NumberOfItemsShipped": 0,
        "NumberOfItemsUnshipped": 2,
        "PaymentMethod": "Other",
        "PaymentMethodDetails": ["Standard"],
        "MarketplaceId": "A1PA6795UKMFR9",
        "OrderType": "StandardOrder",
        "EarliestShipDate": "2026-02-21T00:00:00Z",
        "LatestShipDate": "2026-02-23T23:59:59Z",
        "IsBusinessOrder": False,
        "IsPrime": False,
        "BuyerInfo": {
            "BuyerEmail": "buyer123@marketplace.amazon.de",
            "BuyerName": "Max Mustermann",
        },
        "ShippingAddress": {
            "Name": "Max Mustermann",
            "AddressLine1": "Musterstrasse 42",
            "AddressLine2": "",
            "AddressLine3": "",
            "City": "Berlin",
            "StateOrRegion": "Berlin",
            "PostalCode": "10115",
            "CountryCode": "DE",
            "Phone": "+49301234567",
        },
    }


@pytest.fixture
def sample_amazon_order_items() -> list[dict]:
    return [
        {
            "ASIN": "B0EXAMPLE01",
            "SellerSKU": "SKU-TSHIRT-BLU-L",
            "OrderItemId": "11111111111111",
            "Title": "Blue T-Shirt Large",
            "QuantityOrdered": 1,
            "QuantityShipped": 0,
            "ItemPrice": {"CurrencyCode": "EUR", "Amount": "29.99"},
            "ItemTax": {"CurrencyCode": "EUR", "Amount": "5.70"},
            "ShippingPrice": {"CurrencyCode": "EUR", "Amount": "0.00"},
        },
        {
            "ASIN": "B0EXAMPLE02",
            "SellerSKU": "SKU-CAP-BLK",
            "OrderItemId": "22222222222222",
            "Title": "Black Baseball Cap",
            "QuantityOrdered": 1,
            "QuantityShipped": 0,
            "ItemPrice": {"CurrencyCode": "EUR", "Amount": "29.99"},
            "ItemTax": {"CurrencyCode": "EUR", "Amount": "5.70"},
            "ShippingPrice": {"CurrencyCode": "EUR", "Amount": "0.00"},
        },
    ]


@pytest.fixture
def sample_amazon_catalog_item() -> dict:
    return {
        "asin": "B0EXAMPLE01",
        "summaries": [
            {
                "marketplaceId": "A1PA6795UKMFR9",
                "brandName": "ExampleBrand",
                "itemName": "Blue T-Shirt Large",
                "manufacturer": "ExampleManufacturer",
                "modelNumber": "TS-BLU-L",
            }
        ],
        "identifiers": [
            {
                "marketplaceId": "A1PA6795UKMFR9",
                "identifiers": [
                    {"identifierType": "EAN", "identifier": "4012345678901"},
                ],
            }
        ],
        "images": [],
        "attributes": {},
    }

"""Tier 3 functional checks — DHL Express courier connector.

Tests all read-only endpoints:
- GET  /shipments/{tracking_number}/status   (tracking)
- POST /rates                                (rating)
- POST /rates/standardized                   (standardised rates)
- GET  /products                             (available products)
- GET  /shipments/{tracking_number}/label     (label retrieval)
- GET  /shipments/{tracking_number}/documents (shipment documents)
- GET  /address-validate                     (address validation)
- GET  /points                               (service points / locations)
- POST /landed-cost                          (landed cost estimation)
- POST /shipments                            (create shipment — sandbox)
- POST /pickups                              (create pickup — sandbox)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from src.checks.common import req_check
from src.discovery import VerificationTarget

DUMMY_TRACKING = "1234567890"


def _future_date() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=3)
    return dt.strftime("%Y-%m-%dT14:00:00GMT+01:00")


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url

    # --- Address validation (read-only, lightweight) ---
    addr_check, _ = await req_check(
        client, "GET",
        f"{base}/address-validate",
        "address_validate",
        params={
            "countryCode": "PL",
            "postalCode": "00-001",
            "cityName": "Warszawa",
            "type": "delivery",
        },
        accept_statuses=(200, 401),
    )
    results.append(addr_check)

    # --- Service points / locations ---
    points_check, _ = await req_check(
        client, "GET",
        f"{base}/points",
        "service_points",
        params={
            "countryCode": "PL",
            "postalCode": "00-001",
            "cityName": "Warszawa",
            "maxResults": "5",
        },
        accept_statuses=(200, 401),
    )
    results.append(points_check)

    # --- Tracking (dummy number — expect 404 or 401 with invalid creds) ---
    track_check, _ = await req_check(
        client, "GET",
        f"{base}/shipments/{DUMMY_TRACKING}/status",
        "get_tracking_status",
        accept_statuses=(200, 400, 401, 404),
    )
    results.append(track_check)

    # --- Rates ---
    rate_payload = {
        "shipper_postal_code": "00-001",
        "shipper_city": "Warszawa",
        "shipper_country_code": "PL",
        "receiver_postal_code": "10115",
        "receiver_city": "Berlin",
        "receiver_country_code": "DE",
        "planned_shipping_date": _future_date(),
        "unit_of_measurement": "metric",
        "is_customs_declarable": False,
        "weight": 1.5,
        "length": 30,
        "width": 20,
        "height": 15,
    }
    rate_check, rate_resp = await req_check(
        client, "POST",
        f"{base}/rates",
        "get_rates",
        json_body=rate_payload,
        accept_statuses=(200, 400, 401),
    )
    results.append(rate_check)

    # --- Standardised rates ---
    std_rate_check, _ = await req_check(
        client, "POST",
        f"{base}/rates/standardized",
        "get_rates_standardized",
        json_body=rate_payload,
        accept_statuses=(200, 400, 401),
    )
    results.append(std_rate_check)

    # --- Products ---
    products_check, _ = await req_check(
        client, "GET",
        f"{base}/products",
        "get_products",
        params={
            "originCountryCode": "PL",
            "originPostalCode": "00-001",
            "receiverCountryCode": "DE",
            "receiverPostalCode": "10115",
            "weight": "1.5",
            "plannedShippingDate": _future_date(),
            "isCustomsDeclarable": "false",
            "unitOfMeasurement": "metric",
        },
        accept_statuses=(200, 401),
    )
    results.append(products_check)

    # --- Label retrieval (dummy tracking — expect 400/401/404) ---
    label_check, _ = await req_check(
        client, "GET",
        f"{base}/shipments/{DUMMY_TRACKING}/label",
        "get_label",
        accept_statuses=(200, 400, 401, 404),
    )
    results.append(label_check)

    # --- Documents (dummy tracking — expect 400/401/404) ---
    doc_check, _ = await req_check(
        client, "GET",
        f"{base}/shipments/{DUMMY_TRACKING}/documents",
        "get_documents",
        params={"typeCode": "label"},
        accept_statuses=(200, 400, 401, 404),
    )
    results.append(doc_check)

    # --- Landed cost ---
    landed_payload = {
        "accounts": [{"typeCode": "shipper", "number": "123456789"}],
        "productCode": "P",
        "unitOfMeasurement": "metric",
        "currencyCode": "EUR",
        "isCustomsDeclarable": True,
        "isDTPRequested": False,
        "isInsuranceRequested": False,
        "shipmentPurpose": "commercial",
        "packages": [{
            "weight": 1.0,
            "dimensions": {"length": 30, "width": 20, "height": 15},
        }],
        "items": [{
            "number": 1,
            "name": "Test Item",
            "quantity": 1,
            "quantityType": "pcs",
            "unitPrice": 50.0,
            "unitPriceCurrencyCode": "EUR",
            "weight": {"netValue": 1.0, "grossValue": 1.0},
        }],
        "shipperAddress": {
            "postalCode": "00-001",
            "cityName": "Warszawa",
            "countryCode": "PL",
        },
        "receiverAddress": {
            "postalCode": "10115",
            "cityName": "Berlin",
            "countryCode": "DE",
        },
    }
    landed_check, _ = await req_check(
        client, "POST",
        f"{base}/landed-cost",
        "get_landed_cost",
        json_body=landed_payload,
        accept_statuses=(200, 400, 401, 422, 500),
    )
    results.append(landed_check)

    # --- Create shipment (sandbox — accept various codes) ---
    shipment_payload = {
        "planned_shipping_date": _future_date(),
        "pickup": {
            "is_requested": False,
        },
        "product_code": "N",
        "accounts": [
            {"type_code": "shipper", "number": "123456789"},
        ],
        "customer_details": {
            "shipper_details": {
                "postal_address": {
                    "postal_code": "00-001",
                    "city_name": "Warszawa",
                    "country_code": "PL",
                    "address_line1": "Testowa 1",
                },
                "contact_information": {
                    "company_name": "Test Shipper",
                    "full_name": "Test User",
                    "phone": "+48123456789",
                    "email": "test@example.com",
                },
            },
            "receiver_details": {
                "postal_address": {
                    "postal_code": "10115",
                    "city_name": "Berlin",
                    "country_code": "DE",
                    "address_line1": "Teststr. 1",
                },
                "contact_information": {
                    "company_name": "Test Receiver",
                    "full_name": "Test Empfanger",
                    "phone": "+491234567890",
                    "email": "test@example.de",
                },
            },
        },
        "content": {
            "packages": [{
                "weight": 1.5,
                "dimensions": {"length": 30, "width": 20, "height": 15},
            }],
            "is_customs_declarable": False,
            "description": "Verification test",
            "incoterm_code": "DAP",
            "unit_of_measurement": "metric",
        },
    }
    ship_check, _ = await req_check(
        client, "POST",
        f"{base}/shipments",
        "create_shipment",
        json_body=shipment_payload,
        accept_statuses=(200, 201, 400, 422),
    )
    results.append(ship_check)

    # --- Create pickup (sandbox — accept various codes) ---
    pickup_payload = {
        "planned_pickup_date_and_time": _future_date(),
        "close_time": "18:00",
        "location": "reception",
        "special_instructions": [{"value": "Verification test"}],
        "accounts": [
            {"type_code": "shipper", "number": "123456789"},
        ],
        "customer_details": {
            "shipper_details": {
                "postal_address": {
                    "postal_code": "00-001",
                    "city_name": "Warszawa",
                    "country_code": "PL",
                    "address_line1": "Testowa 1",
                },
                "contact_information": {
                    "company_name": "Test Company",
                    "full_name": "Test User",
                    "phone": "+48123456789",
                },
            },
        },
    }
    pickup_check, _ = await req_check(
        client, "POST",
        f"{base}/pickups",
        "create_pickup",
        json_body=pickup_payload,
        accept_statuses=(200, 201, 400, 422),
    )
    results.append(pickup_check)

    return results

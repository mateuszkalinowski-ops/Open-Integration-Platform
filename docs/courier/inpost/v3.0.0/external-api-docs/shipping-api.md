# InPost International API 2025 (Global API) — Shipping API v2

> Source: https://developers.inpost-group.com/shipping

## Overview

The Shipping API v2 provides synchronous shipment creation — tracking numbers are returned immediately in the creation response. All endpoints are organization-scoped and support multi-parcel shipments.

**Base path**: `/shipping/v2/organizations/{organizationId}`

## Endpoints

### Create Shipment

```
POST /shipping/v2/organizations/{organizationId}/shipments
Authorization: Bearer {token}
Content-Type: application/json
```

#### Optional Headers

| Header | Description |
|---|---|
| `X-Inpost-Deduplication-Id` | Idempotency key to prevent duplicate shipment creation |

#### Request Body (`ShippingCreateShipmentDto`)

```json
{
    "enableDropOffCode": null,
    "sender": {
        "companyName": "Sender Corp",
        "firstName": "Jan",
        "lastName": "Kowalski",
        "phone": "+48123456789",
        "email": "jan@example.com",
        "languageCode": "PL"
    },
    "recipient": {
        "companyName": null,
        "firstName": "Anna",
        "lastName": "Nowak",
        "phone": "+48987654321",
        "email": "anna@example.com",
        "languageCode": "PL"
    },
    "origin": {
        "countryCode": "PL",
        "street": "Testowa",
        "houseNumber": "1",
        "flatNumber": null,
        "city": "Warszawa",
        "postalCode": "00-001"
    },
    "destination": {
        "countryCode": "DE",
        "street": "Hauptstraße",
        "houseNumber": "5",
        "flatNumber": null,
        "city": "Berlin",
        "postalCode": "10115"
    },
    "returnDestination": null,
    "references": "Order #12345",
    "valueAddedServices": [
        {
            "id": "additionalCover",
            "value": "1000",
            "currency": "EUR"
        },
        {
            "id": "priority",
            "value": "EXPRESS"
        }
    ],
    "parcels": [
        {
            "dimensions": {
                "length": 30,
                "width": 20,
                "height": 10,
                "unit": "CM"
            },
            "weight": {
                "amount": 2.5,
                "unit": "KG"
            }
        },
        {
            "dimensions": {
                "length": 40,
                "width": 30,
                "height": 20,
                "unit": "CM"
            },
            "weight": {
                "amount": 5.0,
                "unit": "KG"
            }
        }
    ]
}
```

#### Key differences from 2024 API

1. **Contact info**: Phone is a simple string (not object with prefix/number)
2. **Language code**: Added `languageCode` field to contact info
3. **Origin/destination**: Always address-based (unified structure, no point-specific variants)
4. **References**: Simple string (not nested custom object)
5. **Value-added services**: Array of service objects with `id`, `value`, optional `currency`
6. **Parcels**: Array — multi-parcel support
7. **Dimensions/weight**: Numeric values (not strings)

#### Response

```json
{
    "trackingNumber": "620000000001234567"
}
```

The tracking number is returned **synchronously** — no need for a second call to retrieve it.

### Get Shipment Label

```
GET /shipping/v2/organizations/{organizationId}/shipments/{trackingNumber}/label
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json
```

The `Accept` header determines the label format. Use `application/json` for JSON + base64 response:

```json
{
    "label": {
        "content": "JVBERi0xLjQK..."
    }
}
```

Or use specific format headers for raw output (see [api-reference.md](api-reference.md#label-formats)).

### Get Shipment Details

```
GET /shipping/v2/organizations/{organizationId}/shipments/{trackingNumber}
Authorization: Bearer {token}
Content-Type: application/json
```

Returns full shipment object with current status, sender/receiver, parcels, and tracking info.

## Data Structures

### ShippingContactInfo

| Field | Type | Required | Description |
|---|---|---|---|
| `companyName` | string | No | Company name |
| `firstName` | string | Yes | First name |
| `lastName` | string | Yes | Last name |
| `phone` | string | Yes | Full phone number (e.g., "+48123456789") |
| `email` | string | Yes | Email address |
| `languageCode` | string | No | Language preference (ISO2) |

### ShippingAddress

| Field | Type | Required | Description |
|---|---|---|---|
| `countryCode` | string | Yes | ISO2 country code |
| `street` | string | Yes | Street name |
| `houseNumber` | string | Yes | Building number |
| `flatNumber` | string | No | Flat/apartment number |
| `city` | string | Yes | City name |
| `postalCode` | string | Yes | Postal code |

### StandardParcel

| Field | Type | Required | Description |
|---|---|---|---|
| `dimensions` | Dimensions | Yes | Parcel dimensions |
| `weight` | Weight | Yes | Parcel weight |

### Dimensions

| Field | Type | Description |
|---|---|---|
| `length` | number | Length |
| `width` | number | Width |
| `height` | number | Height |
| `unit` | string | Unit — `CM` |

### Weight

| Field | Type | Description |
|---|---|---|
| `amount` | number | Weight value |
| `unit` | string | Unit — `KG` |

## Value-Added Services

| Service ID | Type | Description |
|---|---|---|
| `additionalCover` | CurrencyValueAdded | Insurance coverage (requires `value` and `currency`) |
| `priority` | StandardValueAdded | Priority level: `STANDARD`, `EXPRESS` |

### CurrencyValueAdded

```json
{
    "id": "additionalCover",
    "value": "1000",
    "currency": "EUR"
}
```

### StandardValueAdded

```json
{
    "id": "priority",
    "value": "EXPRESS"
}
```

# InPost International API 2025 (Global API) — Returns API v1

> Source: https://developers.inpost-group.com/

## Overview

The Returns API v1 is **new in the 2025 Global API** — it provides dedicated endpoints for creating and managing return shipments. The 2024 API did not have a returns module.

**Base path**: `/returns/v1/organizations/{organizationId}`

## Endpoints

### Create Return Shipment

```
POST /returns/v1/organizations/{organizationId}/shipments
Authorization: Bearer {token}
Content-Type: application/json
```

#### Request Body (`ReturnsCreateShipmentDto`)

```json
{
    "enableDropOffCode": true,
    "sender": {
        "companyName": null,
        "firstName": "Anna",
        "lastName": "Nowak",
        "phone": "+48987654321",
        "email": "anna@example.com"
    },
    "origin": {
        "countryCode": "PL"
    },
    "destination": {
        "countryCode": "PL",
        "street": "Magazynowa",
        "houseNumber": "10",
        "flatNumber": null,
        "city": "Warszawa",
        "postalCode": "00-001"
    },
    "references": {
        "clientId": "CLIENT-001",
        "orderNumber": "ORD-2025-12345"
    },
    "parcels": [
        {
            "dimensions": {
                "length": 30,
                "width": 20,
                "height": 10,
                "unit": "CM"
            },
            "weight": {
                "amount": "2.5",
                "unit": "KG"
            }
        }
    ]
}
```

#### Response

```json
{
    "shipmentId": "ret-f47ac10b-58cc-4372",
    "parcels": [
        {
            "tracking_number": "620000000009876543"
        }
    ],
    "status": "CREATED"
}
```

### Get Return Shipment Information

```
GET /returns/v1/organizations/{organizationId}/shipments/{shipmentId}
Authorization: Bearer {token}
Content-Type: application/json
```

Returns full return shipment details including parcel tracking numbers.

#### Response

```json
{
    "shipmentId": "ret-f47ac10b-58cc-4372",
    "parcels": [
        {
            "tracking_number": "620000000009876543"
        }
    ],
    "status": "CREATED",
    "sender": { ... },
    "destination": { ... }
}
```

### Get Return Shipment Label

```
GET /returns/v1/organizations/{organizationId}/shipments/{trackingNumber}/label
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json
```

Returns the return label in JSON + base64 format:

```json
{
    "label": {
        "content": "JVBERi0xLjQK..."
    }
}
```

Decode the `content` field from base64 to get the PDF bytes.

## Data Structures

### ReturnsContactInfo

| Field | Type | Required | Description |
|---|---|---|---|
| `companyName` | string | No | Company name |
| `firstName` | string | Yes | Sender first name |
| `lastName` | string | Yes | Sender last name |
| `phone` | string | Yes | Full phone number |
| `email` | string | Yes | Email address |

### ReturnsOrigin

| Field | Type | Required | Description |
|---|---|---|---|
| `countryCode` | string | Yes | Origin country (ISO2) |

The origin specifies only the country — the sender drops off at a nearby InPost point.

### ReturnsAddress (destination)

| Field | Type | Required | Description |
|---|---|---|---|
| `countryCode` | string | Yes | Destination country (ISO2) |
| `street` | string | Yes | Street name |
| `houseNumber` | string | Yes | Building number |
| `flatNumber` | string | No | Flat/apartment number |
| `city` | string | Yes | City name |
| `postalCode` | string | Yes | Postal code |

### ReturnsReferences

| Field | Type | Required | Description |
|---|---|---|---|
| `clientId` | string | No | Client identifier |
| `orderNumber` | string | No | Order number |

### ReturnsParcel

| Field | Type | Required | Description |
|---|---|---|---|
| `dimensions` | ReturnsDimensions | No | Parcel dimensions |
| `weight` | ReturnsWeight | No | Parcel weight |

### ReturnsDimensions

| Field | Type | Description |
|---|---|---|
| `length` | number | Length |
| `width` | number | Width |
| `height` | number | Height |
| `unit` | string | Unit — `CM` |

### ReturnsWeight

| Field | Type | Description |
|---|---|---|
| `amount` | string | Weight value |
| `unit` | string | Unit — `KG` |

## Additional Parameters

| Parameter | Type | Description |
|---|---|---|
| `enableDropOffCode` | boolean | If true, generates a drop-off code for locker access |

# InPost International API 2025 (Global API) — Pickups API v1

> Source: https://developers.inpost-group.com/pickups

## Overview

The Pickups API v1 manages one-time courier pickup orders. All endpoints are organization-scoped. The 2025 API adds pickup cancellation support compared to the 2024 version.

**Base path**: `/pickups/v1`

**Availability**: Ordering via API is currently supported only in Poland.

## Endpoints

### Create Pickup Order

```
POST /pickups/v1/organizations/{organizationId}/one-time-pickups
Authorization: Bearer {token}
Content-Type: application/json
```

#### Request Body (`PickupsCreatePickupOrderDto`)

```json
{
    "address": {
        "countryCode": "PL",
        "street": "Testowa",
        "houseNumber": "1",
        "flatNumber": null,
        "city": "Warszawa",
        "postalCode": "00-001"
    },
    "contactPerson": {
        "firstName": "Jan",
        "lastName": "Kowalski",
        "phone": {
            "prefix": "+48",
            "number": "123456789"
        },
        "email": "jan@example.com"
    },
    "pickupTime": {
        "from": "2025-06-15T09:00:00+02:00",
        "to": "2025-06-15T12:00:00+02:00"
    },
    "references": {
        "custom": {
            "content": "Batch #12345"
        }
    },
    "volume": {
        "itemType": "PARCEL",
        "count": 5,
        "totalVolume": {
            "amount": 5,
            "unit": "L"
        }
    },
    "trackingNumbers": ["620000000001234567"]
}
```

Key difference from 2024 API:
- `trackingNumbers` array — associates specific shipments with the pickup
- `totalVolume` instead of `totalWeight`

#### Response

Returns the created pickup order object with assigned ID and status.

### List Pickup Orders

```
GET /pickups/v1/organizations/{organizationId}/one-time-pickups
Authorization: Bearer {token}
Content-Type: application/json
```

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page` | int | No | Page number |
| `size` | int | No | Page size |

### Get Pickup Order by ID

```
GET /pickups/v1/organizations/{organizationId}/one-time-pickups/{orderId}
Authorization: Bearer {token}
Content-Type: application/json
```

### Cancel Pickup Order

```
PUT /pickups/v1/organizations/{organizationId}/one-time-pickups/{orderId}/cancel
Authorization: Bearer {token}
Content-Type: application/json
```

Cancels an existing pickup order. This endpoint is **new in the 2025 API** — the 2024 version did not support cancellation.

### Get Cutoff Pickup Time

```
GET /pickups/v1/cutoff-time
Authorization: Bearer {token}
Content-Type: application/json
```

Returns the latest hour for same-day pickup creation at a given postal code.

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `postalCode` | string | Yes | Postal code of pickup location |
| `countryCode` | string | Yes | Country code (e.g., `PL`) |

## Scheduling Rules

### Same-Day Pickups

Same-day pickup is possible if:

1. Request is submitted before the cutoff time (retrieve via `/pickups/v1/cutoff-time`)
2. `pickup_from` must be at or before the cutoff time
3. `pickup_to` must be at least 120 minutes later than `pickup_from`
4. `pickup_to` must be at least 120 minutes later than current time
5. Pickup window must fall within the same day, typically 09:00–18:00 local time

### Advance Scheduling

Pickups can be scheduled up to **7 days** in advance.

### Deduplication Rules

- Multiple pickups from the same address and time are **not allowed**
- Exception: In commercial centers, provide a distinct `location_description` (e.g., "Building A – Dock 3")

## Data Structures

### PickupAddress

| Field | Type | Required | Description |
|---|---|---|---|
| `countryCode` | string | Yes | ISO 2-letter country code |
| `street` | string | Yes | Street name |
| `houseNumber` | string | Yes | Building number |
| `flatNumber` | string | No | Flat/apartment number |
| `city` | string | Yes | City name |
| `postalCode` | string | Yes | Postal code |

### PickupContactInfo

| Field | Type | Required | Description |
|---|---|---|---|
| `firstName` | string | Yes | First name |
| `lastName` | string | Yes | Last name |
| `phone` | PickupPhoneNumber | Yes | Phone with prefix and number |
| `email` | string | Yes | Email address |

### PickupPhoneNumber

| Field | Type | Description |
|---|---|---|
| `prefix` | string | Country prefix (e.g., "+48") |
| `number` | string | Phone number (digits only) |

### PickupVolume

| Field | Type | Required | Description |
|---|---|---|---|
| `itemType` | string | Yes | Always `"PARCEL"` |
| `count` | int | Yes | Number of parcels |
| `totalVolume` | TotalVolume | Yes | Total volume |

### PickupTotalVolume

| Field | Type | Description |
|---|---|---|
| `amount` | number | Volume amount |
| `unit` | string | Unit — `L` (liters) |

### PickupCustomReferences

```json
{
    "custom": {
        "content": "any reference string"
    }
}
```

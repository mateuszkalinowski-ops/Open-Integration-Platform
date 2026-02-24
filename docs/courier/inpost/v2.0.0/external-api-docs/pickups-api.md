# InPost International API 2024 — Pickups API

> Source: https://developers.inpost-group.com/pickups

## Overview

The Pickups API manages one-time courier pickup orders. Merchants with an active logistics contract can schedule courier collection for a specific day and time window.

**Availability**: Ordering via API is currently supported only in Poland.

## Endpoints

### Create Pickup Order

```
POST /one-time-pickups
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
        "from": "2024-06-15T09:00:00+02:00",
        "to": "2024-06-15T12:00:00+02:00"
    },
    "references": {
        "custom": {
            "content": "Order batch #12345"
        }
    },
    "volume": {
        "itemType": "PARCEL",
        "count": 5,
        "totalWeight": {
            "amount": 12.5,
            "unit": "KG"
        }
    }
}
```

#### Response

Returns the created pickup order object with assigned ID.

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
GET /one-time-pickups/{orderId}
Authorization: Bearer {token}
Content-Type: application/json
```

### Get Cutoff Pickup Time

```
GET /cutoff-time
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

1. Request is submitted before the cutoff time (retrieve via `/cutoff-time`)
2. `pickup_from` must be at or before the cutoff time
3. `pickup_to` must be at least 120 minutes later than `pickup_from`
4. `pickup_to` must be at least 120 minutes later than current time
5. Pickup window must fall within the same day, typically 09:00–18:00 local time

### Advance Scheduling

Pickups can be scheduled up to **7 days** in advance.

### Deduplication Rules

- Multiple pickups from the same address and time are **not allowed**
- Exception: In commercial centers, multiple pickups may be scheduled from the same address if a distinct `location_description` is provided (e.g., "Building A – Dock 3")

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
| `phone` | PhoneNumber | Yes | Phone with prefix and number |
| `email` | string | Yes | Email address |

### PickupVolume

| Field | Type | Required | Description |
|---|---|---|---|
| `itemType` | string | Yes | Always `"PARCEL"` |
| `count` | int | Yes | Number of parcels |
| `totalWeight` | TotalWeight | Yes | Combined weight |

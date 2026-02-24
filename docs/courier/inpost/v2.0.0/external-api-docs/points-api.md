# InPost International API 2024 — Points API

> Source: https://developers.inpost-group.com/ (Points & Location section)

## Overview

The Points API provides access to InPost pickup and drop-off locations across all supported markets. It returns both APM lockers and PUDO points in a unified response.

**Required scope**: `api:points:read`

## Endpoints

### Search Points

```
GET /points
Authorization: Bearer {token}
Accept-Language: pl-PL
Content-Type: application/json
```

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page` | string | No | Page number |
| `perPage` | string | No | Results per page |
| `limit` | string | No | Maximum results |
| `address.country` | string | No | Filter by country code (ISO2) |
| `address.administrativeArea` | string | No | Filter by administrative region |
| `address.city` | string | No | Filter by city |
| `address.postalCode` | string | No | Filter by postal code |
| `capabilities` | string | No | Filter by point capabilities |
| `type` | string | No | Filter by point type |

#### Response (`GetPointsResponse`)

```json
{
    "items": [
        {
            "id": "PL_KRA010",
            "type": "APM",
            "address": {
                "street": "Krakowska",
                "buildingNumber": "10",
                "city": "Kraków",
                "postalCode": "30-001",
                "country": "PL",
                "administrativeArea": "małopolskie"
            },
            "coordinates": {
                "longitude": 19.945,
                "latitude": 50.065
            },
            "imageUrl": "https://...",
            "operatingHours": {
                "monday": "00:00-24:00",
                "tuesday": "00:00-24:00",
                "wednesday": "00:00-24:00",
                "thursday": "00:00-24:00",
                "friday": "00:00-24:00",
                "saturday": "00:00-24:00",
                "sunday": "00:00-24:00"
            },
            "distance": 1250
        }
    ]
}
```

### Get Point by ID

```
GET /points/{id}
Authorization: Bearer {token}
Accept-Language: pl-PL
Content-Type: application/json
```

Returns a single `PointDto` object with full details.

### Search Points by Location (Proximity)

```
GET /points/search-by-location
Authorization: Bearer {token}
Accept-Language: pl-PL
Content-Type: application/json
```

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page` | string | No | Page number |
| `perPage` | string | No | Results per page |
| `relativePoint` | string | No | Coordinates for proximity search (lat,lng) |
| `relativePostCode` | string | No | Postal code for proximity search |
| `maxDistance` | string | No | Maximum distance in meters |
| `address.country` | string | No | Filter by country code |
| `limit` | string | No | Maximum results |
| `capabilities` | string | No | Filter by capabilities |
| `type` | string | No | Filter by point type |

## Point Types

| Type | Description |
|---|---|
| `APM` | Automated Parcel Machine (Paczkomat) |
| `PUDO` | Pick-Up Drop-Off Point (retail store, kiosk, service point) |
| `HUB` | InPost warehouse / sorting center |

## Point Object Structure (PointDto)

| Field | Type | Description |
|---|---|---|
| `id` | string | Point identifier (e.g., `PL_KRA010`) |
| `type` | string | Point type: APM, PUDO, HUB |
| `address` | Address | Physical address |
| `coordinates` | Coordinates | GPS location (longitude, latitude) |
| `imageUrl` | string | URL to point image |
| `operatingHours` | OperatingHours | Opening hours per day |
| `distance` | number | Distance from search origin (meters) |

### Address Object

| Field | Type | Description |
|---|---|---|
| `street` | string | Street name |
| `buildingNumber` | string | Building number |
| `city` | string | City name |
| `postalCode` | string | Postal code |
| `country` | string | ISO2 country code |
| `administrativeArea` | string | Region/province |

## Connector Normalization

The connector normalizes InPost point data to a unified schema:

```json
{
    "type": "APM",
    "name": "PL_KRA010",
    "address": {
        "line1": "Krakowska 10",
        "line2": "",
        "state_code": "małopolskie",
        "postal_code": "30-001",
        "country_code": "PL",
        "city": "Kraków",
        "longitude": "19.945",
        "latitude": "50.065"
    },
    "image_url": "https://...",
    "open_hours": { ... },
    "option_cod": false,
    "option_send": true,
    "option_deliver": false,
    "additional_info": "",
    "distance": 1250,
    "foreign_address_id": ""
}
```

## Supported Markets

APM and PUDO deliveries are available for shipments from Poland to:
Belgium, Spain, France, Italy, Luxembourg, Netherlands, Portugal.

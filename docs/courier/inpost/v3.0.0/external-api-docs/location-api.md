# InPost International API 2025 (Global API) — Location API v1

> Source: https://developers.inpost-group.com/ (Points & Locker List section)

## Overview

The Location API v1 replaces the Points API from the 2024 version. It provides a unified endpoint for accessing InPost pickup and drop-off locations across all supported markets — both APM lockers and PUDO points are returned in a single response.

**Base path**: `/location/v1`  
**Required scope**: `api:points:read`

## Endpoints

### Search Points

```
GET /location/v1/points
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

#### Headers

| Header | Default | Description |
|---|---|---|
| `Accept-Language` | `pl-PL` | Response language preference |

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
GET /location/v1/points/{id}
Authorization: Bearer {token}
Accept-Language: pl-PL
Content-Type: application/json
```

Returns a single `PointDto` with full details.

### Search Points by Location (Proximity)

```
GET /location/v1/points/search-by-location
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

## Point Object (PointDto)

| Field | Type | Description |
|---|---|---|
| `id` | string | Point identifier (e.g., `PL_KRA010`) |
| `type` | string | Point type: APM, PUDO, HUB |
| `address` | Address | Physical address |
| `coordinates` | Coordinates | GPS location |
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

## Differences from 2024 Points API

| Feature | 2024 (Points API) | 2025 (Location API v1) |
|---|---|---|
| Base path | `/points` | `/location/v1/points` |
| Search endpoint | `/points/search-by-location` | `/location/v1/points/search-by-location` |
| Unified cross-market | Per request | Single request returns all markets |

## Supported Markets

APM and PUDO deliveries available for shipments from Poland to:
Belgium, Spain, France, Italy, Luxembourg, Netherlands, Portugal.

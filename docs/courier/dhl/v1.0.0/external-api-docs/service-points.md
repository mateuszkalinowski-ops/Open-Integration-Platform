# DHL24 WebAPI v2 — Service Points (Pickup Points)

> Sources:
> - DHL24 WebAPI: https://dhl24.com.pl/en/webapi2/doc.html
> - Parcelshop WebAPI: https://dhl24.com.pl/en/servicepoint/doc.html
> Fetched: 2026-02-24

---

## Overview

There are two APIs for finding DHL service/pickup points:

1. **DHL24 WebAPI** `getNearestServicepoints` — standard service point lookup
2. **Parcelshop Manager WebAPI** `getNearestServicepoints` / `getNearestServicepointsCOD` —
   parcelshop-specific lookup with COD filtering

## DHL24 WebAPI — getNearestServicepoints

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `country` | string(2) | Yes | Country code (e.g. `PL`) |
| `postcode` | string | Yes | Postal code (without dash) |
| `city` | string | No | City name |
| `radius` | int | No | Search radius in meters (default 500) |

### Output — PointStructure

Each point in the response array:

| Field | Type | Description |
|-------|------|-------------|
| `sap` | string | SAP number — unique service point identifier |
| `name` | string | Point name |
| `type` | string | Point type (e.g. PARCEL_LOCKER, SERVICE_POINT) |
| `address.street` | string | Street |
| `address.houseNumber` | string | House number |
| `address.postcode` | string | Postal code |
| `address.city` | string | City |
| `address.country` | string | Country code |
| `longitude` | float | GPS longitude |
| `latitude` | float | GPS latitude |
| `description` | string | Additional info / opening hours |

---

## Parcelshop WebAPI — getNearestServicepoints

### Input — GetNearestServicepointsStructure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `postcode` | string | Yes | Postal code (without dash) |
| `city` | string | No | City |
| `radius` | int | No | Radius in meters (default 500) |

### Output

Same PointStructure format as DHL24 API but without `type` and `country` fields.
Points include `address.city` instead.

---

## Parcelshop WebAPI — getNearestServicepointsCOD

Same input as `getNearestServicepoints` but returns only service points
that accept Cash on Delivery (COD) payments.

---

## Parcelshop WebAPI — getNearestServicepointsAll

Returns all service points without radius filtering.

---

## Normalized Point Schema (Connector Output)

The connector normalizes service point data to a unified format:

```json
{
  "type": "",
  "name": "DHL ServicePoint Name",
  "address": {
    "line1": "Street",
    "line2": "House Number",
    "state_code": "",
    "postal_code": "00-001",
    "country_code": "PL",
    "city": "Warszawa",
    "longitude": 21.0122,
    "latitude": 52.2297
  },
  "image_url": "",
  "open_hours": "",
  "option_cod": false,
  "option_send": true,
  "option_deliver": false,
  "additional_info": "Description from API",
  "distance": 0,
  "foreign_address_id": "SAP_NUMBER"
}
```

The `foreign_address_id` contains the DHL SAP number, which is used as
`servicePointAccountNumber` when creating parcelshop shipments.

---

## getPostalCodeServices

Checks available DHL services for a given postal code.

### Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `postcode` | string | Yes | Postal code |

### Output

List of available service types for the given postal code (e.g. AH, 09, 12, SP).

# DHL24 WebAPI v2 — Full API Reference

> Source: https://dhl24.com.pl/en/webapi2/doc.html
> WSDL Production: https://dhl24.com.pl/webapi2 (v4.20.58)
> WSDL Sandbox: https://sandbox.dhl24.com.pl/webapi2
> Fetched: 2026-02-24

## Overview

DHL24 WebAPI v2 is a **SOAP-based** web service enabling integration of DHL24
shipping features into external software. The service is described via WSDL.

The connector uses two separate SOAP APIs:
1. **DHL24 WebAPI v2** — standard courier shipments (domestic, international)
2. **Parcelshop Manager WebAPI** — service point (parcelshop) shipments

## Authentication

Every SOAP call requires an `AuthData` structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Login credential |
| `password` | string | Yes | Password credential |

Credentials are obtained from the DHL24 portal. Sandbox and production use
separate credential sets.

## Environments

| Environment | DHL24 WebAPI WSDL | Parcelshop WebAPI WSDL |
|-------------|-------------------|----------------------|
| Production | `https://dhl24.com.pl/webapi2` | `https://dhl24.com.pl/servicepoint` |
| Sandbox | `https://sandbox.dhl24.com.pl/webapi2` | `https://sandbox.dhl24.com.pl/servicepoint` |

---

## DHL24 WebAPI v2 — Methods

### createShipments

Creates 1–3 shipments in a single call. Can optionally book a courier pickup.

**Input:** `AuthData` + array of `ShipmentFullData`
**Output:** Array of `ShipmentBasicData` (waybill number, label data)

### createShipment (grouping method)

Creates a shipment and optionally books a courier in one request.

**Input:** `AuthData` + `ShipmentData` (see detailed docs in `createShipment.md`)
**Output:** `ShipmentResponse` with label and dispatch info

### bookCourier

Books courier pickup for already created shipments.

**Input:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `pickupDate` | date | Yes | Pickup date (YYYY-MM-DD) |
| `pickupTimeFrom` | string | Yes | Start time (HH:MM) |
| `pickupTimeTo` | string | Yes | End time (HH:MM) |
| `additionalInfo` | string | No | Additional info for courier |
| `shipmentIdList` | array | Yes | List of shipment IDs |
| `courierWithLabel` | bool | No | Courier brings labels |

**Output:** Array of dispatch notification numbers

### deleteShipments

Deletes/cancels shipments by waybill number.

**Input:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `shipment` | object | Yes | `shipmentIdentificationNumber` + `dispatchIdentificationNumber` |

**Output:** `{ result: bool, error: string? }`

### getLabels

Retrieves shipping labels.

**Input:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `itemsToPrint` | array | Yes | Array of `{ shipmentId, labelType }` |

**Label types:**

| Value | Description |
|-------|-------------|
| `LP` | Consignment note |
| `BLP` | BLP label (PDF) |
| `LBLP` | LBLP label (PDF A4) |
| `ZBLP` | BLP label for Zebra printers (ZPL) |
| `ZBLP300` | BLP 300dpi for Zebra printers |

**Output:** Array of `{ shipmentId, labelType, labelMimeType, labelData (base64) }`

### getTrackAndTraceInfo

Downloads delivery process history and current status.

**Input:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `shipmentId` | string | Yes | Shipment ID (waybill number) |

**Output:**

| Field | Type | Description |
|-------|------|-------------|
| `shipmentId` | string | Shipment ID |
| `receivedBy` | string | Person who collected the parcel |
| `events` | array | Array of `ShipmentEvent` objects |

**ShipmentEvent:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Event status description |
| `terminal` | string | Terminal/location name |
| `timestamp` | datetime | Event date and time |

### getNearestServicepoints

Finds nearby DHL service/pickup points.

**Input:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `country` | string(2) | Yes | Country code (e.g. PL) |
| `postcode` | string | Yes | Postal code (without dash) |
| `city` | string | No | City name |
| `radius` | int | No | Search radius in meters (default 500) |

**Output:** Array of service point objects with name, address, coordinates,
opening hours, and capabilities.

### getPostalCodeServices

Checks available DHL services for a given postal code.

**Input:** `AuthData` + postal code
**Output:** List of available service types

### getMyShipments / getMyShipmentsCount

Retrieves list of created shipments with filtering (date range, pagination).

**Input:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `createdFrom` | date | Yes | Start date |
| `createdTo` | date | Yes | End date |
| `offset` | int | No | Pagination offset (100 per page) |

**Output:** Array of shipment objects with details

### cancelCourierBooking

Cancels a previously booked courier pickup.

### getReturnParams

Gets parameters for creating return shipments.

### getVersion

Returns the current WebAPI version string.

---

## Error Handling

SOAP errors are returned as `Fault` objects. Common error codes:

| Code | Description |
|------|-------------|
| `100` | Authentication error (invalid credentials) |
| Other | Application-specific errors with descriptive messages |

HTTP-level errors (connection, timeout) are raised as `TransportError`.

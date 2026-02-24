# DHL Parcelshop Manager WebAPI — Reference

> Source: https://dhl24.com.pl/en/servicepoint/doc.html
> WSDL Production: https://dhl24.com.pl/servicepoint
> WSDL Sandbox: https://sandbox.dhl24.com.pl/servicepoint
> Fetched: 2026-02-24

## Overview

The Parcelshop Manager WebAPI is a separate SOAP service for managing DHL ServicePoint
(parcelshop) shipments. It uses different structures than the standard DHL24 WebAPI.

## Authentication

Same `AuthData` structure as DHL24 WebAPI:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Login |
| `password` | string | Yes | Password |

## Data Structures

### AddressStructure

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Name |
| `postcode` | string | Postal code (without dash) |
| `city` | string | City |
| `street` | string | Street |
| `houseNumber` | string | House number |

### ContactStructure

| Field | Type | Description |
|-------|------|-------------|
| `personName` | string | Contact person |
| `phoneNumber` | string | Phone number |
| `emailAddress` | string | Email |

### PreavisoStructure

Same as ContactStructure — used for pre-delivery notifications.

### FullAddressDataStructure

Combines `address` (AddressStructure) + `contact` (ContactStructure)
+ `preaviso` (PreavisoStructure).

### ShipStructure

| Field | Type | Description |
|-------|------|-------------|
| `shipper` | FullAddressDataStructure | Sender data |
| `receiver` | FullAddressDataStructure | Recipient data |
| `servicePointAccountNumber` | string | Target service point SAP number |

### BillingStructure

| Field | Type | Description |
|-------|------|-------------|
| `paymentType` | string | Payment method |
| `shippingPaymentType` | string | `SHIPPER`, `RECEIVER`, `USER` |
| `billingAccountNumber` | string | Account number |
| `costsCenter` | string | Cost center |

### PieceStructure

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `ENVELOPE`, `PACKAGE`, `PALLET` |
| `width` | int | Width (cm) |
| `height` | int | Height (cm) |
| `lenght` | int | Length (cm) — note: typo in API |
| `weight` | float | Weight (kg) |
| `quantity` | int | Quantity |

### ServiceStructure (special services)

| Field | Type | Description |
|-------|------|-------------|
| `serviceType` | string | Service code (e.g. `UBEZP`, `COD`) |
| `serviceValue` | string | Value for insurance/COD |
| `collectOnDeliveryForm` | string | COD refund form |

### ShipmentInfoStructure

| Field | Type | Description |
|-------|------|-------------|
| `dropOffType` | string | `REGULAR_PICKUP`, `REQUEST_COURIER` |
| `serviceType` | string | Service type code |
| `billing` | BillingStructure | Billing info |
| `shipmentDate` | string | Date YYYY-MM-DD |
| `shipmentStartHour` | string | Start time HH:MM |
| `shipmentEndHour` | string | End time HH:MM |
| `labelType` | string | Label type |
| `specialServices` | array | Array of ServiceStructure items |

## Methods

### createShipment

Creates a parcelshop shipment.

**Input:** `CreateShipmentStructure` containing:
- `authData` — Authorization
- `shipmentData` with `ship`, `shipmentInfo`, `pieceList`, `content`

**Output:** `CreateShipmentResponseStructure`:

| Field | Type | Description |
|-------|------|-------------|
| `shipmentNumber` | string | Waybill number |
| `label` | base64 | Label data |
| `labelMimeType` | string | Label MIME type |

### deleteShipment

Deletes a parcelshop shipment.

**Input:** `DeleteShipmentStructure` with `authData` + `shipmentNumber`
**Output:** `DeleteShipmentResponseStructure` with result status

### getLabel

Retrieves label for a parcelshop shipment.

**Input:** `GetLabelStructure` with `authData` + `shipmentNumber` + `labelType`
**Output:** `LabelStructure` with label data in base64

### getNearestServicepoints

Finds nearby DHL service points.

**Input:** `GetNearestServicepointsStructure`:

| Field | Type | Description |
|-------|------|-------------|
| `authData` | AuthData | Authorization |
| `postcode` | string | Postal code (no dash) |
| `city` | string | City (optional) |
| `radius` | int | Search radius in meters |

**Output:** `GetNearestServicepointsResponseStructure` with array of `PointStructure`:

| Field | Type | Description |
|-------|------|-------------|
| `sap` | string | SAP number (unique point ID) |
| `name` | string | Point name |
| `type` | string | Point type |
| `address` | object | `{ street, houseNumber, postcode, city, country }` |
| `longitude` | float | GPS longitude |
| `latitude` | float | GPS latitude |
| `description` | string | Additional description |

### getNearestServicepointsCOD

Same as `getNearestServicepoints` but returns only points accepting COD payments.

### getNearestServicepointsAll

Returns all service points (no radius filter).

### getPnp

Gets PNP (Pickup & Pack) data.

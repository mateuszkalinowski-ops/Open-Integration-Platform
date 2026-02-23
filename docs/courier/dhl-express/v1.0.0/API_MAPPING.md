# API Mapping — DHL Express v1.0.0

## Pinquark WMS ↔ DHL Express Field Mapping

### Shipment Party (Shipper / Receiver)

| Pinquark WMS Field | DHL Express Field | Notes |
|--------------------|-------------------|-------|
| `first_name` + `last_name` | `contact.fullName` | Concatenated |
| `company_name` | `contact.companyName` | |
| `phone` | `contact.phone` | |
| `email` | `contact.email` | |
| `street` | `address.streetLine1` | Max 45 chars |
| `building_number` | `address.streetLine2` | |
| `postal_code` | `address.postalCode` | |
| `city` | `address.city` | |
| `country_code` | `address.countryCode` | ISO 3166-1 alpha-2 |

### Parcel / Package

| Pinquark WMS Field | DHL Express Field | Notes |
|--------------------|-------------------|-------|
| `weight` | `packages[].weight` | kg (metric) |
| `length` | `packages[].dimensions.length` | cm (metric) |
| `width` | `packages[].dimensions.width` | cm (metric) |
| `height` | `packages[].dimensions.height` | cm (metric) |
| `description` | `content.description` | |

### Shipment

| Pinquark WMS Field | DHL Express Field | Notes |
|--------------------|-------------------|-------|
| `shipment_date` | `plannedShippingDateAndTime` | ISO 8601 with timezone |
| `service_name` | `productCode` | P, U, N, etc. |
| `content` | `content.description` | |
| `cod_value` | Via valueAddedServices | Service code: `COD` |
| `insurance_value` | Via valueAddedServices | Service code: `II` |
| `tracking_number` | Response: `shipmentTrackingNumber` | |
| `waybill_number` | Response: `shipmentTrackingNumber` | Same as tracking |

### Product Codes

| Code | Description |
|------|-------------|
| `P` | DHL Express Worldwide |
| `U` | DHL Express Worldwide (EU) |
| `N` | DHL Express Domestic |
| `D` | DHL Express Worldwide Doc |
| `T` | DHL Express 12:00 |
| `K` | DHL Express 9:00 |
| `E` | DHL Express Envelope |

### Status Mapping

| DHL Express Status | Pinquark WMS Status |
|--------------------|---------------------|
| `transit` | `IN_TRANSIT` |
| `delivered` | `DELIVERED` |
| `failure` | `DELIVERY_FAILED` |
| `customs` | `CUSTOMS_PROCESSING` |
| `pre-transit` | `REGISTERED` |

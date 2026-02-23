# Raben Group — API Field Mapping v1.0.0

## Shipment Creation

### Sender / Receiver

| Platform Field | Raben API Field | Type | Required |
|---|---|---|---|
| `company_name` | `companyName` | string | Yes |
| `contact_person` | `contactPerson` | string | Yes |
| `phone` | `phone` | string | Yes |
| `email` | `email` | string | No |
| `street` | `street` | string | Yes |
| `building_number` | `buildingNumber` | string | No |
| `apartment_number` | `apartmentNumber` | string | No |
| `city` | `city` | string | Yes |
| `postal_code` | `postalCode` | string | Yes |
| `country_code` | `countryCode` | string (ISO 3166-1 alpha-2) | Yes (default: PL) |

### Packages

| Platform Field | Raben API Field | Type | Required |
|---|---|---|---|
| `package_type` | `packageType` | enum: pallet, half_pallet, package, other | No (default: pallet) |
| `quantity` | `quantity` | integer | No (default: 1) |
| `weight` | `weight` | float (kg) | Yes |
| `dimensions.length` | `dimensions.length` | float (cm) | No |
| `dimensions.width` | `dimensions.width` | float (cm) | No |
| `dimensions.height` | `dimensions.height` | float (cm) | No |
| `is_stackable` | `isStackable` | boolean | No (default: true) |
| `ldm` | `ldm` | float (loading meters) | No |

### Service Types

| Platform Value | Raben Service | Description |
|---|---|---|
| `cargo_classic` | Cargo Classic | Standard 24/48h delivery |
| `cargo_premium` | Cargo Premium | Priority same/next day |
| `cargo_premium_08` | Cargo Premium 08:00 | Delivery by 08:00 |
| `cargo_premium_10` | Cargo Premium 10:00 | Delivery by 10:00 |
| `cargo_premium_12` | Cargo Premium 12:00 | Delivery by 12:00 |
| `cargo_premium_16` | Cargo Premium 16:00 | Delivery by 16:00 |

### Additional Services

| Platform Field | Raben API Field | Description |
|---|---|---|
| `pcd_enabled` | `pcdEnabled` | Photo Confirming Delivery |
| `email_notification` | `emailNotification` | Email notification to receiver |
| `tail_lift_pickup` | `tailLiftPickup` | Tail lift at pickup |
| `tail_lift_delivery` | `tailLiftDelivery` | Tail lift at delivery |

## Status Mapping

| Raben Status | Platform Status | Description |
|---|---|---|
| `new` | `created` | Order registered |
| `registered` | `created` | Order registered in system |
| `accepted` | `created` | Order accepted for processing |
| `picked_up` | `picked_up` | Shipment collected from sender |
| `collected` | `picked_up` | Shipment collected |
| `in_transit` | `in_transit` | Shipment in transit |
| `hub_scan` | `in_transit` | Scanned at transit hub |
| `at_terminal` | `at_terminal` | At Raben terminal |
| `cross_dock` | `at_terminal` | Cross-docking at terminal |
| `out_for_delivery` | `out_for_delivery` | On delivery vehicle |
| `on_vehicle` | `out_for_delivery` | Loaded on vehicle |
| `delivered` | `delivered` | Successfully delivered |
| `pcd_confirmed` | `delivered` | Delivered with PCD |
| `cancelled` | `cancelled` | Order cancelled |
| `exception` | `exception` | Delivery exception |
| `damage` | `exception` | Damage reported |
| `returned` | `returned` | Shipment returned |

## Claim Types

| Platform Value | Description |
|---|---|
| `damage` | Package/freight damaged during transport |
| `loss` | Package/freight lost |
| `delay` | Delivery delayed beyond SLA |
| `other` | Other complaint type |

## Authentication

| Parameter | Description |
|---|---|
| `username` | myRaben login credentials |
| `password` | myRaben password |
| Token type | JWT (Bearer token) |
| Token endpoint | `POST /auth/login` |
| Token refresh | Automatic on 401 response |

# InPost International API 2024 — Shipping API

> Source: https://developers.inpost-group.com/shipping

## Overview

The Shipping API allows creating shipments across all supported InPost delivery types, retrieving labels, and querying shipment details. In the 2024 API, shipments are created via type-specific endpoints and identified by UUID.

## Endpoints

### Create Shipment

```
POST /shipments/{shipmentType}
Authorization: Bearer {token}
Content-Type: application/json
```

The `{shipmentType}` path segment determines the delivery combination. The specific path values are determined by the `ShipmentTypeEnum` in the connector:

- Point-to-Point (locker → locker)
- Address-to-Point (address → locker)
- Point-to-Address (locker → address)
- Address-to-Address (address → address)

#### Request Body (`CreateShipmentDTO`)

```json
{
    "labelFormat": "PDF_URL",
    "shipment": {
        "sender": {
            "companyName": "Sender Corp",
            "firstName": "Jan",
            "lastName": "Kowalski",
            "email": "jan@example.com",
            "phone": {
                "prefix": "+48",
                "number": "123456789"
            }
        },
        "recipient": {
            "companyName": null,
            "firstName": "Anna",
            "lastName": "Nowak",
            "email": "anna@example.com",
            "phone": {
                "prefix": "+48",
                "number": "987654321"
            }
        },
        "origin": {
            "address": {
                "street": "Testowa",
                "houseNumber": "1",
                "postalCode": "00-001",
                "city": "Warszawa",
                "countryCode": "PL"
            }
        },
        "destination": {
            "countryCode": "PL",
            "pointName": "KRA010"
        },
        "priority": "STANDARD",
        "valueAddedServices": {
            "insurance": {
                "value": "1000",
                "currency": "EUR"
            }
        },
        "references": {
            "custom": {
                "content": "Order #12345"
            }
        },
        "parcel": {
            "type": "STANDARD",
            "dimensions": {
                "length": "30",
                "width": "20",
                "height": "10",
                "unit": "CM"
            },
            "weight": {
                "amount": "2.5",
                "unit": "KG"
            }
        }
    }
}
```

#### Origin variants

**Address-based origin** (courier pickup):

```json
{
    "address": {
        "street": "Testowa",
        "houseNumber": "1",
        "postalCode": "00-001",
        "city": "Warszawa",
        "countryCode": "PL"
    }
}
```

**Point-based origin** (locker drop-off):

```json
{
    "countryCode": "PL",
    "shippingMethods": ["LOCKER"]
}
```

#### Destination variants

**Address-based destination**:

```json
{
    "address": {
        "street": "Odbiorcza",
        "houseNumber": "5",
        "postalCode": "30-001",
        "city": "Kraków",
        "countryCode": "PL"
    }
}
```

**Point-based destination** (locker/PUDO):

```json
{
    "countryCode": "PL",
    "pointName": "KRA010"
}
```

#### Response (`CreateShipmentResponseDto`)

```json
{
    "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "trackingNumber": "620000000001234567",
    "status": "CREATED",
    "label": {
        "url": "https://...",
        "content": "base64_encoded_pdf..."
    }
}
```

Key fields:
- `uuid`: Shipment unique identifier (used for label retrieval, status queries)
- `trackingNumber`: Public tracking number

### Get Shipment Label

```
GET /shipments/{uuid}/label
Authorization: Bearer {token}
Content-Type: application/json
```

Returns label in JSON format with base64-encoded content:

```json
{
    "label": {
        "content": "JVBERi0xLjQK..."
    }
}
```

Decode the `content` field from base64 to get the PDF bytes.

### Get Shipment Details

```
GET /shipments/{uuid}
Authorization: Bearer {token}
Content-Type: application/json
```

Returns full shipment object including current status, tracking number, sender/receiver details, and parcel information.

## Contact Info Structure

```json
{
    "companyName": "Company Ltd",
    "firstName": "Jan",
    "lastName": "Kowalski",
    "email": "jan@example.com",
    "phone": {
        "prefix": "+48",
        "number": "123456789"
    }
}
```

## Value-Added Services

| Service | Description |
|---|---|
| `insurance` | Additional insurance coverage with value and currency |

## Priority Values

| Value | Description |
|---|---|
| `STANDARD` | Standard delivery (default) |
| `EXPRESS` | Express delivery |

## Parcel Dimensions

- Length, width, height in CM (string values)
- Weight in KG (string value)
- Type: `STANDARD`

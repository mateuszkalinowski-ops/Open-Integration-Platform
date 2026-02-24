# InPost International API 2025 (Global API) — Tracking API v1

> Source: https://developers.inpost-group.com/tracking  
> Event catalog: https://developers.inpost-group.com/tracking-events

## Overview

The Tracking API v1 provides parcel tracking events. In the 2025 Global API, tracking **does not require authentication** — it is a public endpoint.

**Base path**: `/tracking/v1`

## Endpoints

### Get Parcel Tracking Events

```
GET /tracking/v1/parcels
Content-Type: application/json
```

No `Authorization` header required.

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `trackingNumbers` | string[] | Yes | List of tracking numbers to query |

#### Optional Headers

| Header | Description |
|---|---|
| `x-inpost-event-version` | Request specific event version (e.g., `V1`, `V2`) |

#### Response

```json
{
    "parcels": [
        {
            "trackingNumber": "620000000001234567",
            "status": "LMD.1001",
            "events": [
                {
                    "customerReference": "Order-123",
                    "trackingNumber": "620000000001234567",
                    "eventId": "fb2ace20-2d8c-41da-94c4-3bd93f1451a1#CRE.1001",
                    "eventCode": "CRE.1001",
                    "timestamp": "2025-01-08T14:02:55.374675Z",
                    "location": {
                        "id": "PL_WAW01",
                        "type": "LOGISTIC_CENTER",
                        "name": "Warehouse Warsaw",
                        "address": "ul. Logistyczna 1",
                        "postalCode": "00-001",
                        "city": "Warszawa",
                        "country": "PL",
                        "description": null
                    },
                    "delivery": {
                        "recipientName": null,
                        "deliveryNotes": null
                    },
                    "shipment": {
                        "type": "OUTBOUND"
                    },
                    "returnToSender": null,
                    "newDestination": null
                }
            ]
        }
    ]
}
```

## Tracking URL

Public tracking URL for end customers:

```
https://inpost.pl/sledzenie-przesylek?number={tracking_number}
```

## Event Versioning

Events support versioning (V1, V2). V1 is supported indefinitely; subsequent versions are supported for up to 24 months from introduction. Changes:

- **V1**: Released 21 JAN 2025 — initial event set covering all major lifecycle stages
- **V2**: Released 11 NOV 2025 — additional market-specific events for PL and UK

## Complete Tracking Event Catalog

### Creation Events (CRE)

| Code | Title | Version | Market |
|---|---|---|---|
| CRE.1001 | Parcel Creation | V1 | All |
| CRE.1002 | Ready for acceptance | V1 | not in use |

### Customs Events (CC)

| Code | Title | Version | Market |
|---|---|---|---|
| CC.001 | Parcel at customs | V1 | All |
| CC.002 | Parcel customs cleared | V1 | All |
| CC.003 | Parcel held at customs | V1 | All |

### First-Mile Delivery (FMD)

| Code | Title | Version | Market |
|---|---|---|---|
| FMD.1001 | Ready for courier collection | V1 | All |
| FMD.1002 | Collected by courier | V1 | All |
| FMD.1003 | In-transit (first-mile) | V1 | All |
| FMD.1004 | Collected by courier in PUDO | V1 | All |
| FMD.1005 | Collected by courier in APM | V1 | All |
| FMD.1006 | In Transit from sender | V2 | UK |
| FMD.1007 | Parcel waiting collection at origin | V2 | UK |
| FMD.1008 | Parcel not picked up | V2 | UK |
| FMD.1009 | Not picked up - not available | V2 | UK |
| FMD.1010 | Not picked up - no ID | V2 | UK |
| FMD.1011 | Not picked up - store busy | V2 | UK |
| FMD.1012 | Not picked up - no label | V2 | UK |
| FMD.1013 | Parcel pick up scheduled | V2 | UK |
| FMD.1014 | Parcel pick up cancelled | V2 | UK |
| FMD.1015 | In transit from third party | V2 | UK |
| FMD.1016 | Not picked up - no access | V2 | UK |
| FMD.1017 | Not picked up - nothing to collect | V2 | UK |
| FMD.9001 | Parcel claimed | V1 | All |
| FMD.9002 | Parcel oversized | V1 | UK |

### Fulfilment Events (FUL)

| Code | Title | Version | Market |
|---|---|---|---|
| FUL.1001 | Picked | V1 | All |
| FUL.1002 | Packed | V1 | All |
| FUL.1003 | Dispatched | V1 | All |

### Handover Events (HAN)

| Code | Title | Version | Market |
|---|---|---|---|
| HAN.1001 | Handover | V1 | All |

### Mid-Mile Delivery (MMD)

| Code | Title | Version | Market |
|---|---|---|---|
| MMD.1001 | Adopted at Logistics Centre | V1 | All |
| MMD.1002 | Processed at Logistics Centre | V1 | All |
| MMD.1003 | Dispatched from Logistics Centre | V1 | All |
| MMD.1004 | Line-Haul | V1 | All |
| MMD.1005 | Parcel Sorted at Logistic Centre | V2 | PL |
| MMD.1006 | Held at depot - dangerous goods | V2 | UK |
| MMD.1007 | Dispatched from export depot | V2 | UK |
| MMD.1009 | Parcel Repacked | V2 | UK |
| MMD.3001 | Containerised at Logistics Centre | V1 | UK |
| MMD.9001 | Quarantine at Logistics Centre | V1 | UK |

### Last-Mile Delivery (LMD)

| Code | Title | Version | Market |
|---|---|---|---|
| LMD.1001 | In-transit (last-mile) | V1 | All |
| LMD.1002 | Arrived at destination | V1 | All |
| LMD.1003 | Ready to collect | V1 | All |
| LMD.1004 | Ready to collect PUDO | V1 | All |
| LMD.1005 | Ready to collect APM | V1 | All |
| LMD.1006 | Ready to collect at collection point | V1 | All |
| LMD.3001 | Alternative collection point assigned | V1 | All |
| LMD.3002 | Alternative temporary collection point | V1 | PL |
| LMD.3003 | Alternative collection point assigned | V1 | All |
| LMD.3004 | Branch collection assigned | V1 | All |
| LMD.3005 | Original collection point reassigned | V1 | All |
| LMD.3006 | Delivery readdressed | V1 | All |
| LMD.3007 | Stored temporary in service point | V1 | PL |
| LMD.3008 | Expired stored parcel | V1 | All |
| LMD.3009 | Expired on temporary box machine | V1 | PL |
| LMD.3010 | Expired on temporary box machine | V1 | PL |
| LMD.3011 | Expired on temporary collection point | V1 | PL |
| LMD.3012 | Redirect cancelled | V1 | All |
| LMD.3013 | Redirected to PUDO | V1 | All |
| LMD.3014 | Redirected to APM | V1 | All |
| LMD.3015 | Permanently Redirected to PUDO by InPost | V1 | UK |
| LMD.3016 | Permanently Redirected to APM by InPost | V1 | UK |
| LMD.3017 | Redirected to branch | V2 | UK |
| LMD.9001 | Reminder to collect | V1 | All |
| LMD.9002 | Expired | V1 | All |
| LMD.9003 | Oversized | V1 | All |
| LMD.9004 | Attempted delivery | V1 | PL |
| LMD.9005 | Undeliverable | V1 | All |
| LMD.9006 | Rejected by recipient | V1 | All |
| LMD.9007 | Incorrect delivery details | V1 | All |
| LMD.9008 | Receiver unknown | V1 | All |
| LMD.9009 | COD conditions not met | V1 | All |
| LMD.9010 | No mailbox | V1 | All |
| LMD.9011 | No access to location | V1 | All |
| LMD.9012 | Stored temporary in box machine | V1 | PL |
| LMD.9013 | Ready to collect at customer service point | V1 | All |
| LMD.9014 | Uncollected - Return to sender initiated | V1 | PL |
| LMD.9015 | Attempt - Incorrect Delivery Details | V1 | All |
| LMD.9016 | Attempt - No access location | V1 | All |
| LMD.9017 | Attempt - No answer | V1 | All |
| LMD.9018 | Delivery Attempt Failed | V1 | UK |
| LMD.9019 | Parcel not collected | V1 | UK |
| LMD.9020 | APM not available - access issue | V1 | UK |
| LMD.9021 | Not suitable compartment on APM | V1 | UK |
| LMD.9022 | APM Full | V1 | UK |
| LMD.9023 | APM not available - login access | V1 | UK |
| LMD.9024 | PUDO Closed | V1 | UK |
| LMD.9025 | Access Issue on Delivery | V1 | UK |
| LMD.9026 | Delivery point on strike | V2 | UK |
| LMD.9027 | Prohibited content | V2 | PL, UK |
| LMD.9028 | Force Majeure | V2 | PL |
| LMD.9029 | Attempt underage | V2 | UK |
| LMD.9030 | Damaged parcel | V2 | UK |

### End-of-Life Events (EOL)

| Code | Title | Version | Market |
|---|---|---|---|
| EOL.1001 | Delivered | V1 | All |
| EOL.1002 | Parcel collected | V1 | All |
| EOL.1003 | Delivered at Safe Place | V1 | All |
| EOL.1004 | Delivered at neighbour | V1 | All |
| EOL.1005 | Delivered with verified recipient | V1 | All |
| EOL.1006 | Delivered to alternative address | V2 | PL |
| EOL.1007 | Delivered to a third party | V2 | PL |
| EOL.1008 | Delivered into letterbox | V2 | UK |
| EOL.9001 | Missing | V1 | All |
| EOL.9002 | Damaged | V1 | All |
| EOL.9003 | Destroyed | V1 | All |
| EOL.9004 | Cancelled | V1 | All |
| EOL.9005 | Cancelled by customer | V2 | UK |
| EOL.9006 | Destroyed prohibited content | V2 | PL |

### Return Events (RTS)

| Code | Title | Version | Market |
|---|---|---|---|
| RTS.1001 | Returning to Sender | V1 | All |
| RTS.1002 | Returned to Sender | V1 | All |

### Information Events (INF)

| Code | Title | Version | Market |
|---|---|---|---|
| INF.1001 | COD payment received | V1 | All |
| INF.9001 | Delay in Delivery | V1 | All |
| INF.9003 | Delay - PUDO in holiday | V2 | PL |
| INF.9004 | Delay - Local holiday | V2 | PL |
| INF.9005 | Delay - Force Majeure | V2 | PL |
| INF.9009 | Delay - incorrect information | V2 | PL |
| INF.9010 | Customer delivery preferences applied | V2 | UK |
| INF.9012 | Scheduled afternoon delivery | V2 | UK |
| INF.9013 | Security inquiry | V2 | UK |
| INF.9014 | Delivery date set | V2 | UK |
| INF.9016 | Delay - rescheduled by sender | V2 | UK |
| INF.9017 | Delay - waiting booking | V2 | UK |

## Event Object Schema

| Field | Nullable | Type | Description |
|---|---|---|---|
| `customerReference` | Yes | String | Merchant reference from shipment creation |
| `trackingNumber` | No | String | InPost tracking number |
| `eventId` | No | String | Unique event ID (same as `x-inpost-event-id` header) |
| `eventCode` | No | String | Event code from catalog |
| `timestamp` | No | Datetime | ISO 8601 timestamp (local timezone) |
| `location` | Yes | Location | Event location |
| `delivery` | Yes | Delivery | Delivery info (for delivery events) |
| `shipment` | Yes | Shipment | Shipment type info |
| `returnToSender` | Yes | RTS | Return tracking data |
| `newDestination` | Yes | Location | Redirected destination |

### Location Object

| Field | Nullable | Type | Description |
|---|---|---|---|
| `id` | Yes | String | Location ID |
| `type` | No | String | LOCKER_POINT, LOGISTIC_CENTER, PUDO_POINT, ADDRESS, MPOK_POINT |
| `name` | Yes | String | Name/description |
| `address` | Yes | String | Street, door number |
| `postalCode` | Yes | String | Postal code |
| `city` | Yes | String | City name |
| `country` | Yes | String | Country code (ISO2) |
| `description` | Yes | String | Location description |

### Delivery Object

| Field | Nullable | Type | Description |
|---|---|---|---|
| `recipientName` | Yes | String | Name of person who received the parcel |
| `deliveryNotes` | Yes | String | Notes from courier |

### Shipment Object

| Field | Nullable | Type | Description |
|---|---|---|---|
| `type` | Yes | String | `OUTBOUND` or `RETURN` |

### RTS Object

| Field | Nullable | Type | Description |
|---|---|---|---|
| `trackingNumber` | Yes | String | Return parcel tracking number |

## Event Example

```json
{
    "customerReference": "XXXXXX",
    "trackingNumber": "XXXXXX",
    "eventId": "XYZ123",
    "eventCode": "ABC987",
    "timestamp": "2024-04-26T14:00:03.165Z",
    "location": {
        "id": "PL_ASDF",
        "type": "PUDO_POINT",
        "name": "ASDF",
        "address": "street name, door num, etc.",
        "postalCode": "999999-999",
        "city": "Tracking Town",
        "country": "PL",
        "description": "on the left side of Petrol Station XYZ"
    },
    "delivery": {
        "recipientName": "John Doe",
        "deliveryNotes": "Delivered in hand"
    },
    "shipment": {
        "type": "OUTBOUND"
    },
    "returnToSender": {
        "trackingNumber": "XXXXXXXX"
    },
    "newDestination": {
        "id": "PL_XYZ",
        "type": "LOCKER_POINT",
        "name": "XYZ",
        "address": "street building",
        "postalCode": "999999-999",
        "city": "Town",
        "country": "PL",
        "description": "behind the shop building"
    }
}
```

## Release Notes

- V2 | 11 NOV 2025 — additional PL and UK market-specific events
- V1 | 9 MAY 2025 — UK market events (oversized, quarantine, containerised)
- V1 | 7 MAY 2025 — UK redirect events
- V1 | 8 APR 2025 — collection point, delivery attempt, uncollected events
- V1 | 21 JAN 2025 — initial release, all markets

# InPost International API 2024 — Tracking API

> Source: https://developers.inpost-group.com/tracking  
> Event catalog: https://developers.inpost-group.com/tracking-events

## Overview

The Tracking API provides parcel tracking events. In the 2024 API version, tracking requires authentication via Bearer token.

## Endpoints

### Get Parcel Tracking Events

```
GET /track/parcels
Authorization: Bearer {token}
Content-Type: application/json
```

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
                    "eventCode": "CRE.1001",
                    "timestamp": "2024-04-26T14:00:03.165Z",
                    "location": {
                        "id": "PL_WAW01",
                        "type": "LOGISTIC_CENTER",
                        "name": "Warehouse Warsaw",
                        "city": "Warszawa",
                        "country": "PL"
                    }
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

Events support versioning (V1, V2). V1 is supported indefinitely; subsequent versions for up to 24 months from introduction.

## Tracking Event Categories

### Creation Events (CRE)

| Code | Title | Description |
|---|---|---|
| CRE.1001 | Parcel Creation | Parcel has been created |
| CRE.1002 | Ready for acceptance | Parcel is ready for acceptance in InPost network |

### Customs Events (CC)

| Code | Title | Description |
|---|---|---|
| CC.001 | Parcel at customs | Delivered to customs for clearance |
| CC.002 | Parcel customs cleared | Released by customs |
| CC.003 | Parcel held at customs | Held at customs for inspection |

### First-Mile Delivery (FMD)

| Code | Title | Description |
|---|---|---|
| FMD.1001 | Ready for courier collection | Parcel ready for courier pickup |
| FMD.1002 | Collected by courier | Courier has picked up the parcel |
| FMD.1003 | In-transit (first-mile) | Parcel moving through network |
| FMD.1004 | Collected by courier in PUDO | Collected from PUDO point |
| FMD.1005 | Collected by courier in APM | Collected from APM locker |
| FMD.9001 | Parcel claimed | Under claim process |

### Mid-Mile Delivery (MMD)

| Code | Title | Description |
|---|---|---|
| MMD.1001 | Adopted at Logistics Centre | Received at logistics centre |
| MMD.1002 | Processed at Logistics Centre | Processed at logistics centre |
| MMD.1003 | Dispatched from Logistics Centre | Dispatched from logistics centre |
| MMD.1004 | Line-Haul | In transit through network |

### Last-Mile Delivery (LMD)

| Code | Title | Description |
|---|---|---|
| LMD.1001 | In-transit (last-mile) | On the way to final destination |
| LMD.1002 | Arrived at destination | Arrived at final destination |
| LMD.1003 | Ready to collect | Ready for collection |
| LMD.1004 | Ready to collect PUDO | Ready at PUDO point |
| LMD.1005 | Ready to collect APM | Ready at APM locker |
| LMD.3001 | Alternative collection point | Redirected to alternative location |
| LMD.3006 | Delivery readdressed | Parcel readdressed to new location |
| LMD.9001 | Reminder to collect | Must be collected soon |
| LMD.9002 | Expired | Not collected on time |
| LMD.9003 | Oversized | Oversized for destination |
| LMD.9004 | Attempted delivery | Delivery attempted, will reattempt |
| LMD.9005 | Undeliverable | Could not be delivered |
| LMD.9006 | Rejected by recipient | Recipient rejected the parcel |
| LMD.9007 | Incorrect delivery details | Wrong delivery data |

### End-of-Life Events (EOL)

| Code | Title | Description |
|---|---|---|
| EOL.1001 | Delivered | Parcel delivered |
| EOL.1002 | Parcel collected | Collected at collection point |
| EOL.1003 | Delivered at Safe Place | Delivered to safe place |
| EOL.1004 | Delivered at neighbour | Delivered to neighbour |
| EOL.1005 | Delivered with verified recipient | Delivered with ID check |
| EOL.9001 | Missing | Marked as missing |
| EOL.9002 | Damaged | Marked as damaged |
| EOL.9003 | Destroyed | Marked as destroyed |
| EOL.9004 | Cancelled | Marked as cancelled |

### Return Events (RTS)

| Code | Title | Description |
|---|---|---|
| RTS.1001 | Returning to Sender | Journey back to sender started |
| RTS.1002 | Returned to Sender | Received by sender |

### Information Events (INF)

| Code | Title | Description |
|---|---|---|
| INF.1001 | COD payment received | Cash-on-delivery payment received |
| INF.9001 | Delay in Delivery | Service delay notification |

## Event Object Schema

| Field | Nullable | Type | Description |
|---|---|---|---|
| `customerReference` | Yes | String | Merchant reference |
| `trackingNumber` | No | String | InPost tracking number |
| `eventId` | No | String | Unique event ID |
| `eventCode` | No | String | Event code from catalog |
| `timestamp` | No | Datetime | ISO 8601 timestamp |
| `location` | Yes | Location | Event location |
| `delivery` | Yes | Delivery | Delivery info |
| `shipment` | Yes | Shipment | Shipment info |
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

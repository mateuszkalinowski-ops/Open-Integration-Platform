# InPost International API 2025 (Global API) — Reference

> Source: https://developers.inpost-group.com/  
> Used by connector: `integrators/courier/inpost/v3.0.0/`

## Overview

The InPost International 2025 API is the **Global API** — a unified REST API consolidating all InPost services under versioned routes. It replaces legacy per-market APIs (ShipX PL, PL API Gateway, API TRUCKER, etc.) with a single entry point.

Key improvements over the 2024 API:
- **Versioned routes**: `/shipping/v2`, `/tracking/v1`, `/pickups/v1`, `/location/v1`, `/returns/v1`
- **Organization-scoped**: All routes include `organizations/{orgId}` for tenant isolation
- **Synchronous shipment creation**: Tracking numbers returned immediately in creation response
- **Returns API**: Dedicated API for return shipments
- **Multi-parcel support**: Create shipments with multiple parcels in a single request
- **Tracking without auth**: Tracking API does not require authentication header

## Base URLs

| Environment | URL |
|---|---|
| **Production** | `https://api.inpost-group.com` |
| **Stage** | `https://stage-api.inpost-group.com` |

Note: Sandbox URL changed from `sandbox-api` (2024) to `stage-api` (2025).

## Authentication

OAuth 2.1 Client Credentials flow. Token endpoint: `POST /oauth2/token` (changed from `/auth/token` in 2024).

See [authentication.md](authentication.md) for details.

## API Modules Used by Connector

### 1. Shipping API (v2)

Create shipments, retrieve labels and shipment details.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/shipping/v2/organizations/{orgId}/shipments` | Create a shipment |
| `GET` | `/shipping/v2/organizations/{orgId}/shipments/{trackingNumber}/label` | Get label |
| `GET` | `/shipping/v2/organizations/{orgId}/shipments/{trackingNumber}` | Get shipment details |

See [shipping-api.md](shipping-api.md) for full details.

### 2. Tracking API (v1)

Track parcels and retrieve tracking events (no auth required).

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tracking/v1/parcels` | Get tracking events |

See [tracking-api.md](tracking-api.md) for full details.

### 3. Pickups API (v1)

Create, manage, and cancel one-time pickup orders.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/pickups/v1/organizations/{orgId}/one-time-pickups` | Create pickup order |
| `GET` | `/pickups/v1/organizations/{orgId}/one-time-pickups` | List pickup orders |
| `GET` | `/pickups/v1/organizations/{orgId}/one-time-pickups/{orderId}` | Get pickup by ID |
| `PUT` | `/pickups/v1/organizations/{orgId}/one-time-pickups/{orderId}/cancel` | Cancel pickup |
| `GET` | `/pickups/v1/cutoff-time` | Get cutoff time |

See [pickups-api.md](pickups-api.md) for full details.

### 4. Location API (v1)

Search for InPost points (replaces Points API from 2024).

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/location/v1/points` | Search points |
| `GET` | `/location/v1/points/{id}` | Get point by ID |
| `GET` | `/location/v1/points/search-by-location` | Proximity search |

See [location-api.md](location-api.md) for full details.

### 5. Returns API (v1)

Create and manage return shipments.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/returns/v1/organizations/{orgId}/shipments` | Create return shipment |
| `GET` | `/returns/v1/organizations/{orgId}/shipments/{shipmentId}` | Get return details |
| `GET` | `/returns/v1/organizations/{orgId}/shipments/{trackingNumber}/label` | Get return label |

See [returns-api.md](returns-api.md) for full details.

### 6. Webhooks

Real-time tracking event notifications.

See [webhooks.md](webhooks.md) for full details.

## Key Differences from 2024 API

| Feature | 2024 API | 2025 Global API |
|---|---|---|
| Auth endpoint | `/auth/token` | `/oauth2/token` |
| Sandbox URL | `sandbox-api.inpost-group.com` | `stage-api.inpost-group.com` |
| Route versioning | None | `/shipping/v2`, `/tracking/v1`, etc. |
| Org scoping | Not in path | `organizations/{orgId}` in all routes |
| Shipment ID | UUID | Tracking number (returned synchronously) |
| Tracking auth | Required | Not required |
| Points API | `/points` | `/location/v1/points` |
| Returns | Not supported | `/returns/v1` |
| Pickup cancel | Not supported | `PUT .../cancel` |
| Multi-parcel | Single parcel | Multiple parcels per shipment |

## Required OAuth Scopes

| Scope | Purpose |
|---|---|
| `openid` | OpenID Connect |
| `api:points:read` | Read locker/PUDO point data |
| `api:shipments:write` | Create and manage shipments |
| `api:shipments:read` | Read shipment data |
| `api:tracking:read` | Read tracking events |
| `api:one-time-pickups:write` | Create pickup orders |
| `api:one-time-pickups:read` | Read pickup orders |
| `api:returns:write` | Create return shipments |
| `api:returns:read` | Read return shipment data |
| `api:labels:read` | Retrieve shipping labels |

## HTTP Status Codes

| Code | Meaning |
|---|---|
| `200 OK` | GET/PUT success |
| `201 Created` | POST resource created |
| `202 Accepted` | Async processing accepted |
| `204 No Content` | DELETE success |
| `400 Bad Request` | Incorrect JSON data |
| `401 Unauthorized` | Invalid/expired token |
| `403 Forbidden` | Insufficient permissions |
| `404 Not Found` | Resource not found |
| `406 Not Acceptable` | Unsupported Accept header |
| `415 Unsupported Media Type` | Unsupported Content-Type |
| `422 Unprocessable Entity` | Validation errors |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Server error |
| `503 Service Unavailable` | Service temporarily down |

## Label Formats

| Format | Content-Type / Accept | Response |
|---|---|---|
| PDF A4 | `application/pdf;format=A4` | Binary |
| PDF A6 | `application/pdf;format=A6` | Binary |
| PDF A4 (JSON) | `application/pdf+json;format=A4` | JSON + Base64 |
| PDF A6 (JSON) | `application/pdf+json;format=A6` | JSON + Base64 |
| ZPL 203dpi | `text/zpl;dpi=203` | Plain text |
| ZPL 300dpi | `text/zpl;dpi=300` | Plain text |
| ZPL 203dpi (JSON) | `text/zpl+json;dpi=203` | JSON + Base64 |
| ZPL 300dpi (JSON) | `text/zpl+json;dpi=300` | JSON + Base64 |
| EPL 203dpi | `text/epl2;dpi=203` | Plain text |
| EPL 203dpi (JSON) | `text/epl2+json;dpi=203` | JSON + Base64 |
| DPL 203dpi | `text/dpl;dpi=203` | Plain text (pilot PL) |
| DPL 203dpi (JSON) | `text/dpl+json;dpi=203` | JSON + Base64 (pilot PL) |

# InPost International API 2024 — Reference

> Source: https://developers.inpost-group.com/  
> Used by connector: `integrators/courier/inpost/v2.0.0/`

## Overview

The InPost International 2024 API is a REST API that provides international shipping capabilities across multiple InPost markets (PL, UK, IT, FR, ES, BE, NL, LU, PT). It uses OAuth 2.1 for authentication and returns JSON responses.

This connector uses the **2024 version** of the API, which is the pre-versioned-route variant. For merchants going live before February 2026, InPost recommends this version.

## Base URLs

| Environment | URL |
|---|---|
| **Production** | `https://api.inpost-group.com` |
| **Sandbox** | `https://sandbox-api.inpost-group.com` |

## Authentication

OAuth 2.1 Client Credentials flow. Token endpoint: `POST /auth/token`.

See [authentication.md](authentication.md) for details.

## API Modules Used by Connector

### 1. Shipping API

Create shipments, retrieve labels and shipment details.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/shipments/{type}` | Create a shipment (type: point-to-point, address-to-point, etc.) |
| `GET` | `/shipments/{uuid}/label` | Retrieve shipment label (PDF base64) |
| `GET` | `/shipments/{uuid}` | Get shipment details by UUID |

See [shipping-api.md](shipping-api.md) for full details.

### 2. Tracking API

Track parcels and retrieve tracking events.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/track/parcels` | Get tracking events for parcels |

See [tracking-api.md](tracking-api.md) for full details.

### 3. Pickups API

Create and manage one-time pickup orders.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/one-time-pickups` | Create a one-time pickup order |
| `GET` | `/pickups/v1/organizations/{orgId}/one-time-pickups` | List pickup orders |
| `GET` | `/one-time-pickups/{orderId}` | Get pickup order by ID |
| `GET` | `/cutoff-time` | Get latest pickup cutoff time |

See [pickups-api.md](pickups-api.md) for full details.

### 4. Points API

Search for InPost points (lockers, PUDO).

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/points` | Search points with filters |
| `GET` | `/points/{id}` | Get point details by ID |
| `GET` | `/points/search-by-location` | Search points by proximity |

See [points-api.md](points-api.md) for full details.

## Shipment Types

The API supports four delivery combinations:

| Type | From → To | Description |
|---|---|---|
| **Point-to-Point** | Locker → Locker | Sender drops at locker, recipient collects from locker |
| **Address-to-Point** | Address → Locker | Courier picks up from address, recipient collects from locker |
| **Point-to-Address** | Locker → Address | Sender drops at locker, courier delivers to address |
| **Address-to-Address** | Address → Address | Full courier pickup and delivery |

## Required OAuth Scopes

| Scope | Purpose |
|---|---|
| `openid` | OpenID Connect |
| `api:points:read` | Read locker/PUDO point data |
| `api:shipments:write` | Create shipments |
| `api:tracking:read` | Read tracking events |
| `api:one-time-pickups:write` | Create pickup orders |
| `api:one-time-pickups:read` | Read pickup orders |

## HTTP Status Codes

| Code | Meaning |
|---|---|
| `200 OK` | GET/PUT success |
| `201 Created` | POST resource created |
| `204 No Content` | DELETE success |
| `400 Bad Request` | Incorrect JSON data |
| `401 Unauthorized` | Invalid/expired token |
| `403 Forbidden` | Insufficient permissions |
| `404 Not Found` | Resource not found |
| `422 Unprocessable Entity` | Validation errors |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Server error |

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

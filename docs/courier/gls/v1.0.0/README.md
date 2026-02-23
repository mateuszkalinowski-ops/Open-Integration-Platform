# GLS Courier Integration — v1.0.0

## Overview
GLS ADE Plus integration for creating shipments, retrieving labels, tracking packages, and managing courier pickups via SOAP protocol (ADE WebAPI2).

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL (Production)**: https://adeplus.gls-poland.com/adeplus/pm1/ade_webapi2.php?wsdl
- **WSDL URL (Sandbox)**: https://ade-test.gls-poland.com/adeplus/pm1/ade_webapi2.php?wsdl

## Authentication
- Session-based authentication — every operation requires an active session
- Call `adeLogin` with username/password to obtain a session ID
- Pass the session ID to all subsequent SOAP calls
- Call `adeLogout` when the session is no longer needed
- Sessions expire after a period of inactivity; the integrator must handle re-authentication

## Shipment Flow
Multi-step process:
1. **Login** — `adeLogin` to start a session
2. **Create parcel** — `adePreparingBox_Insert` to register a parcel with sender/receiver/services
3. **Create pickup** — `adePickup_Create` to schedule courier pickup for prepared parcels
4. **Get consignment** — `adePickup_GetConsign` to retrieve the consignment document (PDF)
5. **Get label** — `adePickup_GetParcelLabel` (single) or `adePickup_GetParcelsLabels` (batch)
6. **Track** — `adeTrackID_Get` to retrieve tracking history
7. **Logout** — `adeLogout` to close the session

## Available Services
| Code | Description |
|------|-------------|
| `cod` | Cash on Delivery (`srv_bool`) |
| `rod` | Return on Delivery |
| `daw` | Delivery at Work |
| `pr`  | Parcel Return |
| `s10` | Delivery before 10:00 |
| `s12` | Delivery before 12:00 |
| `sat` | Saturday delivery |
| `srs` | Saturday Return Service |
| `sds` | Same Day Service |
| `exc` | Exchange Service |
| `ppe` | Pick & Pack & Export |

## Configuration
See `.env.example` in the integrator directory for required environment variables.

## Sandbox
GLS provides a sandbox environment at `ade-test.gls-poland.com`.
Test credentials must be obtained from GLS Poland developer support.

## Rate Limits
No documented rate limits. Recommended to respect reasonable request frequency and batch label retrieval via `adePickup_GetParcelsLabels`.

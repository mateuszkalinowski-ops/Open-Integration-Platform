# UPS Courier Integration — v1.0.0

## Overview
UPS REST API integration for creating shipments, retrieving labels, tracking packages, and managing international forms via OAuth2-authenticated REST endpoints.

## External API
- **Protocol**: REST (JSON)
- **API URL (Production)**: https://onlinetools.ups.com/
- **API URL (Sandbox)**: https://wwwcie.ups.com/
- **Developer Portal**: https://developer.ups.com/
- **Documentation**: https://developer.ups.com/api/reference

## Authentication
- **OAuth2 Client Credentials** flow
- Token endpoint: `/security/v1/oauth/token`
- Requires `client_id` and `client_secret` (Base64-encoded in Authorization header)
- Access tokens are short-lived; cache and refresh before expiry
- Rate limit on token requests: ~250 tokens/day — always cache tokens

## Services
- `01` — UPS Next Day Air
- `02` — UPS 2nd Day Air
- `03` — UPS Ground
- `07` — UPS Worldwide Express
- `08` — UPS Worldwide Expedited
- `11` — UPS Standard
- `12` — UPS 3 Day Select
- `14` — UPS Next Day Air Early
- `54` — UPS Worldwide Express Plus
- `65` — UPS Saver
- `96` — UPS Worldwide Express Freight

## Label Notes
- Default label format is GIF (base64-encoded in response)
- GIF labels require 270-degree rotation for correct orientation
- Convert rotated GIF to PDF for standard printing workflows
- ZPL format available for thermal printers

## Sandbox
Sandbox available at wwwcie.ups.com with separate OAuth credentials.
Test account required — register at developer.ups.com.

## Rate Limits
- OAuth token requests: ~250/day (cache tokens aggressively)
- Shipment API: No hard documented limit, but throttling may occur above 100 req/min
- Tracking API: No hard documented limit

# Poczta Polska Courier Integration — v1.0.0

## Overview
Poczta Polska integration covering two separate SOAP services: the Tracking API (Sledzenie) for shipment status lookup, and the eNadawca API for creating shipments, generating labels, and managing courier orders. Supports Pocztex 2021 service format.

## External APIs
This integrator connects to **two independent SOAP services**:

### Tracking (Sledzenie)
- **Protocol**: SOAP (WSDL) with WSSE UsernameToken
- **WSDL URL**: https://tt.poczta-polska.pl/Sledzenie/services/Sledzenie?wsdl
- **Authentication**: WS-Security UsernameToken (username + password in SOAP header)

### Posting (eNadawca)
- **Protocol**: SOAP (WSDL) with HTTP Basic Auth
- **Endpoint (Legacy)**: https://e-nadawca.poczta-polska.pl
- **Endpoint (New, 2025+)**: https://e-nadawca.api.poczta-polska.pl/websrv/
- **Authentication**: HTTP Basic Authentication (username + password)

## Shipment Flow
Multi-step process using the eNadawca API:
1. **Clear envelope** — `clearEnvelope` to prepare a fresh posting envelope
2. **Add shipment(s)** — `addShipment` to register one or more parcels (returns GUID)
3. **Order courier** — `zamowKuriera` to schedule a courier pickup
4. **Send envelope** — `sendEnvelope` to finalize and submit the posting batch

Each shipment is identified by a system-generated **GUID**.

## Parcel Format Detection
Automatic size classification based on package dimensions:

| Format | Description |
|--------|-------------|
| S      | Small parcel |
| M      | Medium parcel |
| L      | Large parcel |
| XL     | Extra large parcel |
| 2XL    | Double extra large parcel |

## Key Capabilities
- Shipment creation with GUID-based identification
- Label generation (PDF)
- Tracking via separate WSSE-secured service
- Courier pickup ordering
- Postal office lookup
- Pocztex 2021 service support
- Automatic format detection (S/M/L/XL/2XL)

## Configuration
See `.env.example` in the integrator directory for required environment variables.

## Sandbox
Contact Poczta Polska technical support (ElektronicznyNadawca@poczta-polska.pl) to obtain sandbox access and test credentials for both the Tracking and eNadawca services.

## Rate Limits
No documented rate limits. Recommended to implement client-side throttling, especially for batch tracking queries.

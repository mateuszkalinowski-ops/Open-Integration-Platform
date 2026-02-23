# Packeta (Zásilkovna) Courier Integration — v1.0.0

## Overview
Packeta SOAP API integration for creating packets, retrieving labels, tracking shipments, and managing courier-mode deliveries across Central European pickup point networks.

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL**: https://www.zasilkovna.cz/api/soap.wsdl
- **Documentation**: https://docs.packetery.com/

## Authentication
- `apiPassword` — Single API password for all requests
- Passed in the SOAP request body

## Key Features
- Pickup point delivery across CZ, SK, PL, HU, RO, and other countries
- PP courier mode for specific courier IDs (direct-to-door via partner couriers)
- Target point and carrier pickup point selection
- Label generation (packet labels and courier labels)
- Courier number assignment for partner courier shipments
- Full packet lifecycle: create, track, cancel

## PP Courier Mode
For specific courier IDs, Packeta operates in "PP courier mode" — the packet is delivered to the recipient's door by a partner courier rather than to a pickup point. This mode requires:
- A valid courier ID (from Packeta's supported courier list)
- `carrierPickupPoint` for courier-specific pickup locations (where applicable)

## Configuration
See `.env.example` in the integrator directory for required environment variables:
- `PACKETA_API_URL` — WSDL endpoint URL
- `PACKETA_API_PASSWORD` — API password

## Sandbox
Use the same WSDL endpoint with sandbox API credentials.
Register at https://client.packeta.com/ for test account access.

## Rate Limits
No documented rate limits. Follow standard retry with exponential backoff.

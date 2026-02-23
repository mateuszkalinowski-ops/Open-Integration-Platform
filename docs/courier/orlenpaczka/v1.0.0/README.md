# Orlen Paczka Courier Integration — v1.0.0

## Overview
Orlen Paczka (formerly Paczka w Ruchu) SOAP API integration for creating shipments to Orlen pickup points, retrieving labels, tracking packages, and managing returns.

## External API
- **Protocol**: SOAP
- **Endpoint (Production)**: https://api.orlenpaczka.pl/WebServicePwRProd/WebServicePwR.asmx
- **Documentation**: https://www.paczkawruchu.pl/integracje/

## Authentication
- `PartnerID` — Numeric partner identifier assigned by Orlen Paczka
- `PartnerKey` — Secret key for request signing/authentication
- Both values included in the SOAP request header

## Key Features
- Pickup point delivery network (Orlen stations and partner points)
- Cash on Delivery (COD) support
- Parcel insurance
- Return pack support (reverse logistics)
- Label duplicate printing
- Pickup point availability lookup

## Configuration
See `.env.example` in the integrator directory for required environment variables:
- `ORLENPACZKA_API_URL` — SOAP endpoint URL
- `ORLENPACZKA_PARTNER_ID` — Partner identifier
- `ORLENPACZKA_PARTNER_KEY` — Partner secret key

## Sandbox
Contact Orlen Paczka integration team via https://www.paczkawruchu.pl/integracje/ for sandbox/test credentials.

## Rate Limits
No documented rate limits. Follow standard retry with exponential backoff.

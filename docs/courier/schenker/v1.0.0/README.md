# DB Schenker Courier Integration — v1.0.0

## Overview
DB Schenker SOAP API integration for creating transport orders, tracking shipments, retrieving labels/documents, and managing order lifecycle via WSDL-based web service.

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL (Production)**: https://api2.schenker.pl/services/TransportOrders?wsdl
- **WSDL URL (Sandbox)**: https://testapi2.schenker.pl/services/TransportOrders?wsdl

## Authentication
- HTTP Basic Auth (username + password) on every SOAP request
- Credentials provided by DB Schenker account manager

## Key Features
- SSCC (Serial Shipping Container Code) support for pallet-level tracking
- Multiple reference types: DWB (waybill), COR (customer order reference), PKG (package)
- Cash on Delivery via service code `9`
- Full order lifecycle: create, cancel, track, retrieve documents

## Configuration
See `.env.example` in the integrator directory for required environment variables:
- `SCHENKER_API_URL` — WSDL endpoint URL
- `SCHENKER_USERNAME` — HTTP Basic Auth username
- `SCHENKER_PASSWORD` — HTTP Basic Auth password

## Sandbox
Sandbox environment available at `testapi2.schenker.pl`.
Test credentials must be obtained from DB Schenker.

## Rate Limits
No documented rate limits. Follow standard retry with exponential backoff.

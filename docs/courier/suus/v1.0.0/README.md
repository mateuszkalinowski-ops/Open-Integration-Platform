# Suus Courier Integration — v1.0.0

## Overview
Suus (Rohlig Suus Logistics) SOAP API integration for creating transport orders, retrieving shipping documents/labels, and tracking shipment events.

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL (Production)**: https://wb.suus.com/webservice.php/project/Service?wsdl
- **WSDL URL (Sandbox)**: https://wbtest.suus.com/webservice.php/project/Service?wsdl
- **Documentation**: https://cms.suus.com/uploads/documents-english/documentation-ws-wb-1-17-eng.pdf

## Authentication
- `login` — Account login
- `password` — Account password
- Credentials passed in the `auth` structure within each SOAP request

## Key Features
- Transport order creation with COD and insurance services
- A6 label generation
- Shipment event tracking
- Document retrieval (labels, waybills)
- COD via `RohligCOD` service
- Insurance via `RohligUbezpieczenie3` service

## Configuration
See `.env.example` in the integrator directory for required environment variables:
- `SUUS_API_URL` — WSDL endpoint URL
- `SUUS_LOGIN` — Account login
- `SUUS_PASSWORD` — Account password

## Sandbox
Sandbox environment available at `wbtest.suus.com`.
Test credentials must be obtained from Suus/Rohlig Suus Logistics.

## Rate Limits
No documented rate limits. Follow standard retry with exponential backoff.

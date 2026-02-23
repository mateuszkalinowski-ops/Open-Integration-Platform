# DHL24 Courier Integration — v1.0.0

## Overview
DHL24 WebAPI v2 integration for creating shipments, retrieving labels, tracking packages, and managing courier bookings via SOAP protocol.

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL (Production)**: https://dhl24.com.pl/webapi2
- **WSDL URL (Sandbox)**: https://sandbox.dhl24.com.pl/webapi2
- **Documentation**: https://dhl24.com.pl/en/webapi2/doc.html
- **Current API Version**: 4.20.58

## Authentication
- Username/Password via `AuthData` structure in every SOAP request
- SAP number and account number required for some operations

## Configuration
See `.env.example` in the integrator directory for required environment variables.

## Sandbox
DHL provides a sandbox environment at sandbox.dhl24.com.pl.
Test credentials must be obtained from DHL developer support.

## Rate Limits
No documented rate limits, but recommended max 3 shipments per createShipments call.

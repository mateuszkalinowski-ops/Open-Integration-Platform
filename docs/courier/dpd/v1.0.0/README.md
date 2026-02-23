# DPD Courier Integration — v1.0.0

## Overview
DPD Poland Web Services integration for creating shipments, generating labels, booking courier pickups, and tracking packages via SOAP protocol.

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL (Production)**: https://dpdservices.dpd.com.pl/DPDPackageObjServicesService/DPDPackageObjServices?WSDL
- **WSDL URL (Sandbox)**: https://dpdservicesdemo.dpd.com.pl/DPDPackageObjServicesService/DPDPackageObjServices?WSDL
- **Events WSDL (Production)**: https://dpdservices.dpd.com.pl/DPDPackageObjEventsService/DPDPackageObjEvents?WSDL
- **Events WSDL (Sandbox)**: https://dpdservicesdemo.dpd.com.pl/DPDPackageObjEventsService/DPDPackageObjEvents?WSDL
- **Documentation**: https://dpd.com.pl/integration
- **Current API Version**: v4

## Authentication
- Login/Password + MasterFID (numeric client identifier) via `authDataV1` structure in every SOAP request
- MasterFID is assigned during account registration with DPD

## Configuration
See `.env.example` in the integrator directory for required environment variables.

## Sandbox
DPD provides a sandbox environment at dpdservicesdemo.dpd.com.pl.
Test credentials must be obtained from DPD integration support (integracja@dpd.com.pl).

## Rate Limits
Maximum 60 API calls per minute per account. Exceeding this limit results in HTTP 429 responses.

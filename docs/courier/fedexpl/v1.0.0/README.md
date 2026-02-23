# FedEx PL (IKL Service) Courier Integration — v1.0.0

## Overview
Polish FedEx integration via SOAP IKL Service for creating domestic shipments, generating labels, and handling COD/insurance services. This is a separate integration from the global FedEx REST API, specific to the Polish market (formerly Opek / TNT Poland operations).

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL**: https://poland.fedex.com/fdsWs/IklServicePort?wsdl
- **Endpoint**: `https://poland.fedex.com/fdsWs/IklServicePort`

## Authentication
Credentials are passed within every SOAP request body:

| Parameter          | Description |
|-------------------|-------------|
| `accessCode`      | API key issued by FedEx Poland |
| `senderId`        | Client ID / sender identifier |
| `courierId`       | Courier number assigned to the client |
| `bankAccountNumber` | Bank account for COD settlements |

No session management — each request is independently authenticated.

## Key Capabilities
- Create shipments with full sender/receiver/payer details
- Generate shipping labels in PDF format
- Cash on Delivery (COD) with configurable type and amount
- Insurance support
- Multi-parcel shipments
- Proof of dispatch handling

## Configuration
See `.env.example` in the integrator directory for required environment variables.

## Sandbox
Contact FedEx Poland technical support to obtain sandbox access and test credentials.

## Rate Limits
No documented rate limits. Recommended to implement client-side throttling for bulk operations.

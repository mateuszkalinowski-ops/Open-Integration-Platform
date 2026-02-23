# Geis Courier Integration — v1.0.0

## Overview
Geis SOAP API integration for creating domestic and export shipments, retrieving labels, tracking packages, managing pickups, and handling distribution channels.

## External API
- **Protocol**: SOAP (WSDL)
- **WSDL URL (Production)**: https://gservice.geis.pl/?wsdl
- **WSDL URL (Sandbox)**: https://gservicetest.geis.pl/?wsdl
- **Technical Documentation**: https://www.geis.pl/en/download-tech-support

## Authentication
- `CustomerCode` — Geis customer account number
- `Password` — Account password
- Credentials passed in the SOAP request authentication structure

## Key Features
- Domestic and international (export) shipment support
- Multiple distribution channels
- Pickup scheduling
- Label generation
- Full shipment lifecycle management (create, track, delete)
- Health check endpoint for service availability monitoring
- Waybill number range assignment

## Configuration
See `.env.example` in the integrator directory for required environment variables:
- `GEIS_API_URL` — WSDL endpoint URL
- `GEIS_CUSTOMER_CODE` — Customer account code
- `GEIS_PASSWORD` — Account password

## Sandbox
Sandbox environment available at `gservicetest.geis.pl`.
Test credentials must be obtained from Geis technical support.

## Rate Limits
No documented rate limits. Follow standard retry with exponential backoff.

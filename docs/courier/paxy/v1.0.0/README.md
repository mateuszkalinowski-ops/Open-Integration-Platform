# Paxy Courier Integration — v1.0.0

## Overview
Paxy REST API integration for creating parcels, managing registry books, retrieving labels, tracking shipments, and handling parcel cancellation.

## External API
- **Protocol**: REST (JSON)
- **API URL**: https://api.paxy.pl

## Authentication
- Custom header-based authentication
- `CL-API-KEY` — API key header
- `CL-API-TOKEN` — API token header
- Both headers required on every request

## Key Features
- Parcel creation with carrier selection
- Registry book management (books must be created before parcels)
- Label generation and printing
- Shipment tracking
- Parcel cancellation by waybill
- Carrier code and carrier type derived from `service_name` split

## Workflow
1. Create a registry book via `POST /books`
2. Create parcels linked to the book via `POST /parcels`
3. Retrieve labels via `POST /labels/print`
4. Track parcels via `POST /trackings`

## Configuration
See `.env.example` in the integrator directory for required environment variables:
- `PAXY_API_URL` — API base URL
- `PAXY_API_KEY` — CL-API-KEY value
- `PAXY_API_TOKEN` — CL-API-TOKEN value

## Sandbox
Contact Paxy for sandbox/test credentials and environment details.

## Rate Limits
No documented rate limits. Follow standard retry with exponential backoff.

# DHL Express Courier Integration — v1.0.0

## Overview
DHL Express MyDHL API integration for creating international shipments, retrieving labels, tracking packages, managing pickups, and checking rates via REST protocol.

## External API
- **Protocol**: REST (JSON)
- **Base URL (Production)**: `https://express.api.dhl.com/mydhlapi`
- **Base URL (Test/Sandbox)**: `https://express.api.dhl.com/mydhlapi/test`
- **Developer Portal**: https://developer.dhl.com
- **API Reference**: https://developer.dhl.com/api-reference/dhl-express-mydhl-api
- **Current API Version**: 3.2.0

## Authentication
- **Method**: HTTP Basic Authentication
- **Header**: `Authorization: Basic <Base64(API_KEY:API_SECRET)>`
- API Key and Secret obtained from the DHL Developer Portal after creating an app

## Configuration
See `.env.example` in the integrator directory for required environment variables.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/readiness` | Readiness check (credentials configured?) |
| POST | `/shipments` | Create a DHL Express shipment |
| GET | `/shipments/{tracking_number}/status` | Get tracking status |
| GET | `/shipments/{tracking_number}/label` | Download label PDF |
| GET | `/shipments/{tracking_number}/documents` | Get document images |
| POST | `/rates` | Get rates and product availability |
| GET | `/products` | Lightweight product lookup |
| POST | `/pickups` | Request courier pickup |
| PATCH | `/pickups/{id}` | Update pickup |
| DELETE | `/pickups/{id}` | Cancel pickup |
| GET | `/address-validate` | Validate delivery/pickup capability |
| GET | `/points` | Find DHL Express service points |
| POST | `/landed-cost` | Estimate duties & taxes |

## Quick Start

```bash
# Copy env and fill in API credentials
cp .env.example .env

# Run with Docker
docker compose up -d

# Or run locally
python -m venv .venv && source .venv/bin/activate
pip install -e ../../../shared/python
pip install -r requirements.txt
uvicorn src.app:app --reload --port 8001
```

## Rate Limits
- Test environment: 500 API calls per day
- Production: no hard limit, but follow DHL guidelines

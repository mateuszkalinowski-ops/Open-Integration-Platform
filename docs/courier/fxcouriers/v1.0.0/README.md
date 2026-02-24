# FX Couriers — Courier Integrator v1.0.0

## Overview

FX Couriers connector for the Open Integration Platform. Integrates with the KurierSystem REST API to provide:

- Transport order creation and management
- Shipping label generation (PDF)
- Shipment pickup scheduling
- Order tracking and status monitoring
- Available services configuration

## API Documentation

- Swagger UI: https://fxcouriers.kuriersystem.pl/api/rest/ui/
- OpenAPI JSON: https://fxcouriers.kuriersystem.pl/api/rest/docs
- Polish docs: https://fxcouriers.kuriersystem.pl/api/dokumentacja_pl.html

## Authentication

FX Couriers uses **Bearer token** authentication. A static API token is provided by the FX Couriers sales representative and must be included in the `Authorization` header of every request:

```
Authorization: Bearer <your_api_token>
```

No OAuth flow is required — the token is long-lived.

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `FXCOURIERS_API_URL` | No | `https://fxcouriers.kuriersystem.pl/api/rest` | Base API URL |
| `APP_ENV` | No | `development` | Environment (`development` / `production`) |
| `APP_PORT` | No | `8000` | Application port |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `REST_TIMEOUT` | No | `30` | HTTP request timeout in seconds |

## Credentials (per-tenant)

| Field | Required | Description |
|---|---|---|
| `api_token` | Yes | Bearer API token |
| `company_id` | No | Company ID for multi-company accounts |

## Deployment

### Docker

```bash
cd integrators/courier/fxcouriers/v1.0.0
docker build -t integrations/courier/fxcouriers:1.0.0 .
docker run --rm -p 8000:8000 --env-file .env integrations/courier/fxcouriers:1.0.0
```

### Docker Compose

```bash
cd integrators/courier/fxcouriers/v1.0.0
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

The service will be available at `http://localhost:8019`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/readiness` | Readiness check |
| `GET` | `/services` | List available services |
| `GET` | `/company/{id}` | Get company info |
| `POST` | `/shipments` | Create transport order |
| `GET` | `/shipments` | List orders |
| `GET` | `/shipments/{id}` | Get order details |
| `DELETE` | `/shipments/{id}` | Delete order |
| `GET` | `/shipments/{id}/status` | Get order status |
| `GET` | `/tracking/{id}` | Get tracking info |
| `POST` | `/labels` | Get label PDF |
| `POST` | `/pickups` | Schedule pickup |
| `GET` | `/pickups/{id}` | Get pickup details |
| `DELETE` | `/pickups/{id}` | Cancel pickup |

## Status Mapping

| FX Couriers Status | Platform Status |
|---|---|
| NEW | CREATED |
| WAITING_APPROVAL | CREATED |
| ACCEPTED | CONFIRMED |
| RUNNING | IN_TRANSIT |
| PICKUP | PICKED_UP |
| CLOSED | DELIVERED |
| RETURN | RETURNED |
| PROBLEM | FAILED |
| FAILED | FAILED |
| CANCELLED | CANCELLED |

## Testing

```bash
cd integrators/courier/fxcouriers/v1.0.0
pip install -r requirements.txt
pip install pytest pytest-asyncio
pytest tests/ -v
```

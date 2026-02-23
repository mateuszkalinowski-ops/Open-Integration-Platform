# Raben Group — Courier Integrator v1.0.0

## Overview

Raben Group logistics integration for the Open Integration Platform by Pinquark.com. Provides connectivity with Raben's myRaben platform for freight transport management across Europe.

**Raben Group** operates in 17 European countries providing:
- Domestic and international freight transport (LTL/FTL)
- Palletized shipment management
- Contract logistics and warehousing
- Real-time ETA tracking
- Photo Confirming Delivery (PCD)

## Capabilities

| Capability | Endpoint | Description |
|---|---|---|
| Create transport order | `POST /shipments` | Create a new transport order (myOrder) |
| Get shipment details | `GET /shipments/{waybill}` | Retrieve order details |
| Cancel shipment | `PUT /shipments/{waybill}/cancel` | Cancel a transport order |
| Track shipment | `GET /tracking/{waybill}` | Full tracking history |
| Get status | `GET /shipments/{waybill}/status` | Current status with ETA |
| Get ETA | `GET /shipments/{waybill}/eta` | Estimated time of arrival |
| Get label | `POST /labels` | Shipping label (PDF/ZPL) |
| Submit claim | `POST /claims` | Submit a complaint (myClaim) |
| Get delivery confirmation | `GET /deliveries/{waybill}/confirmation` | PCD with photos |

## Service Types

| Service | Description | Delivery Time |
|---|---|---|
| `cargo_classic` | Standard delivery | 24/48 hours |
| `cargo_premium` | Priority delivery | Same/next day |
| `cargo_premium_08` | Time-definite | By 08:00 |
| `cargo_premium_10` | Time-definite | By 10:00 |
| `cargo_premium_12` | Time-definite | By 12:00 |
| `cargo_premium_16` | Time-definite | By 16:00 |

## Configuration

### Required Parameters

| Parameter | Description |
|---|---|
| `username` | myRaben login / API username |
| `password` | myRaben password / API password |

### Optional Parameters

| Parameter | Default | Description |
|---|---|---|
| `customer_number` | — | Raben customer number |
| `sandbox_mode` | `false` | Use sandbox API |
| `default_service_type` | `cargo_classic` | Default service type |

### Environment Variables

```bash
APP_ENV=development          # development / production
APP_PORT=8000                # HTTP port
LOG_LEVEL=INFO               # DEBUG / INFO / WARNING / ERROR
REST_TIMEOUT=30              # HTTP timeout in seconds
RABEN_API_URL=https://myraben.com/api/v1
RABEN_SANDBOX_API_URL=https://sandbox.myraben.com/api/v1
```

## Setup

### Local Development

```bash
cd integrators/courier/raben/v1.0.0
cp .env.example .env         # Configure environment variables
docker compose up -d          # Start the integrator
```

### Manual Run

```bash
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

### Docker Build

```bash
docker build -t integrations/courier/raben:1.0.0 .
docker run --rm -p 8000:8000 --env-file .env integrations/courier/raben:1.0.0
```

## Testing

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

## API Documentation

After starting the service, Swagger UI is available at: `http://localhost:8000/docs`

## Health Checks

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /readiness` | Readiness check (dependencies) |

## Additional Services

### PCD (Photo Confirming Delivery)
Enable PCD when creating a transport order by setting `pcd_enabled: true`. After delivery, retrieve delivery confirmation photos via `GET /deliveries/{waybill}/confirmation`.

### ETA (Estimated Time of Arrival)
ETA is calculated based on GPS position of the delivery vehicle. It provides a +/- 2 hour delivery window. ETA updates automatically if deviations of 60+ minutes are detected.

### Email Notifications
Enable `email_notification: true` when creating an order to send automatic notifications to the receiver:
1. Shipment registration notification
2. Loading on delivery vehicle notification
3. ETA notification with estimated delivery time window

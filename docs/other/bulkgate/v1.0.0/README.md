# BulkGate SMS Gateway — Connector v1.0.0

## Overview

BulkGate SMS Gateway connector for the Open Integration Platform.  
Provides transactional SMS, bulk/promotional SMS, advanced multi-channel messaging (SMS + Viber cascade), credit balance checks, and delivery report webhooks.

**Category**: Other (SMS Gateway)  
**Protocol**: REST (HTTP API)  
**External API versions**: Simple API v1.0, Advanced API v2.0

## Features

- **Transactional SMS** — single recipient, high priority (Simple API v1.0)
- **Promotional/Bulk SMS** — multiple recipients, marketing campaigns (Simple API v1.0)
- **Advanced transactional SMS** — template variables, multi-channel cascade SMS → Viber (Advanced API v2.0)
- **Credit balance** — check account wallet, credits, and free messages
- **Delivery report webhooks** — receive delivery status updates via HTTP push
- **Incoming SMS webhooks** — receive reply messages
- **Sender ID types** — system number, short code, text sender, own number, BulkGate profile
- **Scheduled sending** — unix timestamp or ISO 8601
- **Unicode support** — full character set including non-latin alphabets
- **Duplicate check** — prevent sending same message to same number within 5 minutes

## Quick Start

### 1. Get BulkGate API credentials

1. Sign up at [BulkGate Portal](https://portal.bulkgate.com/sign/up)
2. Go to **Modules & APIs** → **Create API**
3. Select HTTP API and note your `application_id` and `application_token`

### 2. Configuration

Copy `.env.example` to `.env` and configure:

```bash
APP_ENV=development
APP_PORT=8000
LOG_LEVEL=INFO
REST_TIMEOUT=30
BULKGATE_API_URL=https://portal.bulkgate.com
```

### 3. Run locally

```bash
docker compose up -d
```

The API is available at `http://localhost:8000`.  
Swagger docs: `http://localhost:8000/docs`

### 4. Run tests

```bash
docker compose --profile test run --rm test-runner
```

Or locally:

```bash
pip install -r requirements.txt pytest pytest-asyncio
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/readiness` | Readiness check |
| POST | `/sms/transactional` | Send transactional SMS (single recipient) |
| POST | `/sms/promotional` | Send promotional/bulk SMS (multiple recipients) |
| POST | `/sms/advanced` | Send advanced transactional SMS (templates, multi-channel) |
| POST | `/account/balance` | Check credit balance |
| POST | `/webhooks/delivery-report` | Receive delivery report callbacks |
| POST | `/webhooks/incoming-sms` | Receive incoming SMS replies |
| GET | `/docs` | Swagger UI |

## Authentication

All SMS and account endpoints require BulkGate credentials in the request body:

```json
{
  "credentials": {
    "application_id": "YOUR_APPLICATION_ID",
    "application_token": "YOUR_APPLICATION_TOKEN"
  }
}
```

Credentials are passed per-request and are never stored by the connector.

## Example: Send Transactional SMS

```bash
curl -X POST http://localhost:8000/sms/transactional \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "application_id": "12345",
      "application_token": "your-token"
    },
    "number": "420777777777",
    "text": "Your order #1234 has been shipped.",
    "sender_id": "gText",
    "sender_id_value": "MyShop"
  }'
```

## Example: Send Advanced SMS with Viber Fallback

```bash
curl -X POST http://localhost:8000/sms/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "application_id": "12345",
      "application_token": "your-token"
    },
    "number": ["420777777777", "420888888888"],
    "text": "Hello <first_name>, your delivery arrives at <time>.",
    "variables": {"first_name": "Jan", "time": "14:00"},
    "channel": {
      "viber": {"sender": "MyShop", "expiration": 120},
      "sms": {"sender_id": "gText", "sender_id_value": "MyShop", "unicode": true}
    },
    "country": "CZ"
  }'
```

## Deployment

```bash
docker build -t your-registry.example.com/integrations/other/bulkgate:1.0.0 .
docker push your-registry.example.com/integrations/other/bulkgate:1.0.0
```

## External Resources

- [BulkGate Developer Docs](https://www.bulkgate.com/en/developers/sms-api/)
- [HTTP Simple API](https://help.bulkgate.com/docs/en/http-simple-transactional.html)
- [HTTP Advanced API v2](https://help.bulkgate.com/docs/en/http-advanced-transactional-v2.html)
- [Error Types](https://help.bulkgate.com/docs/en/api-error-types.html)
- [BulkGate Portal](https://portal.bulkgate.com/)

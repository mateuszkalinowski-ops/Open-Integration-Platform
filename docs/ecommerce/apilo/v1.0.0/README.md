# Apilo Integrator v1.0.0

E-commerce integration between the Pinquark Open Integration Platform and the [Apilo REST API](https://developer.apilo.com/api/).

## Overview

Apilo is a multi-channel e-commerce management platform popular in Poland. This integrator connects Apilo accounts to the Pinquark platform, enabling:

- **Order management** — fetch, create, update status, add payments, notes, tags, shipments, documents
- **Product catalog** — list, create, update, delete products; manage categories and attributes
- **Shipment management** — create shipments, track status, confirm pickup
- **Finance documents** — list and manage accounting documents (invoices, receipts, proformas)
- **Background polling** — automatically scrape new/updated orders via configurable interval

## Authentication

Apilo uses OAuth2 with Basic Auth for token exchange:

1. Create an API application in Apilo Admin > API
2. Use the `authorization_code` to obtain initial `access_token` and `refresh_token`
3. Access tokens are valid for **21 days**, refresh tokens for **2 months**
4. The integrator handles automatic token refresh

## Rate Limiting

Apilo API limit: **150 requests/minute**. The client implements automatic retry with backoff on HTTP 429 responses.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `APILO_ACCOUNT_0_NAME` | Yes | — | Account identifier |
| `APILO_ACCOUNT_0_CLIENT_ID` | Yes | — | OAuth2 Client ID |
| `APILO_ACCOUNT_0_CLIENT_SECRET` | Yes | — | OAuth2 Client Secret |
| `APILO_ACCOUNT_0_AUTHORIZATION_CODE` | Yes* | — | Initial authorization code |
| `APILO_ACCOUNT_0_REFRESH_TOKEN` | No | — | Refresh token (if already obtained) |
| `APILO_ACCOUNT_0_BASE_URL` | No | `https://app.apilo.com` | Apilo instance URL |
| `APILO_SCRAPING_ENABLED` | No | `true` | Enable background order polling |
| `APILO_SCRAPING_INTERVAL_SECONDS` | No | `300` | Polling interval in seconds |
| `KAFKA_ENABLED` | No | `false` | Publish orders to Kafka |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./apilo_integrator.db` | State DB |

*Required for initial token exchange; can be omitted if `REFRESH_TOKEN` is provided.

### YAML Configuration

Alternatively, configure accounts in `config/accounts.yaml`:

```yaml
accounts:
  - name: my-store
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    authorization_code: "your-auth-code"
    base_url: "https://app.apilo.com"
    environment: production
```

## Running

### Docker Compose (development)

```bash
docker compose --profile dev up
```

### Docker Compose (production)

```bash
docker compose up -d apilo-integrator
```

### Running Tests

```bash
docker compose --profile test up --abort-on-container-exit
```

Or locally:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/readiness` | Readiness check |
| `GET` | `/accounts` | List accounts |
| `POST` | `/accounts` | Add account |
| `DELETE` | `/accounts/{name}` | Remove account |
| `GET` | `/orders` | List orders |
| `GET` | `/orders/{id}` | Get order details |
| `POST` | `/orders` | Create order |
| `PUT` | `/orders/{id}/status` | Update order status |
| `POST` | `/orders/{id}/payment` | Add payment |
| `POST` | `/orders/{id}/note` | Add note |
| `POST` | `/orders/{id}/shipment` | Add shipment |
| `POST` | `/orders/{id}/tag` | Add tag |
| `DELETE` | `/orders/{id}/tag/{tagId}` | Remove tag |
| `GET` | `/products` | List/search products |
| `GET` | `/products/{id}` | Get product |
| `POST` | `/stock/sync` | Sync stock levels |
| `POST` | `/shipments` | Create shipment |
| `GET` | `/shipments/{id}` | Get shipment |
| `GET` | `/maps` | Get reference maps |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/docs` | Swagger UI |

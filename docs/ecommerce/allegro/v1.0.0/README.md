# Allegro Integrator v1.0.0

E-commerce integration between **pinquark WMS** and **Allegro** marketplace.

## Features

- **Multi-account support** — one container handles multiple Allegro seller accounts
- **OAuth2 Device Flow** — secure authentication without exposing credentials
- **Automatic order scraping** — polls Allegro order events on a configurable interval
- **Order status sync** — bidirectional status synchronization (WMS ↔ Allegro)
- **Stock sync** — push stock levels from WMS to Allegro offers
- **Product enrichment** — fetches EAN, SKU from Allegro offers/products
- **Kafka integration** — publishes orders to Kafka for WMS consumption (optional)
- **Encrypted token storage** — AES-256-GCM encrypted OAuth tokens in database

## Quick Start

### 1. Configure accounts

Edit `config/accounts.yaml` with your Allegro app credentials:

```yaml
accounts:
  - name: my-shop
    client_id: "YOUR_CLIENT_ID"
    client_secret: "YOUR_CLIENT_SECRET"
    api_url: "https://api.allegro.pl"
    auth_url: "https://allegro.pl/auth/oauth"
    environment: production
```

### 2. Start the integrator

```bash
# Development mode (hot-reload, no Kafka)
docker compose --profile dev up allegro-integrator-dev

# Production mode
docker compose up allegro-integrator
```

### 3. Authenticate

```bash
# Step 1: Start device flow
curl -X POST http://localhost:8000/auth/my-shop/device-code

# Response: visit the verification_uri and enter the user_code

# Step 2: Poll for token (after authorizing in browser)
curl -X POST http://localhost:8000/auth/my-shop/poll-token
```

### 4. Use the API

```bash
# List orders
curl "http://localhost:8000/orders?account_name=my-shop"

# Get specific order
curl "http://localhost:8000/orders/CHECKOUT_FORM_ID?account_name=my-shop"

# Update order status
curl -X PUT "http://localhost:8000/orders/CHECKOUT_FORM_ID/status?account_name=my-shop" \
  -H "Content-Type: application/json" \
  -d '{"status": "SHIPPED"}'

# Sync stock
curl -X POST "http://localhost:8000/stock/sync?account_name=my-shop" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"sku": "OFFER_ID", "product_id": "OFFER_ID", "quantity": 10}]}'
```

## API Documentation

Swagger UI is available at `http://localhost:8000/docs` when the integrator is running.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/readiness` | Readiness check (includes dependency checks) |
| GET | `/metrics` | Prometheus metrics |
| POST | `/auth/{account}/device-code` | Start OAuth2 device flow |
| POST | `/auth/{account}/poll-token` | Poll for token after authorization |
| GET | `/auth/{account}/status` | Check auth status for account |
| GET | `/auth/status` | Check auth status for all accounts |
| GET | `/accounts` | List configured accounts |
| POST | `/accounts` | Add a new account at runtime |
| DELETE | `/accounts/{name}` | Remove an account |
| GET | `/orders` | List orders (paginated) |
| GET | `/orders/{id}` | Get a single order |
| PUT | `/orders/{id}/status` | Update order fulfillment status |
| POST | `/stock/sync` | Synchronize stock levels |
| GET | `/products/{id}` | Get product/offer details |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLEGRO_LOG_LEVEL` | `INFO` | Logging level |
| `ALLEGRO_DEBUG` | `false` | Debug mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///...` | Database URL for token persistence |
| `DATABASE_ENCRYPTION_KEY` | _(empty)_ | Base64 AES-256 key for token encryption |
| `KAFKA_ENABLED` | `false` | Enable Kafka order publishing |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `ALLEGRO_SCRAPING_ENABLED` | `true` | Enable background order scraping |
| `ALLEGRO_SCRAPING_INTERVAL_SECONDS` | `60` | Scraping poll interval |

## Architecture

```
                      ┌─────────────────────────────────┐
                      │  Allegro Integrator Container    │
                      │                                 │
 Allegro API ◄───────►│  ┌────────────┐  ┌──────────┐ │
                      │  │ Auth Mgr   │  │ Scraper  │ │
                      │  │ (OAuth2)   │  │ (events) │ │
                      │  └────────────┘  └──────────┘ │
                      │  ┌────────────┐  ┌──────────┐ │
 REST API ◄──────────►│  │ FastAPI    │  │ Kafka    │ │──────► pinquark WMS
                      │  │ Routes     │  │ Producer │ │
                      │  └────────────┘  └──────────┘ │
                      │  ┌────────────────────────────┐│
                      │  │ SQLite (encrypted tokens)  ││
                      │  └────────────────────────────┘│
                      └─────────────────────────────────┘
```

## Running Tests

```bash
# Via Docker
docker compose --profile test up tests

# Locally
pip install -r requirements-dev.txt
pytest tests/ -v
```

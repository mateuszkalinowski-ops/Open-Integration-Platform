# Shopify Integrator v1.0.0

E-commerce integration between the pinquark Integration Platform and Shopify stores.

## Overview

This connector synchronizes orders, products, customers, inventory levels, and fulfillments between pinquark WMS and one or more Shopify stores.

### Capabilities

| Feature | Direction | Description |
|---|---|---|
| Orders | Shopify → Platform | Fetch orders (polling), map to unified schema |
| Order Status | Platform → Shopify | Update fulfillment status, create fulfillments, cancel/close orders |
| Products | Bidirectional | Get products from Shopify, sync products to Shopify |
| Stock | Platform → Shopify | Sync inventory levels via Inventory API |
| Customers | Shopify → Platform | Customer data extracted from orders |

### Shopify API Version

This connector uses the **Shopify Admin REST API 2024-07**.

## Setup

### 1. Create a Shopify Custom App

1. Go to your Shopify Admin → **Settings** → **Apps and sales channels** → **Develop apps**
2. Click **Create an app** and name it (e.g., "pinquark Integration")
3. Configure **Admin API scopes**:
   - `read_orders`, `write_orders`
   - `read_products`, `write_products`
   - `read_inventory`, `write_inventory`
   - `read_fulfillments`, `write_fulfillments`
   - `read_customers`
   - `read_locations`
4. Click **Install app** and copy the **Admin API access token** (`shpat_...`)

### 2. Configure the Connector

#### Option A: accounts.yaml (recommended)

```yaml
accounts:
  - name: my-store
    shop_url: my-store.myshopify.com
    access_token: shpat_xxxxx
    api_version: "2024-07"
    default_location_id: "12345678"
    default_carrier: "Kurier"
```

#### Option B: Environment variables

```bash
SHOPIFY_ACCOUNT_0_NAME=my-store
SHOPIFY_ACCOUNT_0_SHOP_URL=my-store.myshopify.com
SHOPIFY_ACCOUNT_0_ACCESS_TOKEN=shpat_xxxxx
SHOPIFY_ACCOUNT_0_API_VERSION=2024-07
SHOPIFY_ACCOUNT_0_DEFAULT_LOCATION_ID=12345678
```

### 3. Run with Docker

```bash
# Build
docker build -t integrations/ecommerce/shopify:1.0.0 .

# Run standalone
docker compose up shopify-integrator

# Run development mode (hot reload)
docker compose --profile dev up shopify-integrator-dev

# Run tests
docker compose --profile test up tests
```

### 4. Find your Location ID

Call `GET /admin/api/2024-07/locations.json` or use the connector's API after startup. The location ID is required for inventory sync.

## API Reference

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/readiness` | Full readiness check |

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/{account_name}/validate` | Validate access token |
| GET | `/auth/{account_name}/status` | Get auth status |
| GET | `/auth/status` | Get all auth statuses |

### Accounts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/accounts` | List accounts |
| POST | `/accounts` | Add account |
| DELETE | `/accounts/{name}` | Remove account |

### Orders

| Method | Endpoint | Description |
|---|---|---|
| GET | `/orders?account_name=...` | List orders |
| GET | `/orders/{id}?account_name=...` | Get order |
| PUT | `/orders/{id}/status?account_name=...` | Update status |
| POST | `/orders/{id}/fulfill?account_name=...` | Create fulfillment |

### Products

| Method | Endpoint | Description |
|---|---|---|
| GET | `/products/{id}?account_name=...` | Get product |
| POST | `/products/sync?account_name=...` | Sync products |

### Stock

| Method | Endpoint | Description |
|---|---|---|
| POST | `/stock/sync?account_name=...` | Sync inventory |

### Metrics

| Endpoint | Description |
|---|---|
| `/metrics` | Prometheus metrics |
| `/docs` | Swagger UI |

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `SHOPIFY_LOG_LEVEL` | `INFO` | Log level |
| `SHOPIFY_DEBUG` | `false` | Debug mode |
| `SHOPIFY_SCRAPING_ENABLED` | `true` | Enable order polling |
| `SHOPIFY_SCRAPING_INTERVAL_SECONDS` | `60` | Polling interval |
| `DATABASE_URL` | SQLite | Token/state persistence |
| `DATABASE_ENCRYPTION_KEY` | (empty) | AES-256 key for token encryption |
| `KAFKA_ENABLED` | `false` | Enable Kafka publishing |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka servers |

## Rate Limits

Shopify applies a [leaky bucket](https://shopify.dev/docs/api/usage/rate-limits) rate limit:
- REST Admin API: **40 requests/second** (bucket size 80)
- The connector monitors the `X-Shopify-Shop-Api-Call-Limit` header
- Automatic retry with backoff on HTTP 429

## Architecture

```
┌─────────────┐     REST API     ┌───────────────────┐     REST API     ┌─────────────┐
│  pinquark   │ ◄──────────────► │ Shopify Integrator │ ◄──────────────► │   Shopify   │
│  Platform   │                  │    (FastAPI)       │                  │   Store     │
│             │     Kafka        │                    │                  │             │
│             │ ◄──────────────  │  Order Scraper     │                  │             │
└─────────────┘                  └───────────────────┘                  └─────────────┘
```

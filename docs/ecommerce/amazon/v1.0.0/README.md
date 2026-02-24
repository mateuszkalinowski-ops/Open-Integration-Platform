# Amazon Integrator v1.0.0

E-commerce integration connector for the **Amazon Selling Partner API (SP-API)**.

## Features

- **Order Management** — Fetch orders, get order details/items, acknowledge orders, confirm shipments
- **Status Updates** — Update order status via Feeds API (acknowledgement, shipment confirmation, cancellation)
- **Product Catalog** — Search products by keyword/identifier, get product details by ASIN
- **Stock Sync** — Push inventory levels via Feeds API (POST_INVENTORY_AVAILABILITY_DATA)
- **Reports** — Create and retrieve Amazon reports (listings, orders, inventory)
- **Feed Management** — Submit and track feed processing status
- **Background Scraping** — Automatic polling for new/updated orders with Kafka publishing
- **Multi-Account** — Support for multiple Amazon seller accounts (different marketplaces/regions)
- **OAuth2 Auth** — LWA (Login with Amazon) token management with automatic refresh

## Prerequisites

- Amazon Seller Central developer account
- Registered SP-API application (`client_id` + `client_secret`)
- Seller authorization (`refresh_token`)
- Marketplace ID for the target marketplace

## Quick Start

### 1. Configure accounts

Copy the template and fill in real credentials:

```bash
cp config/accounts.yaml.example config/accounts.yaml
```

Or use environment variables:

```bash
export AMAZON_ACCOUNT_0_NAME=my-seller
export AMAZON_ACCOUNT_0_CLIENT_ID=amzn1.application-oa2-client.xxxx
export AMAZON_ACCOUNT_0_CLIENT_SECRET=your-client-secret
export AMAZON_ACCOUNT_0_REFRESH_TOKEN=Atzr|XXXX
export AMAZON_ACCOUNT_0_MARKETPLACE_ID=A1PA6795UKMFR9
export AMAZON_ACCOUNT_0_REGION=eu
```

### 2. Run with Docker

```bash
# Production
docker compose up -d amazon-integrator

# Development (hot reload)
docker compose --profile dev up -d amazon-integrator-dev

# Run tests
docker compose --profile test up --abort-on-container-exit tests
```

### 3. Run locally

```bash
pip install -r requirements.txt
pip install -e ../../shared/python/
uvicorn src.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/readiness` | Readiness check |
| `GET` | `/accounts` | List configured accounts |
| `POST` | `/accounts` | Add account |
| `DELETE` | `/accounts/{name}` | Remove account |
| `GET` | `/orders` | Fetch orders (with pagination) |
| `GET` | `/orders/{order_id}` | Get single order with items |
| `PUT` | `/orders/{order_id}/status` | Update order status |
| `POST` | `/orders/{order_id}/acknowledge` | Acknowledge order |
| `POST` | `/orders/{order_id}/ship` | Confirm shipment with tracking |
| `POST` | `/stock/sync` | Sync inventory levels |
| `GET` | `/products/{asin}` | Get product by ASIN |
| `POST` | `/products/search` | Search catalog items |
| `POST` | `/reports` | Create a report |
| `GET` | `/reports/{report_id}` | Get report status |
| `GET` | `/feeds/{feed_id}` | Get feed processing status |
| `GET` | `/docs` | OpenAPI/Swagger UI |
| `GET` | `/metrics` | Prometheus metrics |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AMAZON_LOG_LEVEL` | `INFO` | Log level |
| `AMAZON_DEBUG` | `false` | Debug mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///...` | State store DB |
| `KAFKA_ENABLED` | `false` | Enable Kafka publishing |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `AMAZON_SCRAPING_ENABLED` | `true` | Enable order polling |
| `AMAZON_SCRAPING_INTERVAL_SECONDS` | `300` | Polling interval |

### Amazon Marketplace IDs

| Marketplace | ID |
|---|---|
| US | `ATVPDKIKX0DER` |
| Canada | `A2EUQ1WTGCTBG2` |
| UK | `A1F83G8C2ARO7P` |
| Germany | `A1PA6795UKMFR9` |
| France | `A13V1IB3VIYBER` |
| Italy | `APJ6JRA9NG5V4` |
| Spain | `A1RKKUPIHCS9HS` |
| Japan | `A1VC38T7YXB528` |
| Australia | `A39IBJ37TRP1C6` |

### SP-API Regions

| Region | Endpoint | Marketplaces |
|---|---|---|
| `na` | sellingpartnerapi-na.amazon.com | US, Canada, Mexico, Brazil |
| `eu` | sellingpartnerapi-eu.amazon.com | UK, DE, FR, IT, ES, NL, SE, PL, TR, etc. |
| `fe` | sellingpartnerapi-fe.amazon.com | Japan, Australia, Singapore, India |

## Rate Limits

The SP-API uses token bucket rate limiting. Key limits:

| API | Rate | Burst |
|---|---|---|
| `getOrders` | 0.0167/s | 20 |
| `getOrder` | 0.5/s | 30 |
| `getOrderItems` | 0.5/s | 30 |
| `searchCatalogItems` | 2/s | — |
| `createFeed` | 0.0083/s | 15 |
| `getFeed` | 2/s | 15 |
| `createReport` | 0.0167/s | 15 |

The integrator handles 429 responses with automatic retry using `Retry-After` headers.

## Architecture

```
┌──────────────────┐     ┌──────────────────┐
│ Pinquark         │     │ Amazon SP-API    │
│ Platform / WMS   │────▶│                  │
│                  │◀────│ Orders, Catalog, │
│                  │     │ Feeds, Reports   │
└──────────────────┘     └──────────────────┘
        │                        ▲
        │   ┌────────────────┐   │
        └──▶│ Amazon         │───┘
            │ Integrator     │
            │ (this service) │
            └────────────────┘
                    │
              ┌─────┴─────┐
              │ SQLite     │  (scraper state)
              │ Kafka      │  (event publishing)
              └────────────┘
```

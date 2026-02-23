# WooCommerce Integrator v1.0.0

E-commerce integration between pinquark WMS and WooCommerce (WordPress) stores.

## Overview

This connector integrates with the WooCommerce REST API v3 to provide:

- **Order synchronization** — Fetch orders, update order statuses
- **Stock management** — Sync stock quantities by SKU or product ID
- **Product catalog** — Read and sync products to WooCommerce
- **Background scraping** — Automated polling for new/modified orders

## Quick Start

### Prerequisites

- WooCommerce store with REST API enabled (WooCommerce → Settings → Advanced → REST API)
- Consumer Key and Consumer Secret generated with Read/Write permissions
- Python 3.12+ or Docker

### Generate API Keys

1. Go to **WooCommerce → Settings → Advanced → REST API** in WordPress admin
2. Click **Add Key**
3. Set **Description**, select **User**, set **Permissions** to **Read/Write**
4. Click **Generate API Key**
5. Save the **Consumer Key** (`ck_...`) and **Consumer Secret** (`cs_...`)

### Configuration

1. Copy `.env.example` to `.env` and fill in values
2. Edit `config/accounts.yaml` with your store credentials

```yaml
accounts:
  - name: my-store
    store_url: "https://my-shop.example.com"
    consumer_key: "ck_xxxxx"
    consumer_secret: "cs_xxxxx"
    api_version: "wc/v3"
    verify_ssl: true
    environment: production
```

### Run with Docker

```bash
# Production
docker compose up -d woocommerce-integrator

# Development (with hot reload)
docker compose --profile dev up woocommerce-integrator-dev

# Run tests
docker compose --profile test up tests
```

### Run Locally

```bash
cd integrators/ecommerce/woocommerce/v1.0.0
pip install -r requirements.txt
pip install -e ../../shared/python

# Configure accounts in config/accounts.yaml
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/readiness` | Readiness check (incl. DB) |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/accounts` | List configured store accounts |
| `POST` | `/accounts` | Add a new store account |
| `DELETE` | `/accounts/{name}` | Remove a store account |
| `GET` | `/auth/{account}/status` | Check auth status |
| `POST` | `/auth/{account}/test` | Test API connection |
| `GET` | `/orders?account_name=...` | List orders (paginated) |
| `GET` | `/orders/{id}?account_name=...` | Get single order |
| `PUT` | `/orders/{id}/status?account_name=...` | Update order status |
| `POST` | `/stock/sync?account_name=...` | Sync stock levels |
| `GET` | `/products/{id}?account_name=...` | Get single product |
| `POST` | `/products/sync?account_name=...` | Sync products |

## Authentication

WooCommerce uses API key authentication:

- **HTTPS** connections: Basic Auth with `consumer_key:consumer_secret`
- **HTTP** connections: OAuth 1.0a with HMAC-SHA256 signature

The connector automatically selects the correct method based on the store URL scheme.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WOOCOMMERCE_LOG_LEVEL` | `INFO` | Logging level |
| `WOOCOMMERCE_DEBUG` | `false` | Debug mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/woo.db` | State database |
| `DATABASE_ENCRYPTION_KEY` | (empty) | AES-256 key (base64) |
| `KAFKA_ENABLED` | `false` | Enable Kafka publishing |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka brokers |
| `WOOCOMMERCE_SCRAPING_ENABLED` | `true` | Enable order scraping |
| `WOOCOMMERCE_SCRAPING_INTERVAL_SECONDS` | `60` | Scraping interval |

## Status Mapping

| WooCommerce Status | Unified Status |
|--------------------|----------------|
| `pending` | `NEW` |
| `processing` | `PROCESSING` |
| `on-hold` | `PROCESSING` |
| `completed` | `DELIVERED` |
| `cancelled` | `CANCELLED` |
| `refunded` | `RETURNED` |
| `failed` | `CANCELLED` |

## Multi-Account Support

A single integrator instance can manage multiple WooCommerce stores simultaneously. Configure accounts via `config/accounts.yaml` or environment variables (`WOOCOMMERCE_ACCOUNT_0_*`).

## Testing

```bash
# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov --cov-report=html
```

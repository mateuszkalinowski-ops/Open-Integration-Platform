# BaseLinker Integrator v1.0.0

Pinquark Integration Platform connector for **BaseLinker** — a multi-channel e-commerce management platform used for order management, product catalog synchronization, stock levels, and courier shipments.

## Features

- **Order management**: fetch, search, and update order statuses
- **Product catalog**: read product data from BaseLinker inventories
- **Stock synchronization**: bulk update stock levels (up to 1000 products per request)
- **Parcel management**: register shipments manually (courier code + tracking number)
- **Journal-based scraping**: background poller uses `getJournalList` for efficient change detection
- **Multi-account**: supports multiple BaseLinker accounts simultaneously
- **Kafka integration**: optional event streaming for orders and products

## Authentication

BaseLinker uses a **static API token** passed in the `X-BLToken` HTTP header.

Generate a token in the BaseLinker panel: **Account & other → My account → API**.

All requests go to a single POST endpoint: `https://api.baselinker.com/connector.php`.

## API Design

Unlike RESTful APIs, BaseLinker uses a method-based dispatch:

```
POST https://api.baselinker.com/connector.php
Headers: X-BLToken: <token>
Body: method=getOrders&parameters={"date_confirmed_from": 1708000000}
```

Rate limit: **100 requests per minute**.

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BASELINKER_API_TOKEN` | — | API token from BaseLinker panel |
| `BASELINKER_SCRAPING_ENABLED` | `true` | Enable background order polling |
| `BASELINKER_SCRAPING_INTERVAL_SECONDS` | `120` | Polling interval |
| `KAFKA_ENABLED` | `false` | Enable Kafka event publishing |
| `DATABASE_URL` | `sqlite:///...` | State persistence database |

### Account Configuration (accounts.yaml)

```yaml
accounts:
  - name: default
    api_token: "${BASELINKER_API_TOKEN}"
    inventory_id: 1         # BaseLinker catalog ID
    warehouse_id: 1         # Warehouse ID for stock operations
    environment: production
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/readiness` | Full readiness check |
| GET | `/accounts` | List configured accounts |
| POST | `/accounts` | Add a new account |
| DELETE | `/accounts/{name}` | Remove an account |
| GET | `/orders?account_name=` | List orders |
| GET | `/orders/{id}?account_name=` | Get single order |
| PUT | `/orders/{id}/status?account_name=` | Update order status |
| POST | `/stock/sync?account_name=` | Sync stock levels |
| GET | `/products/{id}?account_name=` | Get product data |
| POST | `/parcels?account_name=` | Register a shipment |

## Order Status Mapping

BaseLinker uses **custom statuses** configured per account. The integrator maps them to unified statuses by keyword matching on the status name:

| BaseLinker status name keywords | Unified status |
|---|---|
| nowe, new | NEW |
| w realizacji, processing, kompletowanie | PROCESSING |
| gotowe, do wysylki, ready | READY_FOR_SHIPMENT |
| wyslane, shipped, nadane | SHIPPED |
| dostarczone, delivered, zrealizowane | DELIVERED |
| anulowane, cancelled | CANCELLED |
| zwrot, return | RETURNED |

## Running Locally

```bash
# Start the integrator
docker compose up baselinker-integrator

# Development mode with hot reload
docker compose --profile dev up baselinker-integrator-dev

# Run tests
docker compose --profile test up tests
```

## Architecture

```
BaseLinker API (connector.php)
      ↕ X-BLToken / POST
┌─────────────────────────────┐
│   BaseLinker Integrator     │
│  ┌───────────────────────┐  │
│  │ BaseLinkerClient       │  │  ← single POST endpoint, method dispatch
│  │ BaseLinkerIntegration  │  │  ← EcommerceIntegration interface
│  │ BaseLinkerMapper       │  │  ← BL ↔ unified schema conversion
│  │ BaseLinkerScraper      │  │  ← getJournalList-based change detection
│  └───────────────────────┘  │
│           ↕                 │
│  SQLite (state) / Kafka     │
└─────────────────────────────┘
```

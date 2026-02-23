# IdoSell Integrator v1.0.0

Open Integration Platform by Pinquark.com connector for **IdoSell** (formerly IAI-Shop), a major Polish e-commerce SaaS platform.

## Capabilities

| Capability | Description |
|---|---|
| `fetch_orders` | Search and list orders with date/status filters |
| `get_order` | Fetch single order by serial number or ID |
| `update_order_status` | Change order status in IdoSell |
| `sync_stock` | Update product stock quantities |
| `get_product` | Fetch single product details |
| `sync_products` | Update product data (code, etc.) |
| `create_parcel` | Create shipping packages with tracking numbers |

## IdoSell API

- **API Version**: Admin REST API v6 (default) and v7 supported
- **Documentation**: https://idosell.readme.io/reference

### Authentication Modes

| Mode | Auth method | URL pattern | Credentials |
|---|---|---|---|
| `api_key` (default) | `X-API-KEY` header | `/api/admin/{version}/` | API key from admin panel |
| `legacy` | SHA-1 daily key in request body | `/admin/{version}/` | Login + password (compat with Java impl) |

**Legacy SHA-1 algorithm** (ported from Java `IdoAuth.java`):
```
key = sha1(YYYYMMDD + sha1(password))
```
The key regenerates daily at midnight.

## Quick Start

### Option A: Modern API key auth (recommended)

1. In your IdoSell admin panel: **Administration → API → Access Keys for Admin API**
2. Configure:

```yaml
accounts:
  - name: my-shop
    shop_url: "https://client12345.idosell.com"
    api_key: "your_api_key"
    auth_mode: "api_key"
    api_version: "v6"
    default_stock_id: 1
```

### Option B: Legacy SHA-1 auth (Java-compatible)

Use login/password with SHA-1 daily key generation (same as Java `IdoAuth.java`):

```yaml
accounts:
  - name: my-shop
    shop_url: "https://client12345.idosell.com"
    login: "your_login"
    password: "your_password"
    auth_mode: "legacy"
    api_version: "v7"
    default_stock_id: 1
```

### Run

```bash
cp .env.example .env
```

### 3. Run

```bash
# Local development
docker compose --profile dev up

# Production
docker compose up -d
```

### 4. Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check |
| `/readiness` | GET | Readiness check |
| `/accounts` | GET | List configured accounts |
| `/accounts` | POST | Add new account |
| `/auth/{name}/validate` | POST | Validate API key |
| `/orders` | GET | List orders (with filters) |
| `/orders/{id}` | GET | Get single order |
| `/orders/{id}/status` | PUT | Update order status |
| `/stock/sync` | POST | Sync stock levels |
| `/products/{id}` | GET | Get product |
| `/parcels` | POST | Create parcel |

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `IDOSELL_LOG_LEVEL` | `INFO` | Log level |
| `IDOSELL_SCRAPING_ENABLED` | `true` | Enable order polling |
| `IDOSELL_SCRAPING_INTERVAL_SECONDS` | `120` | Polling interval |
| `KAFKA_ENABLED` | `false` | Publish to Kafka |
| `DATABASE_URL` | `sqlite:///...` | State persistence |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Pinquark       │◀───▶│  IdoSell         │◀───▶│  IdoSell        │
│  Platform       │     │  Integrator      │     │  Admin API      │
│  (API Gateway)  │     │  (FastAPI :8000)  │     │  (REST v6/v7)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                        ┌─────┴─────┐
                        │  SQLite   │
                        │  (state)  │
                        └───────────┘
```

## Rate Limits

IdoSell uses monthly quotas (100k–1M depending on plan), not per-second throttling. The integrator uses 120-second polling intervals by default to stay within limits.

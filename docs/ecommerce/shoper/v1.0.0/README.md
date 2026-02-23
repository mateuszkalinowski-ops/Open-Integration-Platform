# Shoper Integrator v1.0.0

E-commerce connector for the Shoper platform — synchronization of orders, products, users, and stock levels.

## Requirements

- Python 3.12+
- Docker (optional)
- Account in Shoper admin panel with REST API access

## Configuration

### Environment variables

| Variable | Required | Default | Description |
|---------|----------|----------|------|
| `SHOPER_LOG_LEVEL` | No | `INFO` | Log level |
| `DATABASE_URL` | No | Local SQLite | Database connection string |
| `DATABASE_ENCRYPTION_KEY` | No | — | AES-256-GCM key (base64, 32 bytes) |
| `KAFKA_ENABLED` | No | `false` | Publish to Kafka |
| `KAFKA_BOOTSTRAP_SERVERS` | No | `kafka:9092` | Kafka broker addresses |
| `SHOPER_SCRAPING_ENABLED` | No | `true` | Automatic polling |
| `SHOPER_SCRAPING_INTERVAL_SECONDS` | No | `300` | Scraping interval (seconds) |

### Account configuration

Shoper accounts are configured in `config/accounts.yaml`:

```yaml
accounts:
  - name: moj-sklep
    shop_url: "https://mojsklep.shoparena.pl"
    login: "admin"
    password: "${SHOPER_PASSWORD}"
    language_id: "pl_PL"
    environment: production
```

Alternatively via environment variables:

```bash
SHOPER_ACCOUNT_0_NAME=moj-sklep
SHOPER_ACCOUNT_0_SHOP_URL=https://mojsklep.shoparena.pl
SHOPER_ACCOUNT_0_LOGIN=admin
SHOPER_ACCOUNT_0_PASSWORD=secret
SHOPER_ACCOUNT_0_LANGUAGE_ID=pl_PL
```

## Running

### Docker

```bash
cp .env.example .env
# Fill in the data in .env and config/accounts.yaml
docker compose up -d
```

### Development

```bash
docker compose --profile dev up -d
```

### Tests

```bash
docker compose --profile test up --abort-on-container-exit
```

Or locally:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|------|
| `GET` | `/health` | Liveness check |
| `GET` | `/readiness` | Readiness check |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/auth/{account}/status` | Authentication status |
| `GET` | `/accounts` | List of configured accounts |
| `POST` | `/accounts` | Add a new account |
| `DELETE` | `/accounts/{name}` | Delete an account |
| `GET` | `/orders` | List of orders |
| `GET` | `/orders/{id}` | Order details |
| `PUT` | `/orders/{id}/status` | Update status |
| `POST` | `/stock/sync` | Stock synchronization |
| `GET` | `/products/{id}` | Product details |
| `POST` | `/parcels` | Create a parcel |
| `PUT` | `/parcels/{order_id}` | Update a parcel |

## Shoper Authentication

Shoper API uses Basic Auth to obtain a Bearer token:

1. POST to `{shop_url}/webapi/rest/auth` with the header `Authorization: Basic base64(login:password)`
2. Response: `{"access_token": "...", "expires_in": 3600}`
3. Subsequent requests: `Authorization: Bearer {access_token}`
4. Token is automatically refreshed before expiration

## Scraping

The scraper fetches new data from Shoper at configurable intervals:

- **Orders**: filtered by `status_date`, order products fetched via bulk API
- **Products**: filtered by `add_date`
- **Users**: filtered by `date_add`, active only

Scraper state (last timestamp) is persisted in the database, so after a restart it continues from where it left off.

## Kafka Topics

| Topic | Direction | Description |
|-------|----------|------|
| `shoper.output.ecommerce.orders.save` | Out | Orders from Shoper |
| `shoper.output.ecommerce.products.save` | Out | Products from Shoper |
| `shoper.output.ecommerce.users.save` | Out | Users from Shoper |

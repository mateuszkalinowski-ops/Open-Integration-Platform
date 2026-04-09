# Connector Configuration — Open Integration Platform by Pinquark.com

Documentation of configuration parameters for all available connectors.
Credentials are stored in an encrypted vault (AES-256-GCM) and managed via the platform REST API or dashboard.

> **Note**: This file is referenced from [`AGENTS.md`](../AGENTS.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`STANDARDS.md`](STANDARDS.md), and [`CONNECTOR-DEVELOPMENT.md`](CONNECTOR-DEVELOPMENT.md). Update it whenever a connector is added or modified.

## Table of Contents

1. [Connector Overview](#connector-overview)
2. [Couriers](#1-couriers)
3. [E-commerce](#2-e-commerce)
4. [WMS](#3-wms)
5. [ERP](#4-erp)
6. [Other](#5-other)
7. [AI](#6-ai)
8. [Credential Management via API](#7-credential-management-via-api)

---

## Connector Overview

The platform supports optional runtime schema discovery for connector actions. Static `event_fields`, `action_fields`, and `output_fields` from `connector.yaml` remain the default source of truth, while SDK-based connectors can additionally expose `GET /schema/{action}` for richer dynamic schemas. The platform merges both sources through `GET /api/v1/connectors/{name}/schema/{action}`.

| # | Connector | Category | Version | Protocol | Required Parameters |
|---|----------|-----------|--------|----------|-------------------|
| 1 | InPost | Courier | v3.0.0 | REST | `organization_id`, `access_token` |
| 2 | DHL Parcel Poland | Courier | v1.4.0 | SOAP (WSDL) | `username`, `password` |
| 3 | DHL Express | Courier | v3.2.0 | REST | `api_key`, `api_secret` |
| 4 | DPD Poland | Courier | v2024-04 | REST | `login`, `password`, `master_fid` |
| 5 | GLS | Courier | v1.0.0 | REST | `username`, `password` |
| 6 | FedEx | Courier | v1.0.0 | REST (OAuth2) | `client_id`, `client_secret` |
| 7 | FedEx Poland | Courier | v1.0.0 | REST | `api_key`, `client_id` |
| 8 | UPS | Courier | v1.0.0 | REST (OAuth2) | `client_id`, `client_secret`, `account_number` |
| 9 | Poczta Polska | Courier | v17.0.0 | SOAP (WSDL) | `username`, `password` |
| 10 | Orlen Paczka | Courier | v1.0.0 | REST | `partner_id`, `partner_key` |
| 11 | Packeta | Courier | v6.3.0 | REST | `api_password` |
| 12 | DB Schenker | Courier | v1.0.0 | REST | `username`, `password` |
| 13 | SUUS | Courier | v1.0.0 | SOAP (WSDL) | `username`, `password` |
| 14 | Paxy | Courier | v1.0.0 | REST | `api_key` |
| 15 | SellAsist | Courier | v1.90.7 | REST | `api_key` |
| 16 | Allegro | E-commerce | v2025 | REST (OAuth2) | `client_id`, `client_secret` |
| 17 | Shoper | E-commerce | v1.0.0 | REST (OAuth2/Basic) | `shop_url`, `login`, `password` |
| 18 | Shopify | E-commerce | v2024-07 | REST (Access Token) | `shop_url`, `access_token` |
| 19 | Pinquark WMS | WMS | v1.0.0 | REST (JWT) | `api_url`, `username`, `password` |
| 20 | Email Client | Other | v1.0.0 | IMAP/SMTP | `imap_host`, `smtp_host`, `email_address`, `password`, (`username`) |
| 21 | SkanujFakture | Other | v1.0.0 | REST (Basic Auth) | `login`, `password` |
| 22 | IdoSell | E-commerce | v6.0.0 | REST (API Key / SHA-1 legacy) | `shop_url`, `api_key` or `login`+`password` |
| 23 | BaseLinker | E-commerce | v1.0.0 | REST (API Token) | `api_token` |
| 24 | Raben Group | Courier | v1.0.0 | REST (JWT) | `username`, `password` |
| 25 | WooCommerce | E-commerce | v1.0.0 | REST (API Key / OAuth 1.0a) | `store_url`, `consumer_key`, `consumer_secret` |
| 26 | Slack | Other | v1.0.0 | REST (Bot Token) | `bot_token` |
| 27 | BulkGate | Other | v2.0.0 | REST (API Token) | `application_id`, `application_token` |
| 28 | Amazon | E-commerce | v2024-11-01 | REST (OAuth2 / LWA) | `client_id`, `client_secret`, `refresh_token`, `marketplace_id` |
| 29 | Geis | Courier | v1.0.0 | SOAP (WSDL) | `customer_code`, `password` |
| 30 | AI Agent | AI | v1.0.0 | REST (Google Gemini) | `gemini_api_key` |
| 31 | Apilo | E-commerce | v2.0.0 | REST (OAuth2 / Basic) | `client_id`, `client_secret`, `authorization_code` |
| 32 | FX Couriers | Courier | v1.0.0 | REST (Bearer Token) | `api_token` |
| 33 | FTP / SFTP | Other | v1.0.0 | FTP (RFC 959) / SFTP (SSH) | `host`, `protocol` |
| 34 | InsERT Nexo (Subiekt) | ERP | v1.0.0 | .NET SDK (pythonnet) + REST | `sql_server`, `sql_database`, `nexo_operator_login`, `nexo_operator_password` |
| 35 | Symfonia ERP (Handel & FK) | ERP | v1.0.0 | REST/JSON (WebAPI) | `webapi_url`, `application_guid` |
| 37 | Amazon S3 | Other | v1.0.0 | REST (AWS S3 API) | `aws_access_key_id`, `aws_secret_access_key` |
| 38 | KSeF | Other | v1.0.0 | REST (JWT + AES-256-CBC) | `nip`, `ksef_token` |

---

## Standardized Rate Comparison (rates.get)

All major courier connectors expose a `rates.get` action that returns shipping rates in a standardized format. This enables the **shipping price comparison workflow** via the Workflow Engine's `parallel` + `aggregate` nodes.

### Standardized Response Format

```json
{
  "products": [
    {
      "name": "Service Name",
      "price": 15.99,
      "currency": "PLN",
      "delivery_days": 2,
      "delivery_date": "",
      "attributes": {
        "source": "connector-name",
        "service": "service_code"
      }
    }
  ],
  "source": "connector-name",
  "raw": {}
}
```

### Standardized Request Payload

```json
{
  "senderPostalCode": "00-001",
  "senderCountryCode": "PL",
  "receiverPostalCode": "30-001",
  "receiverCountryCode": "PL",
  "weight": 5.0,
  "length": 30,
  "width": 20,
  "height": 15
}
```

### Connector Rate Sources

| Connector | Rate Method | Notes |
|-----------|-----------|-------|
| DHL Express | **Live API** (`POST /rates/standardized`) | Real-time pricing from MyDHL Express Rating API |
| UPS | **Live API** (`POST /rates`) | Real-time pricing from UPS Rating API (Shop mode) |
| FedEx | **Live API** (`POST /rates`) | Real-time pricing from FedEx Rate API |
| InPost | Pricing table (`POST /rates`) | Estimated from published weight/size tiers |
| DHL Parcel Poland | Pricing table (`POST /rates`) | Estimated from published weight/size tiers |
| DPD | Pricing table (`POST /rates`) | Estimated from published weight/size tiers |
| GLS | Pricing table (`POST /rates`) | Estimated from published weight/size tiers |

Connectors with "Pricing table" method return approximate baseline rates. Actual contract prices may differ — override via per-tenant field mappings or a custom `transform` node in the workflow.

---

## 1. Couriers

### InPost (v3.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `organization_id` | Yes | Organization ID in InPost |
| `access_token` | Yes | ShipX API access token |
| `sandbox_mode` | No | Test mode (default: false) |
| `default_currency` | No | Default currency (default: PLN) |

Environment variables:
```bash
APP_ENV=production
INPOST_INT_2025_API_URL=https://api.inpost-group.com
INPOST_INT_2025_SANDBOX_API_URL=https://stage-api.inpost-group.com
```

Versions: v1.0.0, v2.0.0, v3.0.0. Changes in v3.0.0: added `default_currency` parameter.

---

### DHL Parcel Poland (v1.4.0)

| Parameter | Required | Description |
|----------|----------|------|
| `username` | Yes | DHL24 login |
| `password` | Yes | DHL24 password |
| `account_number` | No | DHL account number |
| `sap_number` | No | SAP number |
| `sandbox_mode` | No | Test mode |

Environment variables:
```bash
SOAP_TIMEOUT=30
SOAP_OPERATION_TIMEOUT=600
DHL_PROD_WSDL=wsdl/dhl_42.wsdl
DHL_SANDBOX_WSDL=wsdl/sandbox_dhl_42.wsdl
DHL_PROD_PARCELSHOP_URL=https://dhl24.com.pl/servicepoint
DHL_SANDBOX_PARCELSHOP_URL=https://sandbox.dhl24.com.pl/servicepoint
```

Protocol: SOAP (WSDL).

---

### DHL Express (v3.2.0)

| Parameter | Required | Description |
|----------|----------|------|
| `api_key` | Yes | MyDHL Express API key |
| `api_secret` | Yes | API secret |
| `sandbox_mode` | No | Test mode |

Protocol: REST. Retry: exponential backoff (tenacity, max 3 attempts).

---

### DPD Poland (v2024-04)

| Parameter | Required | Description |
|----------|----------|------|
| `login` | Yes | DPD login |
| `password` | Yes | Password |
| `master_fid` | Yes | Customer Master FID |
| `sandbox_mode` | No | Test mode |

---

### GLS (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `username` | Yes | GLS login |
| `password` | Yes | GLS password |
| `sandbox_mode` | No | Test mode |

---

### FedEx (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `client_id` | Yes | OAuth2 Client ID |
| `client_secret` | Yes | OAuth2 Client Secret |
| `sandbox_mode` | No | Test mode |

---

### FedEx Poland (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `api_key` | Yes | FedEx PL API key |
| `client_id` | Yes | Client ID |
| `courier_number` | No | Courier number |
| `account_number` | No | Account number |
| `sandbox_mode` | No | Test mode |

---

### UPS (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `client_id` | Yes | OAuth2 Client ID |
| `client_secret` | Yes | OAuth2 Client Secret |
| `account_number` | Yes | UPS account number |
| `sandbox_mode` | No | Test mode |

---

### Poczta Polska (v17.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `username` | Yes | e-Nadawca login |
| `password` | Yes | Password |
| `tracking_wsdl` | No | Tracking WSDL URL |
| `posting_wsdl` | No | Posting WSDL URL |
| `sandbox_mode` | No | Test mode |

Protocol: SOAP (WSDL).

---

### Orlen Paczka (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `partner_id` | Yes | Partner ID |
| `partner_key` | Yes | Partner key |
| `sandbox_mode` | No | Test mode |

---

### Packeta / Zasilkovna (v6.3.0)

| Parameter | Required | Description |
|----------|----------|------|
| `api_password` | Yes | API password |
| `eshop` | No | Shop ID |
| `sandbox_mode` | No | Test mode |

---

### DB Schenker (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `username` | Yes | Login |
| `password` | Yes | Password |
| `sandbox_mode` | No | Test mode |

---

### SUUS (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `username` | Yes | Login |
| `password` | Yes | Password |
| `wsdl_url` | No | Custom WSDL URL |
| `sandbox_mode` | No | Test mode |

Protocol: SOAP (WSDL).

---

### Paxy (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `api_key` | Yes | API key |
| `sandbox_mode` | No | Test mode |

---

### SellAsist (v1.90.7)

| Parameter | Required | Description |
|----------|----------|------|
| `api_key` | Yes | API key |
| `sandbox_mode` | No | Test mode |

---

### Raben Group (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `username` | Yes | myRaben login / API username |
| `password` | Yes | myRaben password / API password |
| `customer_number` | No | Raben customer number |
| `sandbox_mode` | No | Test mode |
| `default_service_type` | No | Default service type (default: `cargo_classic`) |

Environment variables:
```bash
REST_TIMEOUT=30
RABEN_API_URL=https://myraben.com/api/v1
RABEN_SANDBOX_API_URL=https://sandbox.myraben.com/api/v1
```

Service types: `cargo_classic` (24/48h), `cargo_premium`, `cargo_premium_08`, `cargo_premium_10`, `cargo_premium_12`, `cargo_premium_16`.

Features:
- Transport order creation (myOrder) for LTL/FTL freight
- Shipment tracking with full event history (Track & Trace)
- ETA (Estimated Time of Arrival) with +/- 2h window
- Photo Confirming Delivery (PCD) retrieval
- Shipping label generation (PDF/ZPL)
- Complaint/claim submission (myClaim)
- Additional services: tail lift, email notifications, COD
- JWT-based authentication with automatic token refresh

Protocol: REST (JWT Authentication).

---

### Geis (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `customer_code` | Yes | Geis customer code |
| `password` | Yes | Geis API password |
| `default_language` | No | Default language (default: `PL`) |
| `sandbox_mode` | No | Use sandbox environment (default: `false`) |

Environment variables:
```bash
SOAP_TIMEOUT=30
GEIS_API_URL=https://geis-api-url/service.svc?wsdl
```

Features:
- Pallet and parcel shipment creation (domestic and international)
- Shipping label generation
- Shipment status tracking
- Shipment cancellation
- Shipment details retrieval

Protocol: SOAP (WSDL).

---

### FX Couriers (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `api_token` | Yes | Bearer API token (provided by FX Couriers sales representative) |
| `company_id` | No | Company ID for multi-company accounts |

Environment variables:
```bash
REST_TIMEOUT=30
FXCOURIERS_API_URL=https://fxcouriers.kuriersystem.pl/api/rest
```

Features:
- Transport order creation and management
- Shipping label generation (PDF)
- Shipment pickup scheduling with time windows
- Order tracking and status monitoring
- Service and package configuration retrieval
- Company info management
- Additional services: insurance (UBEZPIECZENIE), COD (POBRANIE), fuel surcharge (OPLATA_PALIWOWA)
- Bearer token authentication (static token, no OAuth flow)

Protocol: REST (Bearer Token Authentication).

---

## 2. E-commerce

### Allegro (v2025)

| Parameter | Required | Description |
|----------|----------|------|
| `client_id` | Yes | OAuth2 Client ID from Allegro Developer |
| `client_secret` | Yes | OAuth2 Client Secret |
| `sandbox_mode` | No | Use allegrosandbox.pl instead of allegro.pl |
| `api_url` | No | Custom API URL (default: `https://api.allegro.pl`) |
| `auth_url` | No | Custom Auth URL (default: `https://allegro.pl/auth/oauth`) |

Environment variables:
```bash
KAFKA_ENABLED=true                      # Publish orders to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ALLEGRO_SCRAPING_ENABLED=true           # Order polling
ALLEGRO_SCRAPING_INTERVAL_SECONDS=60    # How often to check for orders (seconds)
```

Allegro account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: sklep-glowny
    client_id: "xxx"
    client_secret: "yyy"
    api_url: "https://api.allegro.pl"
    auth_url: "https://allegro.pl/auth/oauth"
    environment: production
```

Features:
- Automatic order polling (every 60s by default)
- Publishing orders to Kafka (`allegro.output.ecommerce.orders.save`)
- Event deduplication per checkout form
- Fetching EAN/SKU from offers
- **Product search** via `/offers/listing` endpoint (search by phrase, category, sort by price)
- Rate limit handling (respects `Retry-After` header)
- OAuth2 token auto-refresh

### Shoper (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `shop_url` | Yes | Shoper shop URL (e.g. `https://myshop.shoparena.pl`) |
| `login` | Yes | Shoper panel administrator login |
| `password` | Yes | Administrator password |
| `language_id` | No | Language ID (default: `pl_PL`) |

Environment variables:
```bash
SHOPER_SCRAPING_ENABLED=true            # Automatic order/product/user polling
SHOPER_SCRAPING_INTERVAL_SECONDS=300    # How often to check for new data (seconds)
SHOPER_SCRAPE_ORDERS=true               # Order scraping
SHOPER_SCRAPE_PRODUCTS=true             # Product scraping
SHOPER_SCRAPE_USERS=true                # User scraping
KAFKA_ENABLED=false                     # Publish to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

Shoper account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: moj-sklep
    shop_url: "https://mojsklep.shoparena.pl"
    login: "admin"
    password: "${SHOPER_PASSWORD}"
    language_id: "pl_PL"
    environment: production
```

Features:
- Automatic order polling (every 300s by default)
- Product and user polling
- Fetching order products via bulk API
- Publishing to Kafka (`shoper.output.ecommerce.orders.save`, `shoper.output.ecommerce.products.save`, `shoper.output.ecommerce.users.save`)
- Order status updates
- Stock level synchronization
- Parcel management (create, update)
- **Product search** via REST API with name filters (`LIKE` on `translations.name`)
- Basic Auth → Bearer token authentication with automatic refresh
- Multi-account Shoper support

Protocol: REST (Basic Auth → Bearer Token).

### Shopify (v2024-07)

| Parameter | Required | Description |
|----------|----------|------|
| `shop_url` | Yes | Shopify store URL (e.g. `my-store.myshopify.com`) |
| `access_token` | Yes | Admin API access token (starts with `shpat_`) |
| `api_version` | No | Shopify API version (default: `2024-07`) |
| `default_location_id` | No | Default location ID for inventory sync |
| `default_carrier` | No | Default shipping carrier name (default: `Kurier`) |

Environment variables:
```bash
SHOPIFY_SCRAPING_ENABLED=true           # Automatic order polling
SHOPIFY_SCRAPING_INTERVAL_SECONDS=60    # How often to check for orders (seconds)
KAFKA_ENABLED=false                     # Publish orders to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

Shopify account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: my-store
    shop_url: "my-store.myshopify.com"
    access_token: "shpat_xxxxx"
    api_version: "2024-07"
    default_location_id: "12345678"
    default_carrier: "Kurier"
```

Features:
- Automatic order polling (every 60s by default)
- Publishing orders to Kafka (`shopify.output.ecommerce.orders.save`)
- Incremental order fetching via `since_id`
- Product sync (create/update) via REST API
- Inventory level sync via Inventory API
- Fulfillment creation via Fulfillment Orders API (2023-01+)
- Tracking number updates
- **Product search** by title via Admin API (`GET /products.json?title=...`)
- Rate limit handling (respects `X-Shopify-Shop-Api-Call-Limit` header)
- Multi-store support (multiple Shopify accounts)
- Access token validation

Protocol: REST (Admin API Access Token).

### IdoSell (v6.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `shop_url` | Yes | IdoSell panel URL (e.g. `https://client12345.idosell.com`) |
| `api_key` | Conditional | Admin API key — required for `api_key` auth mode |
| `login` | Conditional | Login — required for `legacy` auth mode |
| `password` | Conditional | Password — required for `legacy` auth mode |
| `auth_mode` | No | `api_key` (default) or `legacy` (SHA-1, Java-compatible) |
| `api_version` | No | API version: `v6` (default) or `v7` |
| `default_stock_id` | No | Default warehouse/stock ID (default: `1`) |
| `default_currency` | No | Default currency (default: `PLN`) |

**Authentication modes:**

| Mode | URL pattern | Auth mechanism |
|---|---|---|
| `api_key` (default) | `/api/admin/{version}/` | `X-API-KEY` header (static key) |
| `legacy` | `/admin/{version}/` | SHA-1 daily key in request body: `sha1(YYYYMMDD + sha1(password))` |

The `legacy` mode is compatible with the existing Java implementation (`IdoAuth.java`).

Environment variables:
```bash
IDOSELL_SCRAPING_ENABLED=true           # Automatic order/product polling
IDOSELL_SCRAPING_INTERVAL_SECONDS=120   # How often to check for new data (seconds)
KAFKA_ENABLED=false                     # Publish to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

IdoSell account configuration in `config/accounts.yaml`:
```yaml
accounts:
  # Modern auth (recommended for new setups):
  - name: my-shop
    shop_url: "https://client12345.idosell.com"
    api_key: "${IDOSELL_API_KEY}"
    auth_mode: "api_key"
    api_version: "v6"
    default_stock_id: 1
    default_currency: "PLN"

  # Legacy auth (compatible with Java implementation):
  - name: legacy-shop
    shop_url: "https://client12345.idosell.com"
    login: "${IDOSELL_LOGIN}"
    password: "${IDOSELL_PASSWORD}"
    auth_mode: "legacy"
    api_version: "v7"
    default_stock_id: 1
    default_currency: "PLN"
```

Features:
- Dual auth mode: modern X-API-KEY and legacy SHA-1 (Java-compatible)
- Automatic order polling (every 120s by default)
- Product polling for modifications
- Publishing to Kafka (`idosell.output.ecommerce.orders.save`, `idosell.output.ecommerce.products.save`)
- Order status updates (24 IdoSell statuses mapped to 7 unified statuses)
- Stock quantity synchronization
- Parcel creation with tracking numbers
- Multi-account IdoSell support
- **Product search** via `/products/products/search` endpoint
- 0-based pagination handling

Protocol: REST (API Key header or SHA-1 body auth).

---

### BaseLinker (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `api_token` | Yes | API token from BaseLinker panel (Account → My account → API) |
| `inventory_id` | No | BaseLinker catalog/inventory ID for product operations (default: `0`) |
| `warehouse_id` | No | Warehouse ID for stock operations (default: `0`) |
| `scraping_enabled` | No | Enable background order polling (default: `true`) |
| `scraping_interval_seconds` | No | Polling interval in seconds (default: `120`) |

Environment Variables:

| Variable | Description |
|---|---|
| `BASELINKER_API_TOKEN` | API token |
| `BASELINKER_SCRAPING_ENABLED` | Enable scraping (default: `true`) |
| `BASELINKER_SCRAPING_INTERVAL_SECONDS` | Polling interval (default: `120`) |
| `KAFKA_ENABLED` | Enable Kafka publishing (default: `false`) |

BaseLinker account configuration in `config/accounts.yaml`:

```yaml
accounts:
  - name: default
    api_token: "${BASELINKER_API_TOKEN}"
    inventory_id: 1
    warehouse_id: 1
    environment: production
```

Features:
- Single POST endpoint API (connector.php) with method-based dispatch
- Rate limit handling (100 req/min with automatic backoff)
- Order management with custom status mapping (keyword-based)
- Product catalog sync via BaseLinker inventories
- Bulk stock update (up to 1000 products per request)
- Manual parcel registration (courier code + tracking number)
- Journal-based change detection for efficient scraping
- Multi-account support
- **Product search** via `getInventoryProductsList` + `getInventoryProductsData` with name filtering
- Kafka event streaming for orders and products

Protocol: REST (API Token via X-BLToken header).

---

### WooCommerce (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `store_url` | Yes | WooCommerce store URL (e.g. `https://my-store.example.com`) |
| `consumer_key` | Yes | REST API Consumer Key (starts with `ck_`) |
| `consumer_secret` | Yes | REST API Consumer Secret (starts with `cs_`) |
| `api_version` | No | WooCommerce API version (default: `wc/v3`) |
| `verify_ssl` | No | SSL verification (default: `true`) |

Environment variables:
```bash
WOOCOMMERCE_SCRAPING_ENABLED=true           # Automatic order polling
WOOCOMMERCE_SCRAPING_INTERVAL_SECONDS=60    # How often to check for orders (seconds)
KAFKA_ENABLED=false                         # Publish orders to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

WooCommerce account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: my-store
    store_url: "https://my-store.example.com"
    consumer_key: "ck_xxxxx"
    consumer_secret: "cs_xxxxx"
    api_version: "wc/v3"
    verify_ssl: true
    environment: production
```

Features:
- Automatic order polling (every 60s by default) with `modified_after` incremental fetching
- Publishing orders to Kafka (`output.ecommerce.orders.save`)
- Order status updates (bidirectional status mapping)
- Stock level synchronization by product ID or SKU lookup
- Product sync (create/update)
- API key authentication: Basic Auth (HTTPS) or OAuth 1.0a HMAC-SHA256 (HTTP)
- **Product search** via WooCommerce REST API (`GET /products?search=...`)
- Multi-store support (multiple WooCommerce accounts per instance)
- Rate limit handling (respects `Retry-After` header)

Protocol: REST (API Key / OAuth 1.0a).

---

### Amazon (v2024-11-01)

| Parameter | Required | Description |
|----------|----------|------|
| `client_id` | Yes | LWA application client ID |
| `client_secret` | Yes | LWA application client secret |
| `refresh_token` | Yes | Seller authorization refresh token (does not expire) |
| `marketplace_id` | Yes | Amazon Marketplace ID (e.g. `A1PA6795UKMFR9` for Germany) |
| `region` | No | SP-API region: `na`, `eu`, `fe` (default: `eu`) |
| `sandbox_mode` | No | Use sandbox endpoints (default: false) |

Environment variables:
```bash
AMAZON_LOG_LEVEL=INFO
AMAZON_SCRAPING_ENABLED=true
AMAZON_SCRAPING_INTERVAL_SECONDS=300
```

Amazon account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: my-seller
    client_id: "amzn1.application-oa2-client.xxxx"
    client_secret: "your-client-secret"
    refresh_token: "Atzr|XXXX"
    marketplace_id: "A1PA6795UKMFR9"
    region: "eu"
    sandbox_mode: false
    environment: production
```

Features:
- Order management (fetch, get details, get items, acknowledge, ship, cancel)
- Status updates via Feeds API (POST_ORDER_ACKNOWLEDGEMENT_DATA, POST_ORDER_FULFILLMENT_DATA)
- Product catalog (search by keyword/identifier, get by ASIN)
- Stock synchronization via Feeds API (POST_INVENTORY_AVAILABILITY_DATA)
- Reports API (create, get status, download)
- Feed status tracking
- Background order scraper with configurable interval
- Multi-account support (multiple sellers/marketplaces)
- LWA OAuth2 with automatic token refresh
- All global Amazon marketplaces supported (US, EU, FE regions)

Protocol: REST (Amazon SP-API with LWA OAuth2 authentication).

---

### Apilo (v2.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `client_id` | Yes | OAuth2 Client ID (from Apilo Admin > API) |
| `client_secret` | Yes | OAuth2 Client Secret |
| `authorization_code` | Yes* | Initial authorization code for token exchange |
| `refresh_token` | No | Refresh token (if already obtained; alternative to authorization_code) |
| `base_url` | No | Apilo instance URL (default: `https://app.apilo.com`) |

*Required for initial token exchange; can be omitted if `refresh_token` is provided.

Environment variables:
```bash
APILO_LOG_LEVEL=INFO
APILO_SCRAPING_ENABLED=true
APILO_SCRAPING_INTERVAL_SECONDS=300
APILO_RATE_LIMIT_RPM=150
```

Apilo account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: my-store
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    authorization_code: "your-auth-code"
    base_url: "https://app.apilo.com"
    environment: production
```

Features:
- Order management (list, get, create, update status, add payments/notes/tags/shipments/documents)
- Product catalog (list, search, get, create, update, patch, delete)
- Shipment management (create via Shipping API, track, confirm pickup)
- Finance document management (list, create, delete accounting documents)
- Category and attribute management
- Media upload (PDF, images)
- Background order scraper with configurable polling interval
- Multi-account support (via YAML or environment variables)
- OAuth2 with automatic token refresh (access tokens valid 21 days)
- Rate limiting compliance (150 req/min)
- Reference maps (statuses, payment types, carriers, platforms, tags)

Protocol: REST (Apilo REST API v2 with OAuth2 Basic Auth token exchange).

---

## 3. WMS

### Pinquark WMS (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `api_url` | Yes | WMS API URL (e.g. `https://wms.example.com`) |
| `username` | Yes | WMS login |
| `password` | Yes | WMS password |

Features:
- JWT authentication with automatic token refresh
- Feedback-aware write: polling for processing confirmation from `/feedbacks`
- Bulk operations: articles, documents, items, contractors, batches
- Credential validation via Platform API (`POST /credentials/pinquark-wms/validate`)

---

## 4. ERP

### InsERT Nexo / Subiekt (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `sql_server` | Yes | SQL Server hostname or IP (on-premise) |
| `sql_database` | Yes | Nexo database name |
| `nexo_operator_login` | Yes | Nexo operator login |
| `nexo_operator_password` | Yes | Nexo operator password |
| `cloud_url` | No | Cloud connector URL (for hybrid mode) |
| `sync_interval_seconds` | No | Sync interval in seconds (default: 300) |

**Deployment model**: Hybrid (on-premise agent + cloud connector)

The InsERT Nexo connector requires an **on-premise agent** (`onpremise/nexo-agent/`) running in the client's network with direct access to the SQL Server database and the Nexo .NET SDK (via Python.NET). The agent syncs data with the cloud connector over HTTPS.

Environment variables:
```bash
NEXO_CONNECTOR_LOG_LEVEL=INFO
NEXO_SQL_SERVER=localhost\\NEXO
NEXO_SQL_DATABASE=NexoDB
NEXO_OPERATOR_LOGIN=operator
NEXO_OPERATOR_PASSWORD=${NEXO_PASSWORD}
```

Features:
- Contractor CRUD (list, get, create, update, delete)
- Product catalog CRUD (list, get, create, update, delete)
- Sales document creation (invoices, receipts) and retrieval
- Warehouse document creation (PZ, WZ, MM) and retrieval
- Order management (create, update, list, get)
- Stock level queries (all products or by product ID)
- Hybrid deployment: on-premise agent communicates with cloud connector
- .NET SDK interop via Python.NET (pythonnet)
- SQLite local queue for offline resilience
- Automatic heartbeat monitoring

Protocol: .NET SDK (pythonnet) + REST (cloud connector).

### Symfonia ERP — Handel & FK (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `webapi_url` | Yes | Symfonia WebAPI URL (e.g. `https://192.168.1.100:8080`) |
| `application_guid` | Yes | Application GUID from Symfonia configurator |
| `device_name` | No | Device name for session identification (default: `pinquark-oip`) |
| `sync_interval_seconds` | No | Polling interval for incremental sync (default: 300) |
| `session_timeout_minutes` | No | Session timeout before renewal (default: 30) |

**Deployment model**: Cloud (direct REST connection to on-premise Symfonia WebAPI)

The Symfonia ERP connector integrates with **Symfonia Handel** (trade, warehouse, sales, purchases) and **Symfonia Finanse i Księgowość** (finance & accounting) modules via the Symfonia WebAPI REST/JSON interface. No on-premise agent required — the connector communicates directly with the WebAPI service.

Environment variables:
```bash
SYMFONIA_CONNECTOR_LOG_LEVEL=INFO
SYMFONIA_CONNECTOR_WEBAPI_URL=https://192.168.1.100:8080
SYMFONIA_CONNECTOR_APPLICATION_GUID=493EB16D-7029-48AA-BB25-8BA7138D763A
SYMFONIA_CONNECTOR_DEVICE_NAME=pinquark-oip
SYMFONIA_CONNECTOR_SESSION_TIMEOUT_MINUTES=30
SYMFONIA_CONNECTOR_SYNC_INTERVAL_SECONDS=300
```

Features:
- Contractor CRUD (list, get, create, update) with HMF and SQL filtering
- Product catalog CRUD (list, get, create, update) with barcode management
- Sales documents (list, get, filter by date/buyer, PDF export, corrections)
- Purchase documents (list, get, filter by date/supplier, PDF export)
- Orders — foreign (ZMO) and own (ZMW) — with date/recipient filtering
- Inventory states (all, by product, by warehouse, change detection)
- Payment operations (KP/KW documents)
- Incremental sync for all entities via `IncrementalSync` endpoints
- Session-based authentication with automatic renewal
- Credential validation via Ping/Alive endpoints

Protocol: REST/JSON (Symfonia WebAPI).

---

## 5. Other

### Email Client (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `imap_host` | Yes | IMAP server address (e.g. `imap.gmail.com`) |
| `smtp_host` | Yes | SMTP server address (e.g. `smtp.gmail.com`) |
| `email_address` | Yes | Account email address |
| `password` | Yes | Password or App Password |
| `username` | No | IMAP/SMTP login if different from email address (default: email_address) |
| `imap_port` | No | IMAP port (default: 993) |
| `smtp_port` | No | SMTP port (default: 587) |
| `use_ssl` | No | SSL/TLS (default: true) |
| `polling_folder` | No | IMAP folder for polling (default: INBOX) |
| `polling_interval_seconds` | No | Polling interval in seconds (default: 60) |

Environment variables:
```bash
EMAIL_POLLING_ENABLED=true                 # Automatic email polling
EMAIL_POLLING_INTERVAL_SECONDS=60          # How often to check for new emails (seconds)
EMAIL_POLLING_FOLDER=INBOX                 # IMAP folder for polling
EMAIL_POLLING_MAX_EMAILS=50                # Max emails per polling cycle
KAFKA_ENABLED=false                        # Publish to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

Email account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: moje-konto
    email_address: "user@example.com"
    username: ""  # optional, if IMAP/SMTP login != email_address
    password: "${EMAIL_PASSWORD}"
    imap_host: "imap.gmail.com"
    imap_port: 993
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    use_ssl: true
    polling_folder: "INBOX"
    environment: production
```

Features:
- Automatic polling for new emails (every 60s by default)
- Sending emails with HTML, attachments, and priority support
- Publishing to Kafka (`email.output.other.emails.received`, `email.output.other.emails.sent`)
- Listing IMAP folders
- Marking as read, deleting emails
- Multi-account email support
- Prometheus metrics for IMAP/SMTP operations

Protocol: IMAP4rev1 (RFC 3501) + SMTP (RFC 5321).

---

### SkanujFakture (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `login` | Yes | SkanujFakture account login (email) |
| `password` | Yes | Account password |
| `api_url` | No | API URL (default: `https://skanujfakture.pl:8443/SFApi`) |
| `company_id` | No | Company ID (auto-detected if not provided) |
| `polling_interval_seconds` | No | Polling interval for new documents (default: 300) |
| `polling_status_filter` | No | Status filter for polling (default: `zeskanowany`) |

Environment variables:
```bash
SF_POLLING_ENABLED=true                    # Automatic document polling
SF_POLLING_INTERVAL_SECONDS=300            # How often to check for new documents (seconds)
SF_POLLING_STATUS_FILTER=zeskanowany       # Status filter
KAFKA_ENABLED=false                        # Publish to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

SkanujFakture account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: moja-firma
    login: "user@example.com"
    password: "${SF_PASSWORD}"
    api_url: "https://skanujfakture.pl:8443/SFApi"
    company_id: 147
    environment: production
```

Features:
- Document upload with automatic OCR (PDF, JPG, PNG)
- Fetching scanned documents with details (contractor, amounts, VAT, line items)
- Document update and deletion
- Document attribute management
- Accounting dictionaries (COST_TYPE, COST_CENTER, ATTRIBUTE)
- KSeF integration — fetching XML/QR, sending FA3 invoices
- Automatic polling for new documents (every 300s by default)
- Publishing to Kafka (`skanujfakture.output.other.documents.scanned`)
- Multi-account SkanujFakture support

Protocol: REST (Basic Authentication).

---

### Slack (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `bot_token` | Yes | Bot User OAuth Token (`xoxb-...`) |
| `app_token` | No | App-Level Token for Socket Mode (`xapp-...`) |
| `default_channel` | No | Default channel for sending messages (default: `general`) |

Environment variables:
```bash
SLACK_POLLING_ENABLED=true                 # Automatic message polling
SLACK_POLLING_INTERVAL_SECONDS=30          # How often to check for new messages (seconds)
KAFKA_ENABLED=false                        # Publish to Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

Slack account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: my-workspace
    bot_token: "xoxb-your-bot-token"
    app_token: "xapp-your-app-token"  # optional
    default_channel: "general"
    environment: production
```

Features:
- Sending messages to channels and threads (Block Kit support)
- Fetching channel message history with time range filtering
- Listing channels (public, private, IM, MPIM)
- File uploads to channels
- Adding emoji reactions to messages
- Automatic polling for new messages (every 30s by default)
- Publishing to Kafka (`slack.output.other.messages.received`)
- Multi-workspace support
- User name resolution with caching
- Prometheus metrics for Slack API operations

Protocol: REST (Slack Web API, Bearer Token authentication).

### BulkGate SMS Gateway (v2.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `application_id` | Yes | BulkGate Application ID |
| `application_token` | Yes | BulkGate Application Token |
| `sender_id` | No | Default sender ID type (default: `gSystem`) |
| `sender_id_value` | No | Default sender ID value |
| `default_country` | No | Default country code (ISO 3166-1 alpha-2) |
| `unicode` | No | Enable Unicode SMS by default (default: `false`) |
| `webhook_url` | No | Delivery report webhook URL |

Environment variables:
```bash
APP_ENV=production
BULKGATE_API_URL=https://portal.bulkgate.com
REST_TIMEOUT=30
```

BulkGate account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: main-sms
    application_id: "12345"
    application_token: "your-token"
    sender_id: "gText"
    sender_id_value: "MyCompany"
    default_country: "CZ"
    unicode: false
    environment: production
```

Features:
- Transactional SMS (single recipient, high priority)
- Promotional/Bulk SMS (multiple recipients)
- Advanced transactional SMS with template variables and multi-channel cascade (SMS → Viber)
- Credit balance checking
- Delivery report webhooks
- Incoming SMS webhooks (replies)
- Sender ID types: system number, short code, text sender, own number, BulkGate profile
- Scheduled sending (ISO 8601 / unix timestamp)
- Unicode SMS support
- Duplicate message prevention
- Coverage: 200+ countries

Protocol: REST (BulkGate HTTP API, Application ID + Token authentication).

---

### FTP / SFTP (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `host` | Yes | Server hostname or IP address |
| `protocol` | Yes | Protocol: `ftp` or `sftp` |
| `port` | No | Port (default: 21 for FTP, 22 for SFTP) |
| `username` | No | Login username |
| `password` | No | Login password |
| `private_key` | No | SSH private key in PEM format (SFTP only) |
| `passive_mode` | No | Use passive mode for FTP (default: `true`) |
| `base_path` | No | Base directory on server (default: `/`) |
| `polling_enabled` | No | Enable background polling for new files (default: `false`) |
| `polling_path` | No | Directory to poll for new files (default: `/`) |
| `polling_interval_seconds` | No | Polling interval in seconds (default: `300`) |

Environment variables:
```bash
FTP_LOG_LEVEL=INFO
FTP_POLLING_ENABLED=false
FTP_POLLING_INTERVAL_SECONDS=300
FTP_POLLING_PATH=/
FTP_CONNECT_TIMEOUT=15.0
FTP_OPERATION_TIMEOUT=60.0
KAFKA_ENABLED=false
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

FTP/SFTP account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: my-sftp-server
    host: sftp.example.com
    protocol: sftp
    port: 22
    username: "${SFTP_USERNAME}"
    password: "${SFTP_PASSWORD}"
    base_path: /data/exchange
    environment: production

  - name: legacy-ftp
    host: ftp.legacy.example.com
    protocol: ftp
    port: 21
    username: "${FTP_USERNAME}"
    password: "${FTP_PASSWORD}"
    passive_mode: true
    base_path: /
    environment: production
```

Features:
- Dual protocol: FTP (aioftp) and SFTP (asyncssh) via unified API
- File operations: upload (base64), download (base64), list, delete, move/rename
- Directory operations: create, list (filtered)
- Glob pattern filtering for file listing (e.g., `*.csv`, `report_*`)
- Background polling for new files with SQLite state persistence
- Publishing to Kafka (`ftp-sftp.output.other.files.new`, `ftp-sftp.output.other.files.uploaded`, `ftp-sftp.output.other.files.deleted`)
- Platform event notification for Flow Engine integration
- Multi-account FTP/SFTP support
- Connection testing / validation
- Base path configuration per account
- Prometheus metrics for file operations

Protocol: FTP (RFC 959) / SFTP (SSH File Transfer Protocol).

---

### Amazon S3 (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `aws_access_key_id` | Yes | AWS Access Key ID |
| `aws_secret_access_key` | Yes | AWS Secret Access Key |
| `region` | No | AWS region (default: `us-east-1`) |
| `endpoint_url` | No | Custom S3 endpoint URL for S3-compatible storage (MinIO, Wasabi, etc.) |
| `default_bucket` | No | Default bucket name |
| `use_path_style` | No | Use path-style addressing (default: `false`, required for MinIO) |
| `polling_enabled` | No | Enable background polling for new objects (default: `false`) |
| `polling_bucket` | No | Bucket to poll for new objects |
| `polling_prefix` | No | Key prefix to poll (default: empty) |
| `polling_interval_seconds` | No | Polling interval in seconds (default: `300`) |

Environment variables:
```bash
S3_LOG_LEVEL=INFO
S3_POLLING_ENABLED=false
S3_POLLING_INTERVAL_SECONDS=300
S3_POLLING_BUCKET=
S3_POLLING_PREFIX=
S3_CONNECT_TIMEOUT=15.0
S3_OPERATION_TIMEOUT=60.0
KAFKA_ENABLED=false
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

S3 account configuration in `config/accounts.yaml`:
```yaml
accounts:
  # AWS S3
  - name: production-aws
    aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
    aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
    region: eu-central-1
    default_bucket: my-data-bucket
    environment: production

  # MinIO (S3-compatible)
  - name: local-minio
    aws_access_key_id: minioadmin
    aws_secret_access_key: minioadmin
    region: us-east-1
    endpoint_url: http://minio:9000
    use_path_style: true
    default_bucket: test-bucket
    environment: development
```

Features:
- Object operations: upload (base64), download (base64), list, delete, copy
- Bucket management: list, create, delete
- Pre-signed URL generation (GET/PUT) with configurable expiration
- Background polling for new objects with SQLite state persistence
- Publishing to Kafka (`s3.output.other.objects.new`, `s3.output.other.objects.uploaded`, `s3.output.other.objects.deleted`)
- Platform event notification for Flow Engine integration
- Multi-account S3 support
- S3-compatible storage: MinIO, Wasabi, DigitalOcean Spaces, Backblaze B2, LocalStack
- Input validation for bucket names and object keys
- Connection testing / validation
- Prometheus metrics for S3 operations

Protocol: REST (Amazon S3 API / AWS Signature V4 authentication).

---

### KSeF (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `nip` | Yes | NIP (tax identification number) of the entity |
| `ksef_token` | Yes | KSeF authorization token |
| `environment` | No | API environment: `test`, `demo`, `production` (default: `demo`) |
| `certificate_path` | No | Path to qualified certificate for XAdES auth (alternative to token) |
| `certificate_password` | No | Certificate password |

Environment variables:
```bash
KSEF_LOG_LEVEL=INFO
KSEF_DEFAULT_ENVIRONMENT=demo
KSEF_AUTH_POLL_INTERVAL=2.0
KSEF_AUTH_POLL_MAX_ATTEMPTS=30
KAFKA_ENABLED=false
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

KSeF account configuration in `config/accounts.yaml`:
```yaml
accounts:
  - name: main-company
    nip: "1234567890"
    ksef_token: "${KSEF_TOKEN}"
    environment: production

  - name: demo-company
    nip: "0987654321"
    ksef_token: "${KSEF_DEMO_TOKEN}"
    environment: demo
```

Features:
- Full KSeF 2.0 API support (API version 2.3.0)
- Authentication via KSeF tokens (challenge → encrypted token → JWT)
- Automatic JWT token refresh
- Invoice encryption (AES-256-CBC + RSA-OAEP key wrapping)
- FA(3) XML invoice generation from structured data
- Interactive and batch session management
- Invoice sending, retrieval, status checking, and querying
- UPO (Urzędowe Poświadczenie Odbioru) download
- Three environments: test, demo, production
- Multi-account support (multiple NIP entities)
- Connection validation with health checks
- Prometheus metrics

KSeF API environments:

| Environment | URL | Description |
|---|---|---|
| Test | `https://api-test.ksef.mf.gov.pl/v2` | Self-signed certs, no legal effect |
| Demo | `https://api-demo.ksef.mf.gov.pl/v2` | Real credentials, no legal effect |
| Production | `https://api.ksef.mf.gov.pl/v2` | Real documents, legal effect |

Protocol: REST (JWT authentication, AES-256-CBC invoice encryption, RSA-OAEP key exchange).

---

## 6. AI

### AI Agent (v1.0.0)

| Parameter | Required | Description |
|----------|----------|------|
| `gemini_api_key` | Yes | Google Gemini API Key |
| `model_name` | No | AI model to use (default: `gemini-2.5-flash`). Options: `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro` |
| `default_temperature` | No | Model temperature 0.0–1.0 (default: `0.1`) |
| `max_tokens` | No | Max response tokens (default: `2048`) |
| `risk_threshold_high` | No | Risk score threshold for HIGH level 0–100 (default: `60`) |
| `risk_threshold_critical` | No | Risk score threshold for CRITICAL level 0–100 (default: `85`) |

Environment variables:
```bash
AI_GEMINI_API_KEY=your-gemini-api-key
AI_MODEL_NAME=gemini-2.5-flash
AI_DEFAULT_TEMPERATURE=0.1
AI_MAX_TOKENS=2048
AI_RISK_THRESHOLD_HIGH=60
AI_RISK_THRESHOLD_CRITICAL=85
AI_AVAILABLE_COURIERS=inpost,dhl,dpd,gls,fedex,ups,pocztapolska,orlenpaczka
```

Built-in analysis templates:
- **Order risk analysis** (`agent.analyze_risk`) — evaluates order fraud risk based on order data and customer history
- **Courier recommendation** (`agent.recommend_courier`) — recommends optimal courier based on order parameters, destination, and preferences (cost/speed/reliability)
- **Data extraction** (`agent.extract_data`) — extracts structured data from text (emails, invoices, addresses)
- **Priority classification** (`agent.classify_priority`) — classifies order priority based on SLA rules and customer tier
- **Universal analysis** (`agent.analyze`) — accepts custom prompt and data, returns structured response per provided schema

Features:
- Google Gemini-powered AI analysis with configurable models
- Structured JSON output with schema enforcement
- Confidence scoring and token usage tracking
- Configurable risk thresholds for automated decision-making
- Event emission on analysis completion, risk flags, and courier recommendations

Protocol: REST (Google Gemini API with API Key authentication).

---

## 7. Credential Management via API

Integration credentials are managed through the platform REST API. Authentication: `X-API-Key` header.

### 6.1 Endpoints

| Method | Endpoint | Description | Notes |
|--------|----------|------|-------|
| `POST` | `/api/v1/credentials` | Save credentials | Body: `connector_name` + `credentials` object. Returns credential token (`ctok_xxx`). |
| `GET` | `/api/v1/credentials/{connector}` | Retrieve credentials | All values masked (`••••••••`), returns credential token |
| `GET` | `/api/v1/credentials` | List all credentials | Each entry includes its credential token |
| `POST` | `/api/v1/credentials/{connector}/validate` | Validate credentials | Available for WMS connectors (JWT) |
| `POST` | `/api/v1/credentials/{connector}/token/regenerate` | Regenerate credential token | Old token immediately invalidated |
| `POST` | `/api/v1/credentials/resolve-token` | Resolve token to credentials | Tenant-scoped, body: `{"token": "ctok_xxx"}` |
| `DELETE` | `/api/v1/credentials/{connector}` | Delete credentials | Also deletes associated token. Irreversible. |

### 6.2 Usage Example

```bash
# Save InPost credentials — response includes credential token
curl -X POST http://localhost:8080/api/v1/credentials \
  -H "X-API-Key: pk_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "inpost",
    "credentials": {
      "organization_id": "123456",
      "access_token": "abc..."
    }
  }'
# Response: { "status": "stored", "token": "ctok_aBcDeFgH...", ... }

# Retrieve credentials — values masked, token returned
curl http://localhost:8080/api/v1/credentials/inpost \
  -H "X-API-Key: pk_live_xxx"
# Response: { "values": {"organization_id": "••••••••", ...}, "token": "ctok_aBcDeFgH..." }

# Use token to call a workflow (via header — recommended)
curl "https://your-domain.com/api/v1/workflows/{id}/call?key=file.pdf" \
  -H "X-Credential-Token: ctok_aBcDeFgH..."
```

### 6.3 Security

| Aspect | Implementation |
|--------|---------------|
| Database encryption | AES-256-GCM (envelope encryption) |
| Response masking | All credential values masked as `••••••••` in GET responses — only the opaque token is returned |
| Credential tokens | Opaque `ctok_xxx` references — used instead of API keys for public-facing endpoints (e.g. workflow `/call`) |
| Token regeneration | `POST .../token/regenerate` — old token immediately invalidated |
| Validation | Available for WMS connectors (JWT login) and Email (IMAP+SMTP test); others → `unsupported` status |
| Tenant isolation | Row-Level Security in PostgreSQL |

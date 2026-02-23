# Open Integration Platform by Pinquark.com -- Architecture Documentation

> **Related documents**: `[AGENTS.md](../AGENTS.md)` (agent and coding standards), `[CONNECTORS.md](CONNECTORS.md)` (connector configuration)

## Table of contents

1. [Platform overview](#1-platform-overview)
2. [System architecture](#2-system-architecture)
3. [Data exchange](#3-data-exchange)
   - [3.2 Integration paths](#32-integration-paths) — event-driven, on-demand, and external API trigger
4. [Scaling mechanisms](#4-scaling-mechanisms)
5. [Throughput](#5-throughput)
6. [Platform configuration](#6-platform-configuration)
7. [Integration configuration](#7-integration-configuration) *(separate file: [CONNECTORS.md](CONNECTORS.md))*
8. [Deployment](#8-deployment)

---

## 1. Platform overview

Open Integration Platform by Pinquark.com is an open-source integration hub connecting any systems in an **any-to-any** architecture. Every connected system (courier, e-commerce, ERP, WMS) is an equal participant -- it can emit events and receive actions.

### Integration categories


| Category   | Number of connectors       | Examples                                                                                                       |
| ---------- | -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Courier    | 19 (including 3 InPost versions) | InPost, DHL, DPD, GLS, FedEx, UPS, Poczta Polska, Orlen Paczka, Schenker, Geis, Paxy, Packeta, SUUS, SellAsist, Raben |
| E-commerce | 3                          | Allegro, Shoper, IdoSell                                                                                       |
| WMS        | 1                          | Pinquark WMS                                                                                                   |
| Other      | 2                          | Email Client (IMAP/SMTP), SkanujFakture (invoice OCR)                                                          |


### Technology stack


| Layer          | Technology                             |
| -------------- | -------------------------------------- |
| API Gateway    | FastAPI (Python 3.12)                  |
| Dashboard      | Angular + `@pinquark/integrations` npm |
| Database       | PostgreSQL 16 (async via asyncpg)      |
| Cache          | Redis 7                                |
| Message broker | Apache Kafka (Strimzi operator)        |
| Containerization | Docker, Kubernetes                   |
| Monitoring     | Prometheus + Grafana                   |


---

## 2. System architecture

### 2.1 Component diagram

```
                        ┌─────────────────────────────────────────────────────────────┐
                        │                     Nginx Ingress                           │
                        │         Rate limit: 100 req/min per IP, TLS termination     │
                        └───────────┬──────────────────────────────────┬───────────────┘
                                    │                                  │
                         ┌──────────▼──────────┐           ┌──────────▼──────────────┐
                         │  Platform Gateway   │           │  Integrator Services    │
                         │  FastAPI :8080       │           │  FastAPI :8000 (each)   │
                         │                     │           │                         │
                         │  ┌───────────────┐  │           │  ┌── InPost ──────────┐ │
                         │  │ Rate Limiter  │  │           │  ├── DHL ─────────────┤ │
                         │  │ (Redis, per-  │  │           │  ├── Allegro ─────────┤ │
                         │  │  tenant)      │  │           │  ├── DPD ─────────────┤ │
                         │  ├───────────────┤  │           │  ├── ... (18 more)    │ │
                         │  │ Flow Engine   │  │           │  └───────────────────-┘ │
                         │  │ Workflow Eng. │  │           │                         │
                         │  │ Mapping Res.  │  │           │  Circuit Breaker        │
                         │  └───────────────┘  │           │  HTTP Connection Pool   │
                         └──┬──────────┬───────┘           └──────────┬──────────────┘
                            │          │                              │
                   ┌────────▼───┐  ┌───▼────────┐            ┌───────▼─────────┐
                   │ PostgreSQL │  │   Redis     │            │  External APIs  │
                   │ (asyncpg)  │  │  (cache +   │            │  (DHL, Allegro, │
                   │ pool: 20+30│  │  rate limit)│            │   InPost, ...)  │
                   └────────────┘  └─────────────┘            └─────────────────┘
                            │
                   ┌────────▼──────────┐
                   │    Kafka Cluster   │
                   │  3 brokers, 3 ZK   │
                   │  12-24 partitions  │
                   │  lz4 compression   │
                   └────────────────────┘
```

### 2.2 System layers


| Layer                | Components                        | Key parameters                                                                                                          |
| -------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Ingress**          | Nginx Ingress Controller          | Subdomain routing (`allegro.uat.pinquark.com`), TLS (Let's Encrypt), rate limit 100 req/min per IP, proxy timeout 60s |
| **Platform Gateway** | FastAPI `:8080`                   | Rate limit 1000 req/min per tenant (Redis), Flow Engine, Workflow Engine, Mapping Resolver                              |
| **Integrators**      | FastAPI `:8000` (each separate)   | Independent version/Dockerfile, circuit breaker (5 fails → 30s open), HTTP pool (200 conn / 50 keepalive)               |
| **Data**             | PostgreSQL 16, Redis 7, Kafka 3.7 | DB pool 20+30, Redis cache TTL 300s, Kafka 3 brokers / 12-24 partitions / lz4                                           |


---

## 3. Data exchange

### 3.1 Communication patterns


| Pattern         | Type           | Usage                                          | Examples                                                        |
| --------------- | -------------- | ---------------------------------------------- | --------------------------------------------------------------- |
| **REST API**    | Synchronous    | Operations requiring immediate response        | Shipment creation, label retrieval, credentials validation      |
| **Kafka**       | Asynchronous   | Bulk data transport, events                    | Order synchronization, bulk article import, status updates      |
| **Flow Engine** | Event-driven   | Connecting any sources with destinations       | Allegro `order.created` → InPost `shipment.create`              |


#### REST API -- flow

```
Klient  ──HTTP──>  Platform Gateway  ──HTTP──>  Integrator  ──HTTP──>  External API
                        │
                        └── PostgreSQL (persistence)
                        └── Redis (cache)
```

#### Kafka -- topic naming convention

Format: `{system}.{direction}.{domain}.{entity}.{action}`


| Topic example                          | Description          |
| -------------------------------------- | -------------------- |
| `allegro.output.ecommerce.orders.save` | Order from Allegro   |
| `courier.input.courier.shipments.save` | Shipment to courier  |
| `wms.input.wms.documents.save`         | Document to WMS      |
| `allegro.errors.ecommerce.orders.sync` | Synchronization errors |
| `courier.dlq.courier.shipments.save`   | Dead letter queue    |


#### Flow Engine -- definition example

```yaml
source:
  connector: allegro
  event: order.created
  filter:
    delivery_method: inpost_paczkomat
destination:
  connector: inpost
  action: shipment.create
mapping:
  - from: order.buyer.name -> to: receiver.first_name
  - from: order.point_id   -> to: extras.target_point
```

### 3.2 Integration paths

The platform supports three ways to trigger integrations between systems. All three use the same internal pipeline: event matching → field mapping → action dispatch → result.

| Path | Endpoint | When to use | Response |
| ---- | -------- | ----------- | -------- |
| **Event-driven** (automatic) | `POST /internal/events` | A connector (e.g. WMS poller) detects a change and emits an event automatically. Matching Flows and Workflows execute without user intervention. | Asynchronous — result stored in `FlowExecution` / `WorkflowExecution` audit log |
| **On-demand** (synchronous) | `POST /api/v1/workflows/{id}/test` with `trigger_data` | User clicks a button (e.g. "Order courier") in the UI and expects an immediate result (shipment number, label). | Synchronous — full `WorkflowExecution` returned in HTTP response |
| **External API trigger** | `POST /api/v1/events` with tenant API key | An external system (ERP, e-commerce) calls the platform API directly to trigger a flow. | Synchronous response with execution summary |

#### Example: WMS document → courier shipment + label

The most common scenario: Pinquark WMS changes a document status to "ready for shipping" and the platform automatically creates a shipment in InPost and retrieves the label.

**Path 1 — Event-driven (automatic)**

```
1. WMS Connector polls Pinquark API:
   GET {pinquark_api_url}/documents
   Detects document with erpStatusSymbol = "DO_WYSYLKI"

2. WMS Connector emits event to the platform:
   POST /internal/events
   {
     "connector_name": "pinquark-wms",
     "event": "document.synced",
     "data": {
       "erpId": 12345,
       "documentType": "WZ",
       "erpStatusSymbol": "DO_WYSYLKI",
       "deliveryAddress": { "street": "...", "city": "Warszawa", "zipCode": "00-001" },
       "contact": { "firstName": "Jan", "lastName": "Kowalski", "phone": "500100200" },
       "deliveryMethodSymbol": "INPOST_LOCKER"
     }
   }

3. Flow Engine matches enabled Flows/Workflows where:
   source_connector = "pinquark-wms" AND source_event = "document.synced"

4. For each match — applies source_filter, field_mapping, then dispatches action.
```

**Path 2 — On-demand (synchronous, e.g. user clicks "Order courier")**

Use a multi-step Workflow that creates a shipment and retrieves the label in one execution:

```
POST /api/v1/workflows/{workflow_id}/test
{
  "trigger_data": {
    "erpId": 12345,
    "documentType": "WZ",
    "deliveryAddress": { "street": "...", "city": "Warszawa", "zipCode": "00-001" },
    "contact": { "firstName": "Jan", "lastName": "Kowalski", "phone": "500100200" }
  }
}
```

The Workflow executes nodes sequentially and returns the full result (including label) in the HTTP response.

#### Multi-step Workflow: create shipment + get label

```
[Trigger: document.synced]
       │
       ▼
[Filter: documentType == "WZ" && erpStatusSymbol == "DO_WYSYLKI"]
       │
       ▼
[Action: inpost → shipment.create]
   field_mapping:
     contact.firstName       → receiver.first_name
     contact.lastName        → receiver.last_name
     contact.phone           → receiver.phone
     deliveryAddress.street  → receiver.address.street
     deliveryAddress.city    → receiver.address.city
     deliveryAddress.zipCode → receiver.address.post_code
   output: { shipment_id: "123456789", tracking_number: "62000012345" }
       │
       ▼
[Action: inpost → label.get]
   field_mapping:
     nodes.create_shipment.shipment_id → shipment_id
   output: PDF label bytes
```

Data flow between nodes: each node's output is merged into `ctx.data` and accessible via `nodes.{node_id}.{field}` in subsequent nodes. This allows chaining — the `label.get` step references `shipment_id` from the `shipment.create` step.

#### Required platform configuration

| Step | API call | What it does |
| ---- | -------- | ------------ |
| 1 | `POST /api/v1/credentials` | Store Pinquark WMS credentials (`api_url`, `username`, `password`) |
| 2 | `POST /api/v1/credentials` | Store InPost credentials (`organization_id`, `access_token`) |
| 3 | `POST /api/v1/connector-instances` | Activate the `pinquark-wms` connector for the tenant |
| 4 | `POST /api/v1/connector-instances` | Activate the `inpost` connector for the tenant |
| 5 | `POST /api/v1/flows` or `POST /api/v1/workflows` | Create a Flow (simple) or Workflow (multi-step with label) |

#### Field mapping reference (WMS → Courier)

| Pinquark WMS field | Description | Courier target field |
| --- | --- | --- |
| `contact.firstName` | Contact first name | `receiver.first_name` |
| `contact.lastName` | Contact last name | `receiver.last_name` |
| `contact.phone` | Phone number | `receiver.phone` |
| `contact.email` | Email address | `receiver.email` |
| `deliveryAddress.street` | Delivery street | `receiver.address.street` |
| `deliveryAddress.city` | Delivery city | `receiver.address.city` |
| `deliveryAddress.zipCode` | Postal code | `receiver.address.post_code` |
| `note` | Document notes | `reference` |
| `deliveryMethodSymbol` | Delivery method | `service` (via value mapping) |

These mappings are configurable per tenant via the Flow/Workflow `field_mapping` definition or via per-tenant overrides in the dashboard.

### 3.3 Data format

All REST endpoints use JSON. Error format:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "The provided API key is invalid or expired",
    "details": {},
    "trace_id": "abc123"
  }
}
```

### 3.4 Authentication

- **Platform API**: API key in the `X-API-Key` header (prefix `pk_live_` / `pk_test_`)
- **External API**: credentials stored in an encrypted vault (AES-256-GCM), per-tenant
- **Kafka**: SASL SCRAM-SHA-512

---

## 4. Scaling mechanisms

### 4.1 Horizontal Pod Autoscaler (HPA)

Every integrator in Kubernetes is covered by HPA:


| Parameter               | Value                     | Description                                                  |
| ----------------------- | ------------------------- | ------------------------------------------------------------ |
| `minReplicas`           | 2                         | Minimum for HA (can be reduced to 1 for less critical ones)  |
| `maxReplicas`           | 20                        | Maximum during peak load                                     |
| CPU target              | 70%                       | Scale up above 70% CPU usage                                 |
| Memory target           | 80%                       | Scale up above 80% memory usage                              |
| Scale-up                | max 100% or 4 pods / 60s  | Fast scale-up                                                |
| Scale-down              | max 25% / 120s            | Cautious scale-down                                          |
| Scale-down stabilization | 300s                     | Prevents flapping                                            |


**How it works in practice:**

```
Night (low traffic):    2 pods  →  ~500m CPU
Normal day:             4-6 pods → ~1.5 CPU
Peak (Black Friday):    15-20 pods → ~5-10 CPU
After peak:             gradual return to 2-4 pods (5 min stabilization)
```

Resources per pod:


| Parameter | Requests | Limits |
| --------- | -------- | ------ |
| CPU       | 250m     | 500m   |
| Memory    | 256Mi    | 512Mi  |


### 4.2 Redis caching

The caching layer offloads the database and speeds up operations:


| What is cached          | Redis key                                | TTL  | Fallback        |
| ----------------------- | ---------------------------------------- | ---- | --------------- |
| Default mappings (YAML) | `mapping:defaults:{connector}`           | 600s | In-memory dict  |
| Tenant overrides        | `mapping:overrides:{tenant}:{connector}` | 300s | Direct SQL      |


Cache is automatically invalidated when mappings change. When Redis is unavailable, the system continues operating with a fallback to local memory.

### 4.3 PostgreSQL connection pool

Instead of default SQLAlchemy settings, the platform configures a connection pool:


| Parameter       | Value   | Env var           | Description                          |
| --------------- | ------- | ----------------- | ------------------------------------ |
| `pool_size`     | 20      | `DB_POOL_SIZE`    | Maintained connections               |
| `max_overflow`  | 30      | `DB_MAX_OVERFLOW` | Additional connections during peak   |
| `pool_timeout`  | 30s     | `DB_POOL_TIMEOUT` | Wait time for a free connection      |
| `pool_recycle`  | 1800s   | `DB_POOL_RECYCLE` | Connection refresh interval (30 min) |
| `pool_pre_ping` | true    | --                | Connection verification before use   |


Total: up to 50 active connections (20 base + 30 overflow) per gateway instance.

### 4.4 Kafka tuning

#### Cluster (3 brokers + 3 ZooKeeper)


| Parameter                    | Value   |
| ---------------------------- | ------- |
| Broker replicas              | 3       |
| `min.insync.replicas`        | 2       |
| `default.replication.factor` | 3       |
| Storage per broker           | 50Gi    |
| `message.max.bytes`          | 10MB    |
| `num.io.threads`             | 8       |
| `num.network.threads`        | 5       |


#### Topics


| Topic type            | Partitions | Replicas | Retention        |
| --------------------- | ---------- | -------- | ---------------- |
| Data (courier)        | 24         | 3        | 7 days           |
| Data (ecommerce, wms) | 12         | 3        | 7 days           |
| Error                 | 3          | 3        | 30 days          |
| DLQ                   | 3          | 3        | 30 days (compact) |


#### Producer (sending)


| Parameter          | Value   | Effect                                |
| ------------------ | ------- | ------------------------------------- |
| `compression_type` | lz4     | ~60% size reduction, minimal CPU      |
| `linger_ms`        | 50      | Message batching every 50ms           |
| `batch_size`       | 64KB    | Max batch size                        |
| `acks`             | all     | Acknowledgment from all replicas      |
| `max_request_size` | 10MB    | Max request size                      |


Available methods:

- `send()` -- single message (await, guaranteed delivery)
- `send_batch()` -- multiple messages at once (concurrent, returns success count)

#### Consumer (receiving)


| Parameter            | Value   | Effect                         |
| -------------------- | ------- | ------------------------------ |
| `max_poll_records`   | 500     | Up to 500 messages at once     |
| `fetch_max_bytes`    | 50MB    | Max data per fetch             |
| `enable_auto_commit` | false   | Manual commit after processing |


Available modes:

- `consume()` -- one message at a time (backward compatible)
- `consume_batches()` -- batches via `getmany()` (up to 500 msg at once)

### 4.5 Circuit breaker

Protects against cascading failures from external APIs. Each target host (e.g., `api.allegro.pl`, `api-shipx.inpost.pl`) has its own circuit breaker.


| State                   | Transition  | Condition            |
| ----------------------- | ----------- | -------------------- |
| **CLOSED** (normal)     | → OPEN      | 5 consecutive errors |
| **OPEN** (blocking)     | → HALF_OPEN | After 30s timeout    |
| **HALF_OPEN** (testing) | → CLOSED    | 1 successful request |
| **HALF_OPEN**           | → OPEN      | 1 failed request     |



| Parameter            | Value                                                  |
| -------------------- | ------------------------------------------------------ |
| Opening threshold    | 5 consecutive errors                                   |
| Reset timeout        | 30s                                                    |
| Max attempts in HALF_OPEN | 1                                                 |
| Prometheus metrics   | `circuit_breaker_state`, `circuit_breaker_trips_total` |


When CB is open, requests return an immediate 503 error instead of waiting for a timeout.

### 4.6 HTTP connection pool

TCP/TLS connection reuse per host instead of creating a new `httpx.AsyncClient` per request:


| Parameter                   | Value   | Benefits                          |
| --------------------------- | ------- | --------------------------------- |
| `max_connections`           | 200     | Control of concurrent connections |
| `max_keepalive_connections` | 50      | Eliminates TLS handshake overhead |
| Default timeout             | 30s     | Protection against hanging        |


Integration: circuit breaker per host + connection pool per host = full control over outgoing connections.

### 4.7 Rate limiting (per-tenant)

Redis-based sliding window rate limiter:


| Parameter     | Value                                        | Env var                     |
| ------------- | -------------------------------------------- | --------------------------- |
| Limit         | 1000 req/min                                 | `RATE_LIMIT_REQUESTS`       |
| Window        | 60s                                          | `RATE_LIMIT_WINDOW_SECONDS` |
| Identifier    | API key prefix (16 characters)               | --                          |
| Bypass paths  | `/health`, `/readiness`, `/metrics`, `/docs` | --                          |


Response headers:


| Header                  | When          | Value                              |
| ----------------------- | ------------- | ---------------------------------- |
| `X-RateLimit-Limit`     | Every request | Max requests in the window (e.g., `1000`) |
| `X-RateLimit-Remaining` | Every request | Remaining requests                 |
| `X-RateLimit-Reset`     | Every request | Unix timestamp of window reset     |
| `Retry-After`           | Only 429      | Seconds until retry                |


---

## 5. Throughput

### 5.1 Estimated performance per component


| Component         | Throughput (per instance)   | Scaling               |
| ----------------- | --------------------------- | --------------------- |
| Platform Gateway  | ~5 000-10 000 req/min       | HPA up to 20 replicas |
| Integrator (REST) | ~3 000-8 000 req/min        | HPA up to 20 replicas |
| Kafka producer    | ~50 000 msg/min (batch)     | Partitioning          |
| Kafka consumer    | ~30 000 msg/min (batch 500) | Consumer groups       |
| Redis cache hit   | ~100 000 ops/min            | Single node / cluster |
| PostgreSQL        | ~5 000 queries/min          | Pool 50 conn          |


### 5.2 Total system throughput


| Scenario              | Gateway (replicas) | Integrators (replicas) | Kafka     | Total throughput             |
| --------------------- | ------------------ | ---------------------- | --------- | ---------------------------- |
| Development           | 1                  | 1 per type             | 1 broker  | ~5 000 req/min               |
| UAT                   | 2                  | 2 per type             | 3 brokers | ~20 000 req/min              |
| Production (standard) | 4-6                | 3-5 per type           | 3 brokers | ~100 000 req/min             |
| Production (peak)     | 10-20              | 10-20 per type         | 3 brokers | ~500 000-1 000 000 req/min   |


### 5.3 Bottlenecks and their solutions


| Bottleneck               | Symptom               | Metric/log                                        | Solution                                                         |
| ------------------------ | --------------------- | ------------------------------------------------- | ---------------------------------------------------------------- |
| No free DB connections   | `pool_timeout` errors | SQLAlchemy pool exhausted                         | Increase `DB_POOL_SIZE` / `DB_MAX_OVERFLOW`                      |
| Redis latency            | Slow cache hits       | `integrator_request_duration_seconds` ↑           | Redis Cluster / increase `REDIS_MAX_CONNECTIONS`                 |
| Kafka consumer lag       | Growing queue         | Kafka consumer lag metric > 1000                  | More consumers (max = partitions), increase `max_poll_records`   |
| External API rate limit  | 429 from external API | `integrator_external_api_calls_total{status=429}` | Respect `Retry-After`, per-connector throttling                  |
| Circuit breaker open     | 503 from shared client| `circuit_breaker_state` = 1                       | Wait for reset (30s), investigate error source                   |


---

## 6. Platform configuration

### 6.1 Platform environment variables

#### Application


| Variable    | Default      | Description                                              |
| ----------- | ------------ | -------------------------------------------------------- |
| `APP_ENV`   | `production` | Environment: `development` / `production`                |
| `APP_PORT`  | `8080`       | HTTP port                                                |
| `LOG_LEVEL` | `INFO`       | Log level: `DEBUG` / `INFO` / `WARNING` / `ERROR`       |


#### PostgreSQL


| Variable          | Default                                                                          | Description                                 |
| ----------------- | -------------------------------------------------------------------------------- | ------------------------------------------- |
| `DATABASE_URL`    | `postgresql+asyncpg://pinquark:password@postgres:5432/pinquark_platform`         | Connection string                           |
| `DB_POOL_SIZE`    | `20`                                                                             | Base number of connections in the pool      |
| `DB_MAX_OVERFLOW` | `30`                                                                             | Additional connections during peak          |
| `DB_POOL_TIMEOUT` | `30`                                                                             | Timeout waiting for a free connection (s)   |
| `DB_POOL_RECYCLE` | `1800`                                                                           | Connection refresh every N seconds          |


#### Redis


| Variable                | Default                | Description              |
| ----------------------- | ---------------------- | ------------------------ |
| `REDIS_URL`             | `redis://redis:6379/0` | Redis connection string  |
| `REDIS_MAX_CONNECTIONS` | `50`                   | Max connections in pool  |
| `REDIS_SOCKET_TIMEOUT`  | `5.0`                  | Timeout per operation (s)|
| `REDIS_CACHE_TTL`       | `300`                  | Default cache TTL (s)    |


#### Rate limiting


| Variable                    | Default  | Description                               |
| --------------------------- | -------- | ----------------------------------------- |
| `RATE_LIMIT_REQUESTS`       | `1000`   | Max requests per tenant per window        |
| `RATE_LIMIT_WINDOW_SECONDS` | `60`     | Window duration (s)                       |


#### Security


| Variable                          | Default      | Description                                                       |
| --------------------------------- | ------------ | ----------------------------------------------------------------- |
| `ENCRYPTION_KEY`                  | *(required)* | AES-256-GCM key for credential vault (base64, 32 bytes)           |
| `JWT_SECRET_KEY`                  | *(required)* | JWT signing key                                                   |
| `JWT_ALGORITHM`                   | `HS256`      | JWT algorithm                                                     |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30`         | JWT token lifetime (min)                                          |


#### Connector discovery


| Variable                   | Default        | Description                       |
| -------------------------- | -------------- | --------------------------------- |
| `CONNECTOR_DISCOVERY_PATH` | `/integrators` | Path to the connectors directory  |


### 6.2 Docker Compose (development)

```bash
cd platform
docker compose up -d
```

Starts: platform gateway, PostgreSQL 16, Redis 7.

### 6.3 Docker Compose (production)

```bash
docker compose -f docker-compose.prod.yml up -d
```

Starts: platform, dashboard, PostgreSQL, Redis, and selected connectors (InPost, DHL, DPD, Allegro, WMS).

### 6.4 Kubernetes

Configuration in `k8s/integrators/base/`:


| File              | Purpose             | Key parameters                                                          |
| ----------------- | ------------------- | ----------------------------------------------------------------------- |
| `deployment.yaml` | Deployment template | 2 replicas, CPU 250m-500m, memory 256Mi-512Mi, liveness/readiness probes |
| `hpa.yaml`        | Autoscaling         | 2-20 replicas, CPU target 70%, memory target 80%                        |
| `configmap.yaml`  | Shared variables    | Kafka brokers, log level, service discovery                             |
| `secret.yaml`     | Secrets             | Replaced by CI/CD (never commit values)                                 |


---

## 7. Integration configuration

Detailed documentation of configuration parameters for all 24 connectors (16 couriers, Allegro, Shoper, Shopify, IdoSell, Pinquark WMS, Email Client, SkanujFakture) and credentials management via API can be found in a separate file:

**[CONNECTORS.md](CONNECTORS.md)**

It covers:

- Required and optional parameters for each connector
- Environment variables per integrator
- Account configuration (e.g., Allegro `accounts.yaml`)
- Credentials management via REST API (save, validate, read, delete)
- Connection validation mechanism for each connector

---

## 8. Deployment

### 8.1 Local setup (development)

```bash
# Platform + database + Redis
cd platform && docker compose up -d

# Allegro integrator (standalone)
cd integrators/ecommerce/allegro/v1.0.0
cp .env.example .env  # fill in credentials
docker compose up -d

# Full system (production-like)
cp .env.example .env  # fill in secrets
docker compose -f docker-compose.prod.yml up -d
```

### 8.2 Adding a connector to Docker Compose

To make a new connector available in the workflow and flow system, follow 3 steps:

#### Step 1: Add the service to `docker-compose.prod.yml`

The service name **must** follow the pattern `connector-{name}`, e.g., `connector-skanuj-fakture`. The platform resolves connector addresses as `http://connector-{name}:8000`.

**Variant A** -- Dockerfile in the integrator directory (build context = integrator directory):

```yaml
connector-moj-konektor:
  build:
    context: ./integrators/{kategoria}/{nazwa}/v1.0.0
  environment:
    APP_ENV: production
    APP_PORT: 8000
  depends_on:
    - platform
  restart: unless-stopped
```

**Variant B** -- Dockerfile requires root context (e.g., copies `shared/python`):

```yaml
connector-moj-konektor:
  build:
    context: .
    dockerfile: integrators/{kategoria}/{nazwa}/v1.0.0/Dockerfile
  environment:
    APP_ENV: production
    APP_PORT: 8000
  depends_on:
    - platform
  restart: unless-stopped
```

Choose Variant B when the `Dockerfile` uses `COPY shared/python ...` or references files outside the integrator directory.

Additional environment variables (optional, depending on the connector):


| Variable                | When to add                                    | Example                                   |
| ----------------------- | ---------------------------------------------- | ----------------------------------------- |
| `KAFKA_ENABLED`         | Connector uses Kafka                           | `"false"` (when Kafka is not in compose)  |
| `PLATFORM_API_URL`      | Connector sends events to the platform         | `http://platform:8080`                    |
| `PLATFORM_EVENT_NOTIFY` | Connector should notify the platform of events | `"true"`                                  |


#### Step 2: Register action routing in `platform/core/action_dispatcher.py`

Add an entry in `_CONNECTOR_SERVICE_NAMES` (connector name -> Docker service name mapping):

```python
_CONNECTOR_SERVICE_NAMES: dict[str, str] = {
    ...
    "moj-konektor": "connector-moj-konektor",
}
```

Add action routing in `_ACTION_ROUTES` (action to connector HTTP endpoint mapping):

```python
_ACTION_ROUTES: dict[str, dict[str, ActionRoute]] = {
    ...
    "moj-konektor": {
        "document.upload": ActionRoute(
            method="POST",
            path="/documents",
            query_from_payload=["account_name"],
        ),
        "document.list": ActionRoute(
            method="GET",
            path="/documents",
        ),
    },
}
```

If the connector requires account provisioning (like `email-client` or `skanuj-fakture`), add the corresponding `_ensure_{connector}_account()` function and handling in `dispatch_action()`.

#### Step 3: Build and run

```bash
# Build and run only the new connector
docker compose -f docker-compose.prod.yml up -d --build connector-moj-konektor

# Check health
docker compose -f docker-compose.prod.yml exec platform \
  curl -sf http://connector-moj-konektor:8000/health

# If you changed action_dispatcher.py, also rebuild the platform
docker compose -f docker-compose.prod.yml up -d --build platform connector-moj-konektor
```

#### Verification

After startup, verify:

1. **Health check**: `curl http://connector-moj-konektor:8000/health` from inside the Docker network
2. **Platform discovery**: the connector should appear in `GET /api/v1/connectors` (if it has a `connector.yaml`)
3. **Workflow/Flow**: it can be used as an action target in workflows and flows
4. **Logs**: `docker compose -f docker-compose.prod.yml logs connector-moj-konektor`

---

### 8.3 Kubernetes (UAT/production)

```bash
# Kafka cluster
kubectl apply -f k8s/base/kafka/kafka-cluster.yaml
kubectl apply -f k8s/base/kafka/kafka-topics.yaml

# Secrets (via CI/CD or manual)
kubectl apply -f k8s/integrators/base/secret.yaml

# Config + deployment + HPA + ingress
kubectl apply -f k8s/integrators/base/configmap.yaml
kubectl apply -f k8s/integrators/base/deployment.yaml
kubectl apply -f k8s/integrators/base/hpa.yaml
kubectl apply -f k8s/base/ingress/ingress.yaml
```

### 8.4 Health check

Every component exposes:


| Endpoint         | Description                    | Auth             |
| ---------------- | ------------------------------ | ---------------- |
| `GET /health`    | Liveness: is the process running | No             |
| `GET /readiness` | Readiness: are dependencies OK | No               |
| `GET /metrics`   | Prometheus metrics             | Internal network |


Example `/health` response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": "ok",
    "redis": "ok",
    "registry": "ok"
  }
}
```

### 8.5 Monitoring

Prometheus metrics available at `/metrics`:


| Metric                                     | Type      | Description                             |
| ------------------------------------------ | --------- | --------------------------------------- |
| `integrator_requests_total`                | Counter   | Requests per endpoint/status            |
| `integrator_request_duration_seconds`      | Histogram | Latency per endpoint                    |
| `integrator_external_api_calls_total`      | Counter   | External API calls                      |
| `integrator_external_api_duration_seconds` | Histogram | External API latency                    |
| `circuit_breaker_state`                    | Gauge     | CB state (0=closed, 1=open, 2=half_open)|
| `circuit_breaker_trips_total`              | Counter   | Number of times CB opened               |

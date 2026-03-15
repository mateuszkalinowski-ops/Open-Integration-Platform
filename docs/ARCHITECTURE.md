# Open Integration Platform by Pinquark.com -- Architecture Documentation

> **Related documents**: `[AGENTS.md](../AGENTS.md)` (agent and coding standards), `[CONNECTORS.md](CONNECTORS.md)` (connector configuration)

## Table of contents

1. [Platform overview](#1-platform-overview)
2. [System architecture](#2-system-architecture)
3. [Data exchange](#3-data-exchange)
  - [3.2 Integration paths](#32-integration-paths) — event-driven, on-demand, and external API trigger
  - [3.5 Sync State Engine](#35-sync-state-engine--incremental-data-synchronization) — deduplication, change detection, retry logic
4. [Database schema](#4-database-schema)
5. [Scaling mechanisms](#5-scaling-mechanisms)
6. [Throughput](#6-throughput)
7. [Platform configuration](#7-platform-configuration)
8. [Integration configuration](#8-integration-configuration) *(separate file: [CONNECTORS.md](CONNECTORS.md))*
9. [Deployment](#9-deployment)

---

## 1. Platform overview

Open Integration Platform by Pinquark.com is an open-source integration hub connecting any systems in an **any-to-any** architecture. Every connected system (courier, e-commerce, ERP, WMS) is an equal participant -- it can emit events and receive actions.

### Integration categories


| Category   | Number of connectors             | Examples                                                                                                              |
| ---------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Courier    | 18 (including 3 InPost versions) | InPost, DHL, DPD, GLS, FedEx, UPS, Poczta Polska, Orlen Paczka, Schenker, Geis, Paxy, Packeta, SUUS, Raben           |
| E-commerce | 8                                | Allegro, Amazon, Apilo, BaseLinker, Shopify, Shoper, IdoSell, SellAsist                                               |
| ERP        | 1                                | InsERT Nexo (hybrid on-premise + cloud)                                                                               |
| WMS        | 1                                | Pinquark WMS                                                                                                          |
| AI         | 1                                | Gemini AI Agent (risk analysis, courier recommendations, data extraction)                                             |
| Other      | 6                                | Email Client (IMAP/SMTP), SkanujFakture (invoice OCR), FTP/SFTP (file transfer), Slack, BulkGate SMS, Amazon S3      |


### Technology stack


| Layer            | Technology                             |
| ---------------- | -------------------------------------- |
| API Gateway      | FastAPI (Python 3.12)                  |
| Dashboard        | Angular + `@pinquark/integrations` npm |
| Database         | PostgreSQL 16 (async via asyncpg)      |
| Cache            | Redis 7                                |
| Message broker   | Apache Kafka (Strimzi operator)        |
| Containerization | Docker, Kubernetes                     |
| Monitoring       | Prometheus + Grafana                   |


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
                         │  │  tenant +     │  │           │  ├── DPD ─────────────┤ │
                         │  │  per-connector│  │           │  ├── ... (31 more)    │ │
                         │  ├───────────────┤  │           │  └───────────────────-┘ │
                         │  │ Flow Engine   │  │           │                         │
                         │  │ Workflow Eng. │  │           │  Circuit Breaker        │
                         │  │ Mapping Res.  │  │           │  HTTP Connection Pool   │
                         │  │ OAuth2 Mgr.   │  │           │                         │
                         │  │ Webhook Ingest│  │           │                         │
                         │  │ Schema Reg.   │  │           │                         │
                         │  │ Health Mon.   │  │           │                         │
                         │  │ Audit Trail   │  │           │                         │
                         │  └───────────────┘  │           │                         │
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


| Layer                | Components                        | Key parameters                                                                                                        |
| -------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Ingress**          | Nginx Ingress Controller          | Subdomain routing (`allegro.example.com`), TLS (Let's Encrypt), rate limit 100 req/min per IP, proxy timeout 60s |
| **Platform Gateway** | FastAPI `:8080`                   | Rate limit 1000 req/min per tenant (Redis), Flow Engine, Workflow Engine, Mapping Resolver, OAuth2 Manager, Webhook Ingestion, Schema Registry, Audit Trail, Connector Health Monitor, Connector Rate Limiter, Workflow Scheduler |
| **Integrators**      | FastAPI `:8000` (each separate)   | Independent version/Dockerfile, circuit breaker (5 fails → 30s open), HTTP pool (200 conn / 50 keepalive)             |
| **Data**             | PostgreSQL 16, Redis 7, Kafka 3.7 | DB pool 20+30, Redis cache TTL 300s, Kafka 3 brokers / 12-24 partitions / lz4                                         |


---

## 3. Data exchange

### 3.1 Communication patterns


| Pattern         | Type         | Usage                                    | Examples                                                   |
| --------------- | ------------ | ---------------------------------------- | ---------------------------------------------------------- |
| **REST API**    | Synchronous  | Operations requiring immediate response  | Shipment creation, label retrieval, credentials validation |
| **Kafka**       | Asynchronous | Bulk data transport, events              | Order synchronization, bulk article import, status updates |
| **Flow Engine** | Event-driven | Connecting any sources with destinations | Allegro `order.created` → InPost `shipment.create`         |


#### REST API -- flow

```
Klient  ──HTTP──>  Platform Gateway  ──HTTP──>  Integrator  ──HTTP──>  External API
                        │
                        └── PostgreSQL (persistence)
                        └── Redis (cache)
```

#### Kafka -- topic naming convention

Format: `{system}.{direction}.{domain}.{entity}.{action}`


| Topic example                          | Description            |
| -------------------------------------- | ---------------------- |
| `allegro.output.ecommerce.orders.save` | Order from Allegro     |
| `courier.input.courier.shipments.save` | Shipment to courier    |
| `wms.input.wms.documents.save`         | Document to WMS        |
| `allegro.errors.ecommerce.orders.sync` | Synchronization errors |
| `courier.dlq.courier.shipments.save`   | Dead letter queue      |


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


| Path                         | Endpoint                                               | When to use                                                                                                                                      | Response                                                                        |
| ---------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| **Event-driven** (automatic) | `POST /internal/events`                                | A connector (e.g. WMS poller) detects a change and emits an event automatically. Matching Flows and Workflows execute without user intervention. | Asynchronous — result stored in `FlowExecution` / `WorkflowExecution` audit log |
| **On-demand** (synchronous)  | `POST /api/v1/workflows/{id}/test` with `trigger_data` | User clicks a button (e.g. "Order courier") in the UI and expects an immediate result (shipment number, label).                                  | Synchronous — full `WorkflowExecution` returned in HTTP response                |
| **GET call** (URL-triggered) | `GET /api/v1/workflows/{id}/call?param=value`          | Trigger a workflow via URL with query params as `trigger_data`. If the result contains a `url` field, returns **302 redirect**; otherwise JSON.   | 302 redirect to result URL, or JSON with `context_snapshot.data`                |
| **External API trigger**     | `POST /api/v1/events` with tenant API key              | An external system (ERP, e-commerce) calls the platform API directly to trigger a flow.                                                          | Synchronous response with execution summary                                     |


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

**Path 3 — GET call (URL-triggered, e.g. S3 file access)**

Execute a workflow by passing parameters directly in the URL. If the workflow produces a `url` field in its output, the endpoint returns a 302 redirect — the browser follows it automatically.

```
GET /api/v1/workflows/{workflow_id}/call?key=report.pdf&bucket=my-bucket
```

All query parameters become `trigger_data` for the workflow. Example with S3 presigned URL workflow:

```
GET /api/v1/workflows/{id}/call?key=Etykieta+towaru.pdf
  → Workflow executes: trigger → s3.object.presign → response
  → 302 Redirect → https://s3.waw.io.cloud.ovh.net/bucket/Etykieta%20towaru.pdf?Signature=...
  → Browser downloads the file
```

This is useful for embedding file links in HTML, email templates, or external systems without requiring POST requests or JavaScript.

#### Required platform configuration


| Step | API call                                         | What it does                                                       |
| ---- | ------------------------------------------------ | ------------------------------------------------------------------ |
| 1    | `POST /api/v1/credentials`                       | Store Pinquark WMS credentials (`api_url`, `username`, `password`) |
| 2    | `POST /api/v1/credentials`                       | Store InPost credentials (`organization_id`, `access_token`)       |
| 3    | `POST /api/v1/connector-instances`               | Activate the `pinquark-wms` connector for the tenant               |
| 4    | `POST /api/v1/connector-instances`               | Activate the `inpost` connector for the tenant                     |
| 5    | `POST /api/v1/flows` or `POST /api/v1/workflows` | Create a Flow (simple) or Workflow (multi-step with label)         |


#### Field mapping reference (WMS → Courier)


| Pinquark WMS field        | Description        | Courier target field          |
| ------------------------- | ------------------ | ----------------------------- |
| `contact.firstName`       | Contact first name | `receiver.first_name`         |
| `contact.lastName`        | Contact last name  | `receiver.last_name`          |
| `contact.phone`           | Phone number       | `receiver.phone`              |
| `contact.email`           | Email address      | `receiver.email`              |
| `deliveryAddress.street`  | Delivery street    | `receiver.address.street`     |
| `deliveryAddress.city`    | Delivery city      | `receiver.address.city`       |
| `deliveryAddress.zipCode` | Postal code        | `receiver.address.post_code`  |
| `note`                    | Document notes     | `reference`                   |
| `deliveryMethodSymbol`    | Delivery method    | `service` (via value mapping) |


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
- **Credential tokens**: opaque tokens (`ctok_xxx`) that reference stored credentials without exposing their values. Can also be used as lightweight authentication for public-facing endpoints (e.g. workflow `/call`) instead of the full API key.
- **External API**: credentials stored in an encrypted vault (AES-256-GCM), per-tenant
- **Kafka**: SASL/PLAIN over TLS (SASL_SSL with PLAIN mechanism, configurable via `KAFKA_SASL_MECHANISM`)

#### Demo Gate (self-service tenant registration)

For demo and evaluation deployments the platform provides a **Demo Gate** — a lightweight registration flow that allows users to create isolated workspaces without a full authentication system. It is enabled by setting `DEMO_MODE=true` and will be replaced by proper login/SSO in production.

```
User opens dashboard
       │
       ▼
┌──────────────────────┐     ┌─────────────────────────┐
│ API key in           │ No  │ Gate screen             │
│ localStorage?        │────▶│  • "Create workspace"   │
└──────┬───────────────┘     │  • "I have a key"       │
       │ Yes                 └──────────┬──────────────┘
       ▼                                │
┌──────────────────────┐     ┌──────────▼──────────────┐
│ Validate key         │     │ POST /api/v1/demo/      │
│ (GET /health)        │     │   register              │
└──────┬───────────────┘     │ or validate-key         │
       │ Valid               └──────────┬──────────────┘
       ▼                                │
   Load dashboard ◀─────────────────────┘
   (key in localStorage,                 save key + reload
    injected via PINQUARK_CONFIG)
```

**How it works:**

1. On first visit the Angular dashboard shows a full-screen gate page (route `/gate`).
2. The user either creates a new workspace (enters a name) or provides an existing API key.
3. `POST /api/v1/demo/register` creates a `Tenant` (with plan `demo`) and an `ApiKey` with prefix `pk_demo_`, returns the raw key once.
4. The key is stored in `localStorage('pinquark_demo_api_key')` and used as the `X-API-Key` header for all subsequent API calls — the existing `get_current_tenant()` middleware handles tenant resolution identically to production keys.
5. All data (credentials, flows, workflows, connector instances) is scoped to the tenant via `tenant_id` foreign keys — users cannot see each other's data.
6. A `canActivate` route guard redirects unauthenticated users to `/gate`; the sidebar shows the workspace name and offers "Copy API key" and "Switch workspace" actions.

**Endpoints (public, no auth required, only available when `DEMO_MODE=true`):**

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/demo/register` | POST | Create workspace + API key. Body: `{ "workspace_name": "..." }`. Rate-limited to 10 per IP per hour. |
| `/api/v1/demo/validate-key` | POST | Validate an existing key. Body: `{ "api_key": "pk_demo_..." }`. Returns `{ "valid": true, "tenant_name": "..." }`. |

**Transition to production auth:** When login/SSO is implemented, the gate page is replaced by a login screen, the API key in localStorage is replaced by a session token, and the `DEMO_MODE` flag is set to `false` — the demo endpoints return 404 and the backend tenant model remains unchanged.

### 3.4.1 Dynamic schema registry

Phase 4 also adds a schema registry layer for action input/output discovery:

```
Dashboard
   │
   ├── GET /api/v1/connectors/{name}/schema/{action}
   │       │
   │       ├── Redis cache hit → return cached schema
   │       ├── Connector /schema/{action} endpoint available → merge dynamic + static fields
   │       └── No runtime schema → fall back to connector.yaml action_fields/output_fields
   │
   └── Flow / workflow editors use the merged schema for mapping UIs
```

The registry is backward-compatible: legacy connectors continue to work with manifest-only schemas, while SDK-based connectors can expose `/schema/{action}` for richer runtime metadata.

### 3.5 Sync State Engine — Incremental Data Synchronization

The Sync State Engine prevents duplicate processing and enables incremental synchronization between systems. It is built into the Workflow Engine and uses the `sync_ledger` PostgreSQL table to track per-entity sync state.

#### Problem it solves

When polling external systems (e.g., fetching orders from Allegro every 5 minutes), the same data arrives repeatedly. Without deduplication:
- The same order would create duplicate shipments in a courier system
- Unchanged records would trigger unnecessary API calls
- Failed syncs would have no retry mechanism

#### How it works

```
Event arrives
     │
     ▼
┌─────────────────────────────┐
│  Resolve entity_key from    │  e.g. event_data["erpId"] → "12345"
│  event data                 │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Compute content_hash       │  SHA-256 of selected fields (or entire payload)
│  (deterministic SHA-256)    │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Query sync_ledger          │  SELECT WHERE workflow_id = ? AND entity_key = ?
│  for existing entry         │
└─────────────┬───────────────┘
              │
     ┌────────┴────────┬──────────────┬──────────────┐
     ▼                 ▼              ▼              ▼
  No entry          Same hash      Diff hash     Status=failed
  found             & synced       (changed)     & retries left
     │                 │              │              │
     ▼                 ▼              ▼              ▼
   SYNC              SKIP          UPDATE         RETRY
 (new entity)    (no change)    (re-sync)      (retry sync)
     │                 │              │              │
     ▼                 ▼              ▼              ▼
  Execute          Return None    Execute         Execute
  workflow         (no action)    workflow         workflow
     │                              │              │
     ▼                              ▼              ▼
  Record success/failure in sync_ledger
```

#### Sync decisions

| Decision | Condition | Action |
| --- | --- | --- |
| **SYNC** | Entity key not found in ledger | Execute workflow, create new ledger entry |
| **SKIP** | Same `content_hash` and `sync_status = "synced"` | Do nothing — data unchanged |
| **UPDATE** | Different `content_hash` | Re-execute workflow, update ledger entry |
| **RETRY** | `sync_status = "failed"` and `attempt_count < max_retries` | Re-execute workflow, increment attempt count |

#### Sync modes

| Mode | Behavior |
| --- | --- |
| `incremental` (default) | Check ledger before executing — skip unchanged, sync new/changed entities |
| `force` | Always execute the workflow, then record success in ledger (bypass dedup checks) |
| `full_sync` | Mark all existing entries as `stale`, then sync everything — useful for periodic full reconciliation |

#### Duplicate handling policy (`on_duplicate`)

When the content hash has changed (decision = `UPDATE`):

| Policy | Behavior |
| --- | --- |
| `skip` | Do not re-sync — only new entities are processed |
| `update` | Re-sync the entity with the new data |
| `force` | Always re-sync regardless of hash |

#### Workflow `sync_config` schema

Sync is enabled per-workflow via the `sync_config` JSONB field:

```json
{
  "enabled": true,
  "entity_key_field": "erpId",
  "content_hash_fields": ["erpStatusSymbol", "deliveryAddress", "contact"],
  "mode": "incremental",
  "on_duplicate": "update",
  "max_retries": 3
}
```

| Field | Type | Description |
| --- | --- | --- |
| `enabled` | `boolean` | Enable/disable sync tracking for this workflow |
| `entity_key_field` | `string \| string[]` | Field path(s) in event data to build the unique entity key. Supports dot-notation (`document.erp_id`) and composite keys (`["source", "erp_id"]` → `"allegro:12345"`) |
| `content_hash_fields` | `string[]` | Fields to include in the SHA-256 hash. `["*"]` or omitted = hash entire payload (excluding internal metadata) |
| `mode` | `string` | `incremental` (default), `force`, or `full_sync` |
| `on_duplicate` | `string` | `skip` (default), `update`, or `force` |
| `retry_failed` | `boolean` | Whether to automatically retry failed entries |
| `max_retries` | `integer` | Maximum retry attempts before giving up (default: 3) |

#### Content hash computation

The hash is a deterministic SHA-256 of selected event data fields:

1. If `content_hash_fields` is specified (e.g., `["status", "address"]`), only those fields are hashed
2. If `content_hash_fields` is `["*"]` or omitted, the entire payload is hashed (excluding internal metadata fields like `_`, `account_name`, `polled_at`)
3. Data is serialized via `json.dumps(sort_keys=True)` for determinism

This allows fine-grained control — e.g., only re-sync when `erpStatusSymbol` or `deliveryAddress` changes, ignoring timestamp changes.

#### Entity key resolution

The entity key uniquely identifies a record across sync runs. It supports:

- **Simple field**: `"erpId"` → `"12345"`
- **Nested dot-notation**: `"document.erp_id"` → `"67890"`
- **Composite key**: `["source", "erp_id"]` → `"allegro:12345"` (joined with `:`)

#### Workflow execution endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/workflows/{id}/test` | POST | Execute workflow with `trigger_data` body (test mode) |
| `/api/v1/workflows/{id}/execute` | POST | Execute workflow with `trigger_data` body (production) |
| `/api/v1/workflows/{id}/call` | GET | Execute workflow with query params as `trigger_data`. Returns 302 redirect if output has `url`, otherwise JSON |
| `/api/v1/workflows/{id}/toggle` | POST | Enable/disable workflow |

#### Ledger states

| Status | Meaning |
| --- | --- |
| `pending` | Entry created, not yet processed |
| `synced` | Successfully synchronized |
| `failed` | Sync failed (will be retried up to `max_retries`) |
| `stale` | Marked for re-sync during `full_sync` mode |

#### REST API endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/workflows/{id}/sync-stats` | GET | Get sync ledger statistics (synced/failed/pending/stale counts) |
| `/api/v1/workflows/{id}/sync-failed` | GET | List failed sync entries with error details (max 200) |
| `/api/v1/workflows/{id}/sync-retry` | POST | Reset all failed entries to pending for retry |
| `/api/v1/workflows/{id}/sync-clear` | POST | Delete all ledger entries (force full re-sync) |

#### Example: sync stats response

```json
{
  "workflow_id": "abc-123",
  "workflow_name": "Allegro → InPost",
  "sync_config": {
    "enabled": true,
    "entity_key_field": "erpId",
    "mode": "incremental"
  },
  "stats": {
    "synced": 1250,
    "failed": 3,
    "pending": 0,
    "stale": 0,
    "total": 1253
  }
}
```

#### Implementation

| Component | File | Responsibility |
| --- | --- | --- |
| `SyncStateManager` | `platform/core/sync_state.py` | Ledger queries, decision logic, record success/failure |
| `WorkflowEngine._execute_with_sync` | `platform/core/workflow_engine.py` | Orchestrates sync check → workflow execution → ledger update |
| `SyncLedger` | `platform/db/models.py` | SQLAlchemy model for the `sync_ledger` table |
| `SyncConfig` | `dashboard/.../workflow.model.ts` | TypeScript interface for UI configuration |

---

## 4. Database schema

> **Maintenance rule**: This diagram MUST be updated whenever the database schema changes (new tables, column additions/removals, relationship changes, new migrations). The source image is stored at `docs/database-schema.png`. Current diagram reflects migrations 001–013.

![Database Schema ERD](database-schema.png)

### 4.1 Table overview

| Table | Purpose | Key relationships |
| --- | --- | --- |
| `tenants` | Multi-tenant isolation — central table for all tenant-scoped data | Parent of all tenant-scoped tables |
| `api_keys` | Hashed API keys for platform authentication | FK → `tenants` |
| `connector_instances` | Connectors activated by a tenant with version and config | FK → `tenants`, UQ(tenant, name, version) |
| `credentials` | AES-256-GCM encrypted credentials per connector per tenant | FK → `tenants`, UQ(tenant, connector, name, key) |
| `credential_tokens` | Opaque token references for credential sets — used in GET responses and as lightweight auth for public endpoints | FK → `tenants`, UQ(tenant, connector, credential_name), unique `token` |
| `flows` | Flow rules: source event → destination action | FK → `tenants`, parent of `flow_executions` |
| `flow_executions` | Audit log of flow executions with results and timing | FK → `flows`, FK → `tenants` |
| `field_mappings` | Per-tenant field mapping overrides (layer 2 of hybrid model) | FK → `tenants` |
| `workflows` | Graph-based workflow definitions with nodes/edges in JSONB | FK → `tenants`, parent of `workflow_executions`, `sync_ledger` |
| `workflow_executions` | Audit log of workflow executions with per-node results and graph snapshots | FK → `workflows`, FK → `tenants` |
| `sync_ledger` | Tracks per-entity sync state for incremental synchronization | FK → `workflows`, FK → `tenants`, UQ(workflow, entity_key) |
| `oauth_tokens` | OAuth2 access/refresh tokens per connector, encrypted at rest (AES-256-GCM) | FK → `tenants`, indexes on (tenant, connector), expires_at, status |
| `webhook_events` | Incoming webhook events with signature verification, dedup, and processing status | FK → `tenants`, indexes on (tenant, connector), external_id, status, received_at |
| `audit_log` | Change history for all entity mutations (create, update, delete, enable, disable) | FK → `tenants`, indexes on (tenant, entity_type, entity_id), created_at |
| `workflow_versions` | Immutable snapshots of workflow nodes/edges/variables for versioning and rollback | FK → `workflows`, FK → `tenants`, UQ(workflow_id, version) |
| `verification_reports` | Results of connector verification runs (3-tier checks) | FK → `tenants` (nullable) |
| `verification_settings` | Singleton scheduler configuration for the verification agent | Standalone (no FK) |

### 4.2 Indexes

All tenant-scoped tables have a B-tree index on `tenant_id` for efficient per-tenant queries (migration `006`):

| Index | Table |
| --- | --- |
| `ix_api_keys_tenant_id` | `api_keys` |
| `ix_connector_instances_tenant_id` | `connector_instances` |
| `ix_credentials_tenant_id` | `credentials` |
| `ix_flows_tenant_id` | `flows` |
| `ix_flow_executions_tenant_id` | `flow_executions` |
| `ix_field_mappings_tenant_id` | `field_mappings` |
| `ix_workflows_tenant_id` | `workflows` |
| `ix_workflow_executions_tenant_id` | `workflow_executions` |
| `ix_sync_ledger_tenant_id` | `sync_ledger` |

Migration `008` adds FK-lookup indexes and fixes cascade behavior:

| Index / Change | Table | Description |
| --- | --- | --- |
| `ix_flow_executions_flow_id` | `flow_executions` | B-tree on `flow_id` for JOIN/filter performance |
| `ix_workflow_executions_workflow_id` | `workflow_executions` | B-tree on `workflow_id` for JOIN/filter performance |
| `flow_executions.flow_id` FK | `flow_executions` | Changed to `ON DELETE SET NULL` (allows flow deletion without losing audit history) |
| `sync_ledger.workflow_id` FK | `sync_ledger` | Changed to `ON DELETE CASCADE` (sync state is meaningless without its workflow) |
| Dropped `ix_sync_ledger_lookup` | `sync_ledger` | Redundant — duplicate of the unique constraint's implicit B-tree index |

Migrations `010`–`013` add tables and indexes for OAuth2, webhooks, audit trail, and workflow versioning:

| Index | Table | Description |
| --- | --- | --- |
| `ix_oauth_tokens_tenant_connector` | `oauth_tokens` | Composite on `(tenant_id, connector_name)` |
| `ix_oauth_tokens_expires_at` | `oauth_tokens` | B-tree on `expires_at` for proactive refresh queries |
| `ix_oauth_tokens_status` | `oauth_tokens` | B-tree on `status` |
| `ix_webhook_events_tenant_connector` | `webhook_events` | Composite on `(tenant_id, connector_name)` |
| `ix_webhook_events_external_id` | `webhook_events` | B-tree on `external_id` for dedup lookups |
| `ix_webhook_events_status` | `webhook_events` | B-tree on `processing_status` |
| `ix_webhook_events_received_at` | `webhook_events` | B-tree on `received_at` |
| `ix_audit_log_tenant_entity` | `audit_log` | Composite on `(tenant_id, entity_type, entity_id)` |
| `ix_audit_log_created_at` | `audit_log` | B-tree on `created_at` |
| `ix_workflow_versions_workflow` | `workflow_versions` | B-tree on `workflow_id` |
| `uq_workflow_versions_workflow_version` | `workflow_versions` | Unique on `(workflow_id, version)` |

RLS policies (`tenant_isolation` + `admin_bypass`) are applied to all four new tables.

Migration `014` adds the `credential_tokens` table:

| Index | Table | Description |
| --- | --- | --- |
| `ix_credential_tokens_token` | `credential_tokens` | B-tree on `token` for fast lookup by opaque token |
| `ix_credential_tokens_tenant_connector` | `credential_tokens` | Composite on `(tenant_id, connector_name)` |
| `uq_credential_tokens_tenant_connector_cred` | `credential_tokens` | Unique on `(tenant_id, connector_name, credential_name)` |

RLS policies (`tenant_isolation` + `admin_bypass`) are applied to `credential_tokens`.

Additional indexes: `verification_reports` has indexes on `run_id`, `connector_name`, `status`, `created_at`. `sync_ledger` has composite indexes on `(workflow_id, entity_key)` and `(workflow_id, sync_status)`.

### 4.3 Row Level Security

Migration `007` enables PostgreSQL Row Level Security (RLS) on all tenant-scoped tables. Migrations `010`–`012` extend RLS to the four new tables (`oauth_tokens`, `webhook_events`, `audit_log`, `workflow_versions`). Two policies are created per table:

| Policy | Condition | Purpose |
| --- | --- | --- |
| `tenant_isolation` | `current_setting('app.current_tenant_id', true) <> '' AND tenant_id = current_setting('app.current_tenant_id', true)::uuid` | Restricts rows to the authenticated tenant. The `true` parameter prevents errors when the variable is unset; the empty-string guard ensures no rows are visible without a tenant context. |
| `admin_bypass` | `current_setting('app.rls_bypass', true) = 'on'` | Allows unrestricted access for background jobs, Kafka consumer, verification agent |

**Session variable lifecycle:**

1. `get_current_tenant()` authenticates via API key (header) or credential token (query param) and executes `SET LOCAL app.current_tenant_id = '<uuid>'` on the shared database session.
2. All subsequent queries in that request are automatically scoped to the tenant by the DB engine.
3. Cross-tenant operations (Kafka event bridge, verification runner, startup provisioning) call `set_rls_bypass(session)` to set `app.rls_bypass = 'on'`.

**Production requirement:** RLS policies apply only to non-owner roles. Production deployments **MUST** use a dedicated application database role (e.g. `pinquark_app`) that does not own the tables. The migration/admin role (table owner) bypasses RLS for schema changes.

Tables excluded from RLS: `tenants` (no `tenant_id`), `api_keys` (queried during authentication before tenant context is available), `verification_reports` (nullable `tenant_id`, used cross-tenant by the verification agent), `verification_settings` (global singleton).

### 4.4 Key design decisions

- **UUID primary keys** on all main tables for distributed ID generation without coordination
- **JSONB columns** for flexible schema: workflow nodes/edges, field mappings, execution results, connector config
- **Tenant isolation** enforced at two layers: application-level `tenant_id` filtering and database-level RLS policies
- **Unique constraints** prevent duplicate connector activations, credentials, and field mappings per tenant
- **Audit trail** via `flow_executions` and `workflow_executions` tables with full input/output snapshots, plus dedicated `audit_log` table for entity change tracking and `workflow_versions` for configuration versioning with rollback

---

## 5. Scaling mechanisms

### 5.1 Horizontal Pod Autoscaler (HPA)

Every integrator in Kubernetes is covered by HPA:


| Parameter                | Value                    | Description                                                 |
| ------------------------ | ------------------------ | ----------------------------------------------------------- |
| `minReplicas`            | 2                        | Minimum for HA (can be reduced to 1 for less critical ones) |
| `maxReplicas`            | 20                       | Maximum during peak load                                    |
| CPU target               | 70%                      | Scale up above 70% CPU usage                                |
| Memory target            | 80%                      | Scale up above 80% memory usage                             |
| Scale-up                 | max 100% or 4 pods / 60s | Fast scale-up                                               |
| Scale-down               | max 25% / 120s           | Cautious scale-down                                         |
| Scale-down stabilization | 300s                     | Prevents flapping                                           |


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


### 5.2 Redis caching

The caching layer offloads the database and speeds up operations:


| What is cached               | Redis key                                           | TTL    | Fallback       |
| ---------------------------- | --------------------------------------------------- | ------ | -------------- |
| Default mappings (YAML)      | `mapping:defaults:{connector}`                      | 600s   | In-memory dict |
| Tenant overrides             | `mapping:overrides:{tenant}:{connector}`            | 300s   | Direct SQL     |
| Connector health status      | `connector:health:{instance_key}`                   | 60s    | Direct poll    |
| Connector rate limit tokens  | `rate_limit:{connector}:{version}:{action}:{tenant}`| N/A    | Allow          |
| Action schemas               | `schema:{connector}:{action}:{tenant}`              | 3600s  | connector.yaml |
| OAuth2 state (anti-CSRF)     | `oauth2:state:{state}`                              | 600s   | —              |
| Webhook dedup                | `webhook:dedup:{connector}:{event}:{external_id}`   | 86400s | —              |


Cache is automatically invalidated when mappings change. When Redis is unavailable, the system continues operating with a fallback to local memory.

### 5.3 PostgreSQL connection pool

Instead of default SQLAlchemy settings, the platform configures a connection pool:


| Parameter       | Value | Env var           | Description                          |
| --------------- | ----- | ----------------- | ------------------------------------ |
| `pool_size`     | 20    | `DB_POOL_SIZE`    | Maintained connections               |
| `max_overflow`  | 30    | `DB_MAX_OVERFLOW` | Additional connections during peak   |
| `pool_timeout`  | 30s   | `DB_POOL_TIMEOUT` | Wait time for a free connection      |
| `pool_recycle`  | 1800s | `DB_POOL_RECYCLE` | Connection refresh interval (30 min) |
| `pool_pre_ping` | true  | --                | Connection verification before use   |


Total: up to 50 active connections (20 base + 30 overflow) per gateway instance.

### 5.4 Kafka tuning

#### Cluster (3 brokers + 3 ZooKeeper)


| Parameter                    | Value |
| ---------------------------- | ----- |
| Broker replicas              | 3     |
| `min.insync.replicas`        | 2     |
| `default.replication.factor` | 3     |
| Storage per broker           | 50Gi  |
| `message.max.bytes`          | 10MB  |
| `num.io.threads`             | 8     |
| `num.network.threads`        | 5     |


#### Topics


| Topic type            | Partitions | Replicas | Retention         |
| --------------------- | ---------- | -------- | ----------------- |
| Data (courier)        | 24         | 3        | 7 days            |
| Data (ecommerce, wms) | 12         | 3        | 7 days            |
| Error                 | 3          | 3        | 30 days           |
| DLQ                   | 3          | 3        | 30 days (compact) |


#### Producer (sending)


| Parameter          | Value | Effect                           |
| ------------------ | ----- | -------------------------------- |
| `compression_type` | lz4   | ~60% size reduction, minimal CPU |
| `linger_ms`        | 50    | Message batching every 50ms      |
| `batch_size`       | 64KB  | Max batch size                   |
| `acks`             | all   | Acknowledgment from all replicas |
| `max_request_size` | 10MB  | Max request size                 |


Available methods:

- `send()` -- single message (await, guaranteed delivery)
- `send_batch()` -- multiple messages at once (concurrent, returns success count)

#### Consumer (receiving)


| Parameter            | Value | Effect                         |
| -------------------- | ----- | ------------------------------ |
| `max_poll_records`   | 500   | Up to 500 messages at once     |
| `fetch_max_bytes`    | 50MB  | Max data per fetch             |
| `enable_auto_commit` | false | Manual commit after processing |


Available modes:

- `consume()` -- one message at a time (backward compatible)
- `consume_batches()` -- batches via `getmany()` (up to 500 msg at once)

### 5.5 Circuit breaker

Protects against cascading failures from external APIs. Each target host (e.g., `api.allegro.pl`, `api-shipx.inpost.pl`) has its own circuit breaker.


| State                   | Transition  | Condition            |
| ----------------------- | ----------- | -------------------- |
| **CLOSED** (normal)     | → OPEN      | 5 consecutive errors |
| **OPEN** (blocking)     | → HALF_OPEN | After 30s timeout    |
| **HALF_OPEN** (testing) | → CLOSED    | 1 successful request |
| **HALF_OPEN**           | → OPEN      | 1 failed request     |



| Parameter                 | Value                                                  |
| ------------------------- | ------------------------------------------------------ |
| Opening threshold         | 5 consecutive errors                                   |
| Reset timeout             | 30s                                                    |
| Max attempts in HALF_OPEN | 1                                                      |
| Prometheus metrics        | `circuit_breaker_state`, `circuit_breaker_trips_total` |


When CB is open, requests return an immediate 503 error instead of waiting for a timeout.

### 5.6 HTTP connection pool

TCP/TLS connection reuse per host instead of creating a new `httpx.AsyncClient` per request:


| Parameter                   | Value | Benefits                          |
| --------------------------- | ----- | --------------------------------- |
| `max_connections`           | 200   | Control of concurrent connections |
| `max_keepalive_connections` | 50    | Eliminates TLS handshake overhead |
| Default timeout             | 30s   | Protection against hanging        |


Integration: circuit breaker per host + connection pool per host = full control over outgoing connections.

### 5.7 Real-time connector health monitoring

Background health poller that checks all active connector instances and stores status in Redis.


| Parameter                   | Value | Env var                          | Description                                        |
| --------------------------- | ----- | -------------------------------- | -------------------------------------------------- |
| Check interval              | 30s   | `HEALTH_CHECK_INTERVAL`          | How often to poll each connector                   |
| Request timeout             | 5.0s  | `HEALTH_CHECK_TIMEOUT`           | Timeout per health check request                   |
| Auto-disable threshold      | 5     | `HEALTH_AUTO_DISABLE_THRESHOLD`  | Consecutive failures before disabling connector    |


Status values: `healthy` (200 OK), `degraded` (timeout or intermittent error), `unhealthy` (repeated failures). After `auto_disable_threshold` consecutive failures, the connector instance is automatically disabled (`is_enabled = false`).

Prometheus metrics: `connector_health_status{name, category}` (gauge), `connector_health_latency_ms{name}` (histogram), `connector_health_consecutive_failures{name}` (gauge).

### 5.8 Per-connector rate limiting

Token-bucket rate limiter in Redis, per connector/action/tenant. Configurable via `connector.yaml` `rate_limits` block.


| Parameter                     | Value      | Env var                        | Description                                |
| ----------------------------- | ---------- | ------------------------------ | ------------------------------------------ |
| Default rate                  | 600/min    | `CONNECTOR_RATE_LIMIT_DEFAULT` | Fallback when connector.yaml has no limits |
| Enabled                       | `true`     | `CONNECTOR_RATE_LIMIT_ENABLED` | Global on/off switch                       |


Rate format: `"{count}/{unit}"` where unit is `s`, `min`, or `h` (e.g., `"100/min"`, `"30/s"`, `"5000/h"`). Per-action overrides via `rate_limits.per_action` in `connector.yaml`.

### 5.9 Workflow scheduler

Cron-based workflow triggers via APScheduler. Workflows with a `trigger` node of type `schedule` are automatically registered at startup.


| Parameter              | Env var                       | Description                                |
| ---------------------- | ----------------------------- | ------------------------------------------ |
| Enabled                | `WORKFLOW_SCHEDULER_ENABLED`  | Enable/disable the scheduler (default: true) |


Cron format: 5-part (`minute hour day month day_of_week`) or crontab string. Timezone-aware via `trigger.config.timezone`.

### 5.10 Rate limiting (per-tenant)

Redis-based sliding window rate limiter:


| Parameter    | Value                                        | Env var                     |
| ------------ | -------------------------------------------- | --------------------------- |
| Limit        | 1000 req/min                                 | `RATE_LIMIT_REQUESTS`       |
| Window       | 60s                                          | `RATE_LIMIT_WINDOW_SECONDS` |
| Identifier   | API key prefix (16 characters)               | --                          |
| Bypass paths | `/health`, `/readiness`, `/metrics`, `/docs` | --                          |


Response headers:


| Header                  | When          | Value                                     |
| ----------------------- | ------------- | ----------------------------------------- |
| `X-RateLimit-Limit`     | Every request | Max requests in the window (e.g., `1000`) |
| `X-RateLimit-Remaining` | Every request | Remaining requests                        |
| `X-RateLimit-Reset`     | Every request | Unix timestamp of window reset            |
| `Retry-After`           | Only 429      | Seconds until retry                       |


---

## 6. Throughput

### 6.1 Estimated performance per component


| Component         | Throughput (per instance)   | Scaling               |
| ----------------- | --------------------------- | --------------------- |
| Platform Gateway  | ~5 000-10 000 req/min       | HPA up to 20 replicas |
| Integrator (REST) | ~3 000-8 000 req/min        | HPA up to 20 replicas |
| Kafka producer    | ~50 000 msg/min (batch)     | Partitioning          |
| Kafka consumer    | ~30 000 msg/min (batch 500) | Consumer groups       |
| Redis cache hit   | ~100 000 ops/min            | Single node / cluster |
| PostgreSQL        | ~5 000 queries/min          | Pool 50 conn          |


### 6.2 Total system throughput


| Scenario              | Gateway (replicas) | Integrators (replicas) | Kafka     | Total throughput           |
| --------------------- | ------------------ | ---------------------- | --------- | -------------------------- |
| Development           | 1                  | 1 per type             | 1 broker  | ~5 000 req/min             |
| UAT                   | 2                  | 2 per type             | 3 brokers | ~20 000 req/min            |
| Production (standard) | 4-6                | 3-5 per type           | 3 brokers | ~100 000 req/min           |
| Production (peak)     | 10-20              | 10-20 per type         | 3 brokers | ~500 000-1 000 000 req/min |


### 6.3 Bottlenecks and their solutions


| Bottleneck              | Symptom                | Metric/log                                        | Solution                                                       |
| ----------------------- | ---------------------- | ------------------------------------------------- | -------------------------------------------------------------- |
| No free DB connections  | `pool_timeout` errors  | SQLAlchemy pool exhausted                         | Increase `DB_POOL_SIZE` / `DB_MAX_OVERFLOW`                    |
| Redis latency           | Slow cache hits        | `integrator_request_duration_seconds` ↑           | Redis Cluster / increase `REDIS_MAX_CONNECTIONS`               |
| Kafka consumer lag      | Growing queue          | Kafka consumer lag metric > 1000                  | More consumers (max = partitions), increase `max_poll_records` |
| External API rate limit | 429 from external API  | `integrator_external_api_calls_total{status=429}` | Respect `Retry-After`, per-connector throttling                |
| Circuit breaker open    | 503 from shared client | `circuit_breaker_state` = 1                       | Wait for reset (30s), investigate error source                 |


---

## 7. Platform configuration

### 7.1 Platform environment variables

#### Application


| Variable    | Default      | Description                                       |
| ----------- | ------------ | ------------------------------------------------- |
| `APP_ENV`   | `production` | Environment: `development` / `production`         |
| `APP_PORT`  | `8080`       | HTTP port                                         |
| `LOG_LEVEL` | `INFO`       | Log level: `DEBUG` / `INFO` / `WARNING` / `ERROR` |


#### PostgreSQL


| Variable          | Default                                                                  | Description                               |
| ----------------- | ------------------------------------------------------------------------ | ----------------------------------------- |
| `DATABASE_URL`    | `postgresql+asyncpg://pinquark:password@postgres:5432/pinquark_platform` | Connection string                         |
| `DB_POOL_SIZE`    | `20`                                                                     | Base number of connections in the pool    |
| `DB_MAX_OVERFLOW` | `30`                                                                     | Additional connections during peak        |
| `DB_POOL_TIMEOUT` | `30`                                                                     | Timeout waiting for a free connection (s) |
| `DB_POOL_RECYCLE` | `1800`                                                                   | Connection refresh every N seconds        |


#### Redis


| Variable                | Default                | Description               |
| ----------------------- | ---------------------- | ------------------------- |
| `REDIS_URL`             | `redis://redis:6379/0` | Redis connection string   |
| `REDIS_MAX_CONNECTIONS` | `50`                   | Max connections in pool   |
| `REDIS_SOCKET_TIMEOUT`  | `5.0`                  | Timeout per operation (s) |
| `REDIS_CACHE_TTL`       | `300`                  | Default cache TTL (s)     |


#### Rate limiting


| Variable                    | Default | Description                        |
| --------------------------- | ------- | ---------------------------------- |
| `RATE_LIMIT_REQUESTS`       | `1000`  | Max requests per tenant per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60`    | Window duration (s)                |


#### Security


| Variable                          | Default      | Description                                             |
| --------------------------------- | ------------ | ------------------------------------------------------- |
| `ENCRYPTION_KEY`                  | *(required)* | AES-256-GCM key for credential vault (base64, 32 bytes) |
| `JWT_SECRET_KEY`                  | *(required)* | JWT signing key                                         |
| `JWT_ALGORITHM`                   | `HS256`      | JWT algorithm                                           |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30`         | JWT token lifetime (min)                                |


#### Connector discovery & schema


| Variable                              | Default          | Description                              |
| ------------------------------------- | ---------------- | ---------------------------------------- |
| `CONNECTOR_DISCOVERY_PATH`            | `/integrators`   | Path to the connectors directory         |
| `SCHEMA_REGISTRY_TTL_SECONDS`        | `3600`           | Redis TTL for cached action schemas      |
| `SCHEMA_REGISTRY_REFRESH_INTERVAL_SECONDS` | `300`      | Background schema refresh interval       |


#### Connector health monitoring


| Variable                         | Default | Description                                             |
| -------------------------------- | ------- | ------------------------------------------------------- |
| `HEALTH_CHECK_INTERVAL`          | `30`    | Seconds between health polls                            |
| `HEALTH_CHECK_TIMEOUT`           | `5.0`   | Timeout per health check request (s)                    |
| `HEALTH_AUTO_DISABLE_THRESHOLD`  | `5`     | Consecutive failures before auto-disabling connector    |


#### Per-connector rate limiting


| Variable                       | Default   | Description                                       |
| ------------------------------ | --------- | ------------------------------------------------- |
| `CONNECTOR_RATE_LIMIT_DEFAULT` | `600/min` | Default rate when connector.yaml has no limits     |
| `CONNECTOR_RATE_LIMIT_ENABLED` | `true`    | Enable/disable per-connector rate limiting         |


#### Workflow scheduler


| Variable                      | Default | Description                    |
| ----------------------------- | ------- | ------------------------------ |
| `WORKFLOW_SCHEDULER_ENABLED`  | `true`  | Enable cron-based triggers     |


#### Platform URLs


| Variable    | Default                | Description                                       |
| ----------- | ---------------------- | ------------------------------------------------- |
| `BASE_URL`  | `http://localhost:8080`| Platform base URL (used for OAuth2 callbacks)     |


#### Demo mode


| Variable    | Default | Description                                                                                 |
| ----------- | ------- | ------------------------------------------------------------------------------------------- |
| `DEMO_MODE` | `false` | Enable self-service tenant registration via `/api/v1/demo/register` (see section 3.4 above) |


### 7.2 Docker Compose (development)

```bash
cd platform
docker compose up -d
```

Starts: platform gateway, PostgreSQL 16, Redis 7.

### 7.3 Docker Compose (production)

```bash
docker compose -f docker-compose.prod.yml up -d
```

Starts: platform, dashboard, PostgreSQL, Redis, and selected connectors (InPost, DHL, DPD, Allegro, WMS).

### 7.4 Kubernetes

Configuration in `k8s/integrators/base/`:


| File              | Purpose             | Key parameters                                                           |
| ----------------- | ------------------- | ------------------------------------------------------------------------ |
| `deployment.yaml` | Deployment template | 2 replicas, CPU 250m-500m, memory 256Mi-512Mi, liveness/readiness probes |
| `hpa.yaml`        | Autoscaling         | 2-20 replicas, CPU target 70%, memory target 80%                         |
| `configmap.yaml`  | Shared variables    | Kafka brokers, log level, service discovery                              |
| `secret.yaml`     | Secrets             | Replaced by CI/CD (never commit values)                                  |


---

## 8. Integration configuration

Detailed documentation of configuration parameters for all 35 connectors (18 couriers, 8 e-commerce, 1 ERP, 1 WMS, 1 AI, 6 other) and credentials management via API can be found in a separate file:

**[CONNECTORS.md](CONNECTORS.md)**

It covers:

- Required and optional parameters for each connector
- Environment variables per integrator
- Account configuration (e.g., Allegro `accounts.yaml`)
- Credentials management via REST API (save, validate, read, delete)
- Connection validation mechanism for each connector

---

## 9. Deployment

### 9.1 Local setup (development)

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

### 9.2 Adding a new connector (zero-impact architecture)

Adding a new connector requires **only two steps** and **zero changes to any platform code**.  The platform discovers connectors automatically by scanning the `integrators/` directory (volume-mounted) for `connector.yaml` manifests at startup.

#### Step 1: Create the connector folder with `connector.yaml`

Create the directory structure under `integrators/`:

```
integrators/{category}/{name}/v1.0.0/
  connector.yaml      # declares everything the platform needs
  Dockerfile
  requirements.txt
  src/
    app.py             # FastAPI application
    ...
```

The `connector.yaml` is the **single source of truth** — it declares the connector's identity, action routing, credential provisioning, credential validation, event/action field schemas, and more. See `AGENTS.md` section 2.1.1 for the full field reference.

Minimal `connector.yaml` example:

```yaml
name: my-connector
category: other
version: 1.0.0
display_name: "My Connector"
description: "Example connector"
interface: generic
service_name: connector-my-connector

actions:
  - document.list
  - document.get

action_routes:
  document.list:
    method: GET
    path: /documents
    query_from_payload: [account_name]
  document.get:
    method: GET
    path: /documents/{document_id}
    query_from_payload: [account_name]

credential_validation:
  required_fields: [api_key]

health_endpoint: /health
docs_url: /docs
```

#### Step 2: Add the service to `docker-compose.prod.yml`

```yaml
connector-my-connector:
  build:
    context: ./integrators/other/my-connector/v1.0.0
  environment:
    APP_ENV: production
    APP_PORT: 8000
  depends_on:
    - platform
  restart: unless-stopped
```

The service name **must** match the `service_name` in `connector.yaml` (or follow the `connector-{name}` convention if omitted).

If the `Dockerfile` references files outside its directory (e.g. `shared/python`), use root build context:

```yaml
connector-my-connector:
  build:
    context: .
    dockerfile: integrators/other/my-connector/v1.0.0/Dockerfile
```

#### What you do NOT need to modify

- `platform/core/action_dispatcher.py` — reads `action_routes` and `credential_provisioning` from `connector.yaml`
- `platform/api/gateway.py` — reads `credential_validation` from `connector.yaml`
- `platform/verification-agent/src/discovery.py` — reads `service_name` from `connector.yaml`
- `platform/verification-agent/src/checks/functional.py` — auto-discovers test modules by convention

**No platform container rebuild is needed.** The platform container mounts the `integrators/` directory as a volume and re-scans it on startup. Simply restart the platform after deploying the new connector:

```bash
docker compose -f docker-compose.prod.yml up -d --build connector-my-connector
docker compose -f docker-compose.prod.yml restart platform
```

#### Verification

After startup, verify:

1. **Health check**: `curl http://connector-my-connector:8000/health` from inside the Docker network
2. **Platform discovery**: the connector should appear in `GET /api/v1/connectors`
3. **Workflow/Flow**: it can be used as an action target in workflows and flows
4. **Logs**: `docker compose -f docker-compose.prod.yml logs connector-my-connector`

---

### 9.3 Kubernetes (UAT/production)

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

### 9.4 Health check

Every component exposes:


| Endpoint         | Description                      | Auth             |
| ---------------- | -------------------------------- | ---------------- |
| `GET /health`    | Liveness: is the process running | No               |
| `GET /readiness` | Readiness: are dependencies OK   | No               |
| `GET /metrics`   | Prometheus metrics               | Internal network |


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

### 9.5 Monitoring

Prometheus metrics available at `/metrics`:


| Metric                                     | Type      | Description                              |
| ------------------------------------------ | --------- | ---------------------------------------- |
| `integrator_requests_total`                | Counter   | Requests per endpoint/status             |
| `integrator_request_duration_seconds`      | Histogram | Latency per endpoint                     |
| `integrator_external_api_calls_total`      | Counter   | External API calls                       |
| `integrator_external_api_duration_seconds` | Histogram | External API latency                     |
| `circuit_breaker_state`                    | Gauge     | CB state (0=closed, 1=open, 2=half_open) |
| `circuit_breaker_trips_total`              | Counter   | Number of times CB opened                |
| `connector_health_status`                  | Gauge     | Health status (0=unhealthy, 1=degraded, 2=healthy) |
| `connector_health_latency_ms`             | Histogram | Health check latency per connector       |
| `connector_health_consecutive_failures`    | Gauge     | Consecutive health check failures        |
| `webhook_events_received_total`            | Counter   | Incoming webhook events                  |
| `webhook_events_processed_total`           | Counter   | Successfully processed webhooks          |
| `webhook_events_failed_total`              | Counter   | Failed webhook processing                |
| `webhook_processing_duration_seconds`      | Histogram | Webhook processing latency               |



# Open Integration Platform — Roadmap & Improvement Plan

**Author**: Platform Team  
**Date**: 2026-03-11  
**Status**: Draft  
**Context**: Competitive analysis vs enterprise iPaaS platforms (Workato, Tray.io, Make) and internal technical audit

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Assessment](#2-current-state-assessment)
3. [Product & UX Improvements](#3-product--ux-improvements)
4. [Technical Improvements](#4-technical-improvements)
5. [Implementation Phases](#5-implementation-phases)
6. [Appendix: Competitive Positioning](#6-appendix-competitive-positioning)

---

## 1. Executive Summary

The Open Integration Platform has a strong architectural foundation: manifest-driven connectors, a DAG-based workflow engine with 16 node types, AES-256-GCM credential encryption, Row-Level Security, circuit breaker, hybrid field mapping, async stack (FastAPI + asyncpg), and a 3-tier verification agent. With 37 connectors across 6 categories, the core integration engine is production-capable.

However, to compete with enterprise iPaaS platforms and accelerate adoption, improvements are needed in two areas:

- **Product & UX** — connector catalog, flow templates, onboarding, positioning, AI integration
- **Technical** — Connector SDK, OAuth2 lifecycle, webhook ingestion, real-time health, per-connector rate limiting, execution replay, schema registry, audit trail

This document details every planned improvement, its rationale, technical design, and priority.

---

## 2. Current State Assessment

### 2.1 What we have (strengths)

| Area | Current Implementation |
|------|----------------------|
| **Architecture** | Any-to-any peer topology, manifest-driven dispatch, zero platform code per connector |
| **Workflow Engine** | DAG-based, 16 node types (action, condition, switch, think, transform, filter, delay, loop, merge, parallel, aggregate, http_request, set_variable, response, trigger) |
| **Flow Engine** | Source event → field mapping → destination action, filter matching, JMESPath transforms |
| **Credential Management** | AES-256-GCM vault, per-tenant, per-connector, named credential sets |
| **Field Mapping** | Hybrid model: file-based defaults + DB overrides, Redis cache (TTL 300-600s) |
| **Resilience** | Circuit breaker (5 failures → OPEN, 30s reset), exponential backoff retries |
| **Rate Limiting** | Redis sliding window, per-tenant (1000 req/min default) |
| **Multi-tenancy** | PostgreSQL Row-Level Security, API key auth, tenant isolation |
| **Observability** | Prometheus metrics, structured JSON logging, PII redaction |
| **Sync State** | Deduplication via content hash, entity keys, retry tracking in sync_ledger |
| **Verification** | 3-tier automated testing: infra → auth → functional, scheduled + on-demand |
| **Connectors** | 37 connectors: 18 courier, 8 e-commerce, 1 WMS, 1 ERP, 1 AI, 6 other |
| **Dashboard** | Angular app + `@pinquark/integrations` npm library, workflow canvas, flow designer |
| **Infrastructure** | Docker Compose (prod/VPS), Kubernetes manifests, Strimzi Kafka, Nginx Ingress |

### 2.2 What we lack (gaps)

| Gap | Impact |
|-----|--------|
| No Connector SDK / base framework | Slow connector development, inconsistent implementations |
| No OAuth2 lifecycle management | Manual token refresh, broken e-commerce integrations |
| No webhook ingestion layer | No signature verification, no event dedup at ingestion |
| No real-time connector health | Only batch verification (7-day cycle), no live status |
| No per-connector rate limiting | Risk of hitting external API limits in production |
| No execution replay / re-run | Difficult debugging, no re-run from failed node |
| No dynamic schema registry | Can't handle custom fields in ERP/e-commerce |
| No audit trail | No change history, no rollback, compliance risk |
| No connector catalog (product) | Hard to discover and evaluate connectors |
| No flow templates | Every integration starts from scratch |
| No guided onboarding | High time-to-first-integration |

---

## 3. Product & UX Improvements

### 3.1 Connector Catalog

**Problem**: Connectors are documented only in `connector.yaml` manifests and `docs/CONNECTORS.md`. There is no browsable, filterable product catalog that helps users discover and evaluate connectors.

**Solution**: Build a public connector catalog page in the dashboard with:

| Feature | Description |
|---------|-------------|
| Connector cards | Logo, name, category, country, status badge (stable/beta/planned), version |
| Filtering | By category, country, capability, auth type, status |
| Search | Full-text search across connector names and descriptions |
| Detail page | Per-connector page with: supported events, actions, config schema, auth method, sandbox availability, sample flows, API docs link |
| Capability matrix | Table showing which capabilities each connector supports |
| Status indicators | Real-time health status (green/yellow/red) when connected to live platform |

**Data source**: `ConnectorRegistry` already provides all metadata from `connector.yaml`. The catalog is a UI layer over existing data.

**Files to create/modify**:
- `platform/dashboard/projects/integrations-lib/src/lib/components/connector-catalog/` — new component
- `platform/dashboard/projects/dashboard-app/src/app/pages/catalog/` — new page
- `platform/api/gateway.py` — enhance `GET /api/v1/connectors` with filtering/search params

---

### 3.2 Flow & Workflow Template Library

**Problem**: Every integration starts from scratch. Users must manually configure source, destination, mapping, and error handling.

**Solution**: Pre-built templates for common integration scenarios.

**Template categories**:

| Category | Example Templates |
|----------|-------------------|
| **Shipping automation** | Allegro → InPost: create shipment + status sync |
| **Order sync** | Shopify → WAPRO: order → ERP document |
| **Multi-carrier** | BaseLinker → DHL/DPD/GLS: carrier selection + shipment |
| **Returns** | InPost return → Allegro order status update |
| **Inventory sync** | ERP → marketplace stock levels |
| **Document sync** | ERP → WMS document exchange |
| **Notifications** | Shipment status → Slack/Email notification |

**Technical design**:
- Templates stored as JSON files in `platform/templates/` directory
- Each template: `{ name, description, category, tags, source_connector, destination_connector, nodes, edges, field_mapping, variables }`
- API: `GET /api/v1/templates`, `POST /api/v1/templates/{id}/instantiate` (creates workflow from template)
- Dashboard: template gallery with preview, one-click instantiation, pre-filled credentials prompt

**Files to create**:
- `platform/templates/` — template JSON files
- `platform/api/template_router.py` — FastAPI router for template CRUD
- `platform/dashboard/.../template-gallery/` — Angular component

---

### 3.3 Guided Onboarding Wizard

**Problem**: New users face a steep learning curve. No guided path from "sign up" to "first working integration".

**Solution**: Step-by-step onboarding wizard in the dashboard.

**Wizard flow**:
1. **Choose your scenario** — select from common use cases or "custom"
2. **Select source system** — pick connector (e.g., Allegro)
3. **Select destination system** — pick connector (e.g., InPost)
4. **Connect credentials** — enter API keys / OAuth2 flow
5. **Test connection** — verify both systems are reachable
6. **Configure mapping** — pre-filled from template, allow customization
7. **Test with sample data** — dry-run with mock event
8. **Activate** — enable the flow/workflow

**Technical design**:
- Multi-step Angular component with state machine
- Each step validates before allowing next
- Integrates with: ConnectorRegistry (step 2-3), CredentialValidator (step 5), FlowEngine dry-run (step 7)
- Progress saved to `localStorage` (resume if interrupted)

---

### 3.4 Use-Case-Based Navigation

**Problem**: The platform is organized by technical concepts (connectors, flows, workflows). Users think in terms of business problems.

**Solution**: Multiple entry points to the platform.

**Entry points**:

| Entry | Examples |
|-------|----------|
| **By industry** | E-commerce, Logistics, Fulfillment, Retail, ERP/WMS |
| **By problem** | "Connect marketplace to courier", "Sync orders to ERP", "Automate returns", "Sync inventory" |
| **By system** | Allegro, BaseLinker, Shopify, WAPRO, InPost, DPD, SAP, WooCommerce |
| **By action** | "Create shipment", "Sync orders", "Get label", "Track status" |

**Implementation**: Landing pages in dashboard that filter connector catalog and template library by context. No new backend needed — pure UI routing and filtering.

---

### 3.5 AI Integration in Workflows

**Problem**: The AI connector (Gemini) exists as a standalone integrator, but AI is not woven into the platform experience.

**Solution**: Expose AI as a platform-level capability, not just another connector.

| Feature | Description |
|---------|-------------|
| **AI-assisted field mapping** | Suggest mappings based on field names and types using LLM |
| **AI carrier recommendation** | Given order data, recommend optimal courier (already in AI connector — surface in flow builder) |
| **AI error explanation** | When a flow fails, use AI to explain the error in plain language and suggest fix |
| **AI workflow generator** | Describe integration in natural language → generate workflow DAG (already exists as `WorkflowAiGenerate` endpoint — improve and promote) |
| **AI data validation** | "Think" node in workflows for data quality checks |

**Already exists**: `workflow-ai-chat` component in dashboard, `POST /api/v1/workflows/ai/generate` endpoint. Focus on improving quality and discoverability.

---

### 3.6 Platform Positioning & Messaging

**Problem**: The platform is described in architectural terms (any-to-any topology, hybrid mapping, manifest-driven). Users need business value language.

**Recommended messaging framework**:

| Current (technical) | Recommended (business) |
|---------------------|----------------------|
| Any-to-any topology | "Connect any system to any other — no central bottleneck" |
| Manifest-driven connectors | "Add new integrations without changing the platform" |
| Version isolation | "Upgrade connectors without breaking existing integrations" |
| Verification agent | "Every integration is automatically tested for health and correctness" |
| AES-256-GCM encryption | "Enterprise-grade credential security" |
| On-premise agent | "Connect to local ERP systems behind your firewall" |
| Self-hosted option | "Full control — deploy on your infrastructure" |
| `@pinquark/integrations` | "Embed integrations directly in your application" |

**Key differentiators to emphasize**:
- Polish and regional system support (InPost, Allegro, WAPRO, BaseLinker, IdoSell, Poczta Polska)
- Self-hosted + SaaS flexibility
- Embeddable Angular library
- Open-source (Apache 2.0)
- Deep logistics/courier domain expertise (18 courier connectors)

---

## 4. Technical Improvements

### 4.1 Connector SDK `[DONE]`

**Priority**: 1 (Critical)  
**Effort**: Medium (2-3 weeks)  
**Impact**: 3-5x faster connector development, enforced standards

**Problem**: Each connector is a standalone FastAPI app. Developers must manually implement health endpoints, account management, error handling, metrics, and structured logging. This leads to inconsistency and slow development.

**Solution**: Python package `pinquark-connector-sdk` that provides a base framework.

**Design**:

```python
from pinquark_connector_sdk import ConnectorApp, action, trigger, webhook

class ShopifyConnector(ConnectorApp):
    name = "shopify"
    category = "ecommerce"
    version = "1.0.0"

    class Config:
        required_credentials = ["api_key", "shop_domain"]
        rate_limits = {"default": "40/s"}
        oauth2 = {
            "authorization_url": "https://{shop_domain}/admin/oauth/authorize",
            "token_url": "https://{shop_domain}/admin/oauth/access_token",
            "scopes": ["read_orders", "write_orders"],
        }

    @action(
        name="order.list",
        input_schema=OrderListInput,
        output_schema=OrderListOutput,
    )
    async def list_orders(self, params: OrderListInput) -> OrderListOutput:
        response = await self.http.get(f"/admin/api/2024-01/orders.json", params=params.dict())
        return OrderListOutput.parse_obj(response.json())

    @webhook(
        name="order.created",
        topic="orders/create",
        signature_header="X-Shopify-Hmac-Sha256",
    )
    async def on_order_created(self, payload: dict) -> dict:
        return payload

    @trigger(name="order.poll", interval_seconds=60)
    async def poll_orders(self, since: datetime) -> list[dict]:
        ...

    async def test_connection(self) -> bool:
        response = await self.http.get("/admin/api/2024-01/shop.json")
        return response.status_code == 200
```

**What the SDK provides automatically**:
- `GET /health`, `GET /readiness`, `GET /docs` endpoints
- `POST /accounts`, `GET /auth/{account}/status` account management
- Prometheus metrics (`connector_requests_total`, `connector_external_api_duration_seconds`)
- Structured JSON logging with `trace_id`
- Circuit breaker per external host
- Rate limiting (token bucket)
- `connector.yaml` auto-generation from decorators
- Webhook signature verification
- OAuth2 token management

**Files to create**:
- `sdk/python/pinquark_connector_sdk/` — package root
- `sdk/python/pinquark_connector_sdk/app.py` — `ConnectorApp` base class
- `sdk/python/pinquark_connector_sdk/decorators.py` — `@action`, `@trigger`, `@webhook`
- `sdk/python/pinquark_connector_sdk/auth.py` — OAuth2Manager, credential handling
- `sdk/python/pinquark_connector_sdk/http.py` — pre-configured httpx client with circuit breaker
- `sdk/python/pinquark_connector_sdk/health.py` — health/readiness auto-endpoints
- `sdk/python/pinquark_connector_sdk/metrics.py` — Prometheus auto-instrumentation
- `sdk/python/pinquark_connector_sdk/testing.py` — test utilities, mock server

**Migration path**: New connectors use the SDK. Existing connectors migrated incrementally (SDK wraps existing FastAPI apps).

---

### 4.2 OAuth2 Lifecycle Manager

**Priority**: 2 (Critical for e-commerce)  
**Effort**: Medium (1-2 weeks)  
**Impact**: Reliable e-commerce integrations (Allegro, Shopify, Amazon)

**Problem**: The credential vault stores tokens statically. No automatic refresh, no OAuth2 authorization flow, no token rotation. E-commerce connectors (Allegro, Shopify, Amazon) require OAuth2 with refresh tokens that expire.

**Solution**: Dedicated OAuth2 management module.

**New database table**:

```
oauth_tokens
├── id (UUID, PK)
├── tenant_id (UUID, FK → tenants)
├── connector_name (VARCHAR 100)
├── credential_name (VARCHAR 100, default "default")
├── provider (VARCHAR 50) — "allegro", "shopify", etc.
├── access_token_encrypted (TEXT) — AES-256-GCM
├── refresh_token_encrypted (TEXT) — AES-256-GCM
├── token_type (VARCHAR 20) — "bearer"
├── scope (TEXT)
├── expires_at (TIMESTAMPTZ)
├── refresh_expires_at (TIMESTAMPTZ, nullable)
├── last_refreshed_at (TIMESTAMPTZ)
├── refresh_count (INTEGER, default 0)
├── status (VARCHAR 20) — "active", "expired", "revoked", "error"
├── last_error (TEXT, nullable)
├── created_at (TIMESTAMPTZ)
├── updated_at (TIMESTAMPTZ)
```

**Components**:

| Component | Responsibility |
|-----------|---------------|
| `core/oauth2_manager.py` | Token storage, retrieval, encryption. Authorization URL generation, callback handling, token exchange. |
| `core/oauth2_refresher.py` | Background task (asyncio): checks tokens expiring in next 5 minutes, refreshes proactively. Runs every 60 seconds. |
| `api/oauth2_routes.py` | `GET /api/v1/oauth2/{connector}/authorize` — redirect to provider. `GET /api/v1/oauth2/callback` — handle callback. `POST /api/v1/oauth2/{connector}/refresh` — manual refresh. |

**connector.yaml extension**:

```yaml
credential_validation:
  oauth2:
    authorization_url: "https://allegro.pl/auth/oauth/authorize"
    token_url: "https://allegro.pl/auth/oauth/token"
    scopes: ["allegro:api:orders:read", "allegro:api:orders:write"]
    pkce: true
    refresh_before_expiry_seconds: 300
```

**Integration with existing CredentialVault**: OAuth2Manager uses CredentialVault for encryption. When an action needs credentials, the vault checks for OAuth2 tokens first, refreshes if needed, then returns the current access_token.

---

### 4.3 Webhook Ingestion Service

**Priority**: 5 (Important)  
**Effort**: Medium (1-2 weeks)  
**Impact**: Event-driven integrations, external system notifications

**Problem**: No dedicated webhook receiver. Events come through Kafka or REST polling. External systems (Allegro, Shopify, InPost) push webhooks, but there's no standardized way to receive, verify, and route them.

**Solution**: Webhook ingestion layer in the API gateway.

**Design**:

```
External System → POST /api/v1/webhooks/{connector}/{event}
                      │
                      ├── 1. Signature verification (HMAC, provider-specific)
                      ├── 2. Idempotency check (Redis: webhook_id dedup, TTL 24h)
                      ├── 3. Payload normalization
                      ├── 4. Persist to webhook_events table
                      ├── 5. Trigger matching flows/workflows
                      └── 6. Return 200 OK (< 500ms)
```

**New database table**:

```
webhook_events
├── id (UUID, PK)
├── tenant_id (UUID, FK → tenants)
├── connector_name (VARCHAR 100)
├── event_type (VARCHAR 100)
├── external_id (VARCHAR 500, nullable) — provider's event/message ID
├── payload (JSONB)
├── headers (JSONB) — stored for debugging
├── signature_valid (BOOLEAN)
├── processing_status (VARCHAR 20) — "received", "processing", "processed", "failed", "dead_letter"
├── error (TEXT, nullable)
├── retry_count (INTEGER, default 0)
├── received_at (TIMESTAMPTZ)
├── processed_at (TIMESTAMPTZ, nullable)
```

**connector.yaml extension**:

```yaml
webhooks:
  order.created:
    signature_header: "X-Allegro-Signature"
    signature_algorithm: "hmac-sha256"
    signature_key_field: "webhook_secret"  # from credentials
  shipment.status_changed:
    signature_header: "X-InPost-Signature"
    signature_algorithm: "hmac-sha256"
```

**Features**:
- Per-connector signature verification (HMAC-SHA256, RSA, provider-specific)
- Idempotency via `external_id` dedup in Redis (24h TTL)
- Async processing — return 200 immediately, process in background
- Dead Letter Queue — failed webhooks stored for manual retry
- Webhook replay — `POST /api/v1/webhooks/{id}/replay`
- Dashboard: webhook event log with filtering, payload inspection, manual retry

---

### 4.4 Real-Time Connector Health `[DONE]`

**Priority**: 3 (High)  
**Effort**: Low (3-5 days)  
**Impact**: Operational visibility, proactive issue detection

**Problem**: Verification agent runs every 7 days (batch). No real-time health status for connectors. Operators cannot see which connectors are healthy right now.

**Solution**: Lightweight health poller with Redis-backed status store.

**Design**:

```
Background Task (every 30s)
    │
    ├── For each active ConnectorInstance:
    │     GET http://connector-{name}:8000/health
    │     ├── 200 → status: healthy, record latency
    │     ├── timeout → status: degraded, increment failure_count
    │     └── error → status: unhealthy, increment failure_count
    │
    ├── Store in Redis:
    │     connector:health:{name} = {
    │       status, latency_ms, last_check, error_rate_5m,
    │       consecutive_failures, last_error
    │     }
    │
    └── Auto-disable after 5 consecutive failures:
          UPDATE connector_instances SET is_enabled = false
          WHERE consecutive_failures >= 5
```

**New components**:

| Component | Responsibility |
|-----------|---------------|
| `core/connector_health.py` | Background health poller, Redis store, auto-disable logic |
| `api/gateway.py` enhancement | `GET /api/v1/connectors/{name}/health` — real-time status |

**Prometheus metrics**:

```
connector_health_status{name, category}     — gauge (0=unhealthy, 1=degraded, 2=healthy)
connector_health_latency_ms{name}           — histogram
connector_health_consecutive_failures{name} — gauge
```

**Dashboard integration**: Green/yellow/red indicator on connector list and detail pages.

---

### 4.5 Per-Connector Rate Limiting `[DONE]`

**Priority**: 4 (High)  
**Effort**: Low (3-5 days)  
**Impact**: Production stability, prevent external API bans

**Problem**: Rate limiting is per-tenant only (1000 req/min). External APIs have their own rate limits (e.g., Allegro: 9000 req/min, InPost: 100 req/min). The platform doesn't respect these.

**Solution**: Token bucket rate limiter per connector, configurable via `connector.yaml`.

**connector.yaml extension**:

```yaml
rate_limits:
  global: 100/min
  per_action:
    shipment.create: 30/min
    label.get: 60/min
    pickup_points.list: 10/min
```

**Design**:

```
ActionDispatcher.dispatch_action()
    │
    ├── 1. Check per-connector rate limit (Redis token bucket)
    │     Key: rate_limit:{connector}:{action}:{tenant}
    │     ├── tokens available → proceed
    │     └── no tokens → queue or return 429 with retry_after
    │
    ├── 2. Execute action on connector
    │
    └── 3. Handle 429 from connector
          ├── Read Retry-After header
          ├── Wait and retry (up to max_retries)
          └── Propagate 429 to caller if retries exhausted
```

**Components**:

| Component | Responsibility |
|-----------|---------------|
| `core/connector_rate_limiter.py` | Token bucket implementation in Redis per connector/action/tenant |
| `core/action_dispatcher.py` enhancement | Check rate limit before dispatch, handle 429 responses |

**Redis keys**:

```
rate_limit:{connector}:{action}:tokens   — current token count
rate_limit:{connector}:{action}:last     — last refill timestamp
```

---

### 4.6 Workflow Engine Enhancements

**Priority**: 6 (Medium)  
**Effort**: Medium (2-3 weeks)  
**Impact**: Complex integration scenarios, composability

**Problem**: Workflow engine has 16 node types but lacks sub-workflow composition, dedicated error handling branches, batch processing, and scheduled triggers.

#### 4.6.1 Sub-Workflow Node

Execute another workflow as a step in the current workflow, passing data in and receiving data out.

```python
# New node type: "sub_workflow"
{
    "id": "node-5",
    "type": "sub_workflow",
    "config": {
        "workflow_id": "uuid-of-child-workflow",
        "input_mapping": {
            "order_id": "{{data.order.id}}",
            "customer": "{{data.order.buyer}}"
        },
        "timeout_seconds": 60
    }
}
```

**Implementation**: `WorkflowEngine._exec_sub_workflow()` — creates a child execution, runs it, returns output to parent context. Guard against circular references (max depth).

#### 4.6.2 Error Handler Node

Dedicated error-handling branch that receives error context and can: log, notify, transform, retry with different config, or route to fallback connector.

```python
# New node type: "error_handler"
{
    "id": "node-err",
    "type": "error_handler",
    "config": {
        "catch_from": ["node-3", "node-4"],  # which nodes to catch errors from
        "actions": [
            {"type": "notify", "channel": "slack", "message": "Flow failed: {{error}}"},
            {"type": "set_variable", "name": "fallback_used", "value": true}
        ]
    }
}
```

**Implementation**: When a node in `catch_from` fails, instead of stopping the workflow, route to the error_handler node. The error context (`error`, `failed_node_id`, `failed_node_output`) is available in the handler.

#### 4.6.3 Batch Processing Node

Process a list of items with configurable concurrency and throttling.

```python
# New node type: "batch"
{
    "id": "node-batch",
    "type": "batch",
    "config": {
        "source": "{{data.orders}}",
        "concurrency": 5,
        "throttle_ms": 100,
        "on_item_error": "continue",  # or "stop"
        "body_nodes": ["node-6", "node-7"]  # sub-graph to execute per item
    }
}
```

**Implementation**: Iterate over list, execute sub-graph per item with `asyncio.Semaphore(concurrency)` and throttle delay. Collect results into array. Report per-item success/failure.

#### 4.6.4 Schedule Trigger

Cron-like trigger for periodic workflows (e.g., sync inventory every hour).

```python
# Trigger config extension
{
    "type": "trigger",
    "config": {
        "trigger_type": "schedule",
        "cron": "0 */1 * * *",  # every hour
        "timezone": "Europe/Warsaw"
    }
}
```

**Implementation**: APScheduler `CronTrigger` in platform, registered at workflow activation. On trigger, execute workflow with `trigger_data: { scheduled_at, cron_expression }`.

---

### 4.7 Execution Replay & Debugging

**Priority**: 7 (Medium)  
**Effort**: Medium (1-2 weeks)  
**Impact**: Developer experience, faster issue resolution

**Problem**: Workflow executions store `node_results` and `context_snapshot`, but there's no way to: replay an execution, re-run from a failed node, or dry-run with test data.

**Solution**:

#### 4.7.1 Per-Edge Data Snapshots

Currently, `node_results` stores output per node. Enhance to also store **input** per node (the data as it enters the node):

```json
{
    "node_id": "node-3",
    "node_type": "action",
    "label": "Create Shipment",
    "status": "success",
    "input": { "receiver": "...", "parcels": [...] },
    "output": { "shipment_id": "123", "tracking": "..." },
    "duration_ms": 340
}
```

#### 4.7.2 Re-Run from Node

API endpoint to re-run a workflow execution starting from a specific node:

```
POST /api/v1/workflows/{id}/executions/{exec_id}/rerun
Body: { "from_node_id": "node-3", "override_data": { ... } }
```

**Implementation**: Load `context_snapshot` from the original execution, restore state up to `from_node_id`, then continue execution from there. Optionally override input data.

#### 4.7.3 Dry-Run / Test Mode

Execute a workflow with mock data without side effects:

```
POST /api/v1/workflows/{id}/test
Body: { "trigger_data": { ... }, "dry_run": true }
```

**Implementation**: In dry-run mode, action nodes return mock responses (from `connector.yaml` `output_fields` schema) instead of calling real connectors. All other nodes (condition, transform, filter) execute normally.

#### 4.7.4 Execution Diff

Compare two executions side-by-side to understand what changed:

```
GET /api/v1/workflows/{id}/executions/diff?exec_a={id1}&exec_b={id2}
```

Returns per-node comparison: what was different in input, output, status, duration.

---

### 4.8 Dynamic Schema Registry

**Priority**: 9 (Medium)  
**Effort**: Medium (2 weeks)  
**Impact**: Custom field support for ERP/e-commerce

**Problem**: `event_fields`, `action_fields`, `output_fields` in `connector.yaml` are static. External systems have dynamic schemas (Allegro custom parameters, Shopify metafields, ERP custom columns).

**Solution**: Schema Registry that caches dynamic schemas from connectors.

**Design**:

```
Dashboard / Flow Builder
    │
    ├── GET /api/v1/connectors/{name}/schema/{action}
    │     │
    │     ├── Check Redis cache: schema:{connector}:{action}:{tenant}
    │     │     ├── cache hit → return
    │     │     └── cache miss ↓
    │     │
    │     ├── Call connector: GET http://connector-{name}:8000/schema/{action}
    │     │     (connector queries external API for current schema)
    │     │
    │     ├── Merge with static schema from connector.yaml
    │     │
    │     ├── Cache in Redis (TTL 1h)
    │     │
    │     └── Return merged schema
    │
    └── Schema change detection:
          Background job compares cached schema with fresh fetch.
          If changed → notify tenant, invalidate mapping cache.
```

**Connector SDK integration**: The `@action` decorator supports `dynamic_schema=True`, which tells the SDK to expose a `/schema/{action}` endpoint that queries the external API.

**New components**:

| Component | Responsibility |
|-----------|---------------|
| `core/schema_registry.py` | Fetch, cache, merge, diff schemas |
| `api/gateway.py` enhancement | `GET /api/v1/connectors/{name}/schema/{action}` |

---

### 4.9 Audit Trail & Configuration Versioning

**Priority**: 10 (Medium)  
**Effort**: Low (1 week)  
**Impact**: Compliance, rollback capability, change tracking

**Problem**: No history of who changed what and when. No rollback capability. `updated_at` is the only change indicator.

**Solution**: Audit log table and workflow versioning.

**New database table**:

```
audit_log
├── id (UUID, PK)
├── tenant_id (UUID, FK → tenants)
├── user_id (VARCHAR 100, nullable) — API key prefix or user identifier
├── entity_type (VARCHAR 50) — "workflow", "flow", "credential", "connector_instance"
├── entity_id (UUID)
├── action (VARCHAR 20) — "create", "update", "delete", "enable", "disable"
├── old_value (JSONB, nullable) — state before change
├── new_value (JSONB, nullable) — state after change
├── ip_address (VARCHAR 45, nullable)
├── created_at (TIMESTAMPTZ)
```

**Workflow versioning**:

```
workflow_versions
├── id (UUID, PK)
├── workflow_id (UUID, FK → workflows)
├── version (INTEGER)
├── nodes (JSONB)
├── edges (JSONB)
├── variables (JSONB)
├── created_by (VARCHAR 100)
├── created_at (TIMESTAMPTZ)
```

**API endpoints**:

```
GET  /api/v1/audit-log?entity_type=workflow&entity_id={id}  — change history
GET  /api/v1/workflows/{id}/versions                        — version list
GET  /api/v1/workflows/{id}/versions/{version}              — specific version
POST /api/v1/workflows/{id}/rollback?version={n}            — restore version
```

**Implementation**: Middleware/hook in gateway that captures before/after state on every mutation endpoint. Workflow versioning: snapshot nodes/edges/variables on every `PUT /workflows/{id}`.

---

### 4.10 Visual Field Mapper

**Priority**: 8 (Medium)  
**Effort**: High (3-4 weeks)  
**Impact**: UX for non-technical users

**Problem**: Field mapping is configured as JSON arrays. No visual interface for mapping fields.

**Solution**: Drag-and-drop field mapper in the Angular dashboard.

**Design**:

```
┌─────────────────────┐         ┌─────────────────────┐
│   Source Schema      │         │   Dest. Schema       │
│                      │         │                      │
│  ● order.id         │─────────│  ● shipment.ref     │
│  ● order.buyer.name │─────────│  ● receiver.name    │
│  ● order.buyer.addr │─────────│  ● receiver.address │
│  ● order.items[]    │─────────│  ● parcels[]        │
│  ● order.total      │    ┌────│  ● declared_value   │
│                      │    │   │                      │
└──────────────────────┘    │   └──────────────────────┘
                            │
                    ┌───────┴───────┐
                    │  Transform:   │
                    │  multiply(x,  │
                    │    100)       │
                    └───────────────┘
```

**Features**:
- Left panel: source schema (from Schema Registry or connector.yaml)
- Right panel: destination schema
- Drag lines between fields to create mappings
- Click on a line to add transform expression
- AI-assisted suggestions: "Auto-map" button that uses field name similarity + AI
- Test mapping: input sample data, see output
- Expression builder for transforms: `concat()`, `split()`, `format_date()`, `lookup()`, `multiply()`, `if_else()`

**Technical approach**:
- Angular component using SVG or Canvas for connection lines
- Expression language parser (simple DSL, not full programming language)
- Schema fetched from Schema Registry (4.8) or static `connector.yaml`

---

## 5. Implementation Phases

### Phase 1: Foundation (Weeks 1-4) `[DONE]`

Focus: Production stability and developer velocity.

| # | Feature | Section | Effort | Status |
|---|---------|---------|--------|--------|
| 1 | Connector SDK (core + 1 connector migration) | 4.1 | 2-3 weeks | **DONE** |
| 2 | Real-time connector health | 4.4 | 3-5 days | **DONE** |
| 3 | Per-connector rate limiting | 4.5 | 3-5 days | **DONE** |

**Outcome**: Faster connector development, live health monitoring, production-safe rate limiting.

### Phase 2: Auth & Events (Weeks 5-8)

Focus: Reliable credentials and event-driven architecture.

| # | Feature | Section | Effort |
|---|---------|---------|--------|
| 4 | OAuth2 lifecycle manager | 4.2 | 1-2 weeks |
| 5 | Webhook ingestion service | 4.3 | 1-2 weeks |
| 6 | Audit trail + versioning | 4.9 | 1 week |

**Outcome**: Reliable OAuth2 for e-commerce, webhook-driven flows, change tracking.

### Phase 3: Engine & Debug (Weeks 9-12)

Focus: Workflow power and developer experience.

| # | Feature | Section | Effort |
|---|---------|---------|--------|
| 7 | Sub-workflow + error handler nodes | 4.6.1, 4.6.2 | 1-2 weeks |
| 8 | Batch processing + schedule trigger | 4.6.3, 4.6.4 | 1 week |
| 9 | Execution replay, re-run, dry-run | 4.7 | 1-2 weeks |

**Outcome**: Composable workflows, better error handling, debugging capabilities.

### Phase 4: Product & UX (Weeks 13-18)

Focus: User-facing experience.

| # | Feature | Section | Effort |
|---|---------|---------|--------|
| 10 | Connector catalog | 3.1 | 1-2 weeks |
| 11 | Template library | 3.2 | 1-2 weeks |
| 12 | Onboarding wizard | 3.3 | 1-2 weeks |
| 13 | Dynamic schema registry | 4.8 | 2 weeks |

**Outcome**: Discoverable connectors, quick-start templates, guided onboarding.

### Phase 5: Advanced UX (Weeks 19-24)

Focus: Visual tools and AI enhancement.

| # | Feature | Section | Effort |
|---|---------|---------|--------|
| 14 | Visual field mapper | 4.10 | 3-4 weeks |
| 15 | AI-assisted mapping & error explanation | 3.5 | 1-2 weeks |
| 16 | Use-case navigation & positioning | 3.4, 3.6 | 1 week |

**Outcome**: Non-technical users can configure integrations visually.

---

### Phase Summary

```
Phase 1 (Wk 1-4)     ████████░░░░░░░░░░░░░░░░  SDK, Health, Rate Limiting
Phase 2 (Wk 5-8)     ░░░░░░░░████████░░░░░░░░  OAuth2, Webhooks, Audit
Phase 3 (Wk 9-12)    ░░░░░░░░░░░░░░░░████████  Engine, Replay, Debug
Phase 4 (Wk 13-18)   ░░░░░░░░░░░░░░░░░░░░████  Catalog, Templates, Onboarding
Phase 5 (Wk 19-24)   ░░░░░░░░░░░░░░░░░░░░░░██  Visual Mapper, AI, Positioning
```

---

## 6. Appendix: Competitive Positioning

### 6.1 Feature Matrix: OIP vs Workato vs Make

| Feature | OIP (Current) | OIP (After Roadmap) | Workato | Make (Integromat) |
|---------|:---:|:---:|:---:|:---:|
| Open-source | Yes | Yes | No | No |
| Self-hosted | Yes | Yes | No | No |
| Embeddable library | Yes | Yes | Yes (Embedded) | No |
| Connector count | 37 | 37+ | 1000+ | 1500+ |
| Polish system support | Deep | Deep | Minimal | Minimal |
| Courier connectors | 18 | 18+ | ~5 | ~5 |
| OAuth2 lifecycle | No | Yes | Yes | Yes |
| Webhook ingestion | Basic | Full | Full | Full |
| Visual flow builder | Yes | Yes | Yes | Yes |
| Visual field mapper | No | Yes | Yes | Yes |
| AI workflow gen | Basic | Enhanced | Yes | No |
| Connector SDK | No | Yes | Yes (Ruby) | Yes |
| Real-time health | No | Yes | Yes | Yes |
| Execution replay | No | Yes | Yes | Yes |
| Sub-workflows | No | Yes | Yes | Yes |
| Scheduled triggers | No | Yes | Yes | Yes |
| Batch processing | No | Yes | Yes | Yes |
| Dynamic schemas | No | Yes | Yes | Partial |
| Audit trail | No | Yes | Yes | Yes |
| Flow templates | No | Yes | Yes | Yes (Community) |
| On-premise agent | Yes | Yes | Yes | No |
| Per-connector rate limit | No | Yes | Yes | Yes |
| Verification agent | Yes | Yes | No | No |
| Version isolation | Yes | Yes | No | No |
| Manifest-driven | Yes | Yes | No | No |

### 6.2 Where OIP Wins

Even after all improvements, OIP's unique differentiators remain:

1. **Open-source (Apache 2.0)** — no vendor lock-in, full code access, community contributions
2. **Deep Polish/regional system coverage** — InPost, Allegro, WAPRO, BaseLinker, IdoSell, Poczta Polska, Orlen Paczka, Packeta, DPD PL, GLS PL
3. **Self-hosted + SaaS** — deploy anywhere, full control
4. **Embeddable Angular library** — `@pinquark/integrations` for embedding in existing apps
5. **Connector version isolation** — multiple versions coexist, zero-risk upgrades
6. **Manifest-driven architecture** — zero platform code per connector
7. **Automated verification agent** — 3-tier health/auth/functional testing
8. **Logistics domain expertise** — 18 courier connectors with deep integration
9. **On-premise ERP bridge** — connect to local WAPRO/Subiekt via Docker agent
10. **Transparent pricing** — free (open-source) vs $10k+/year for enterprise iPaaS

---

*This document should be updated as features are implemented. Mark sections with implementation status: `[PLANNED]`, `[IN PROGRESS]`, `[DONE]`.*

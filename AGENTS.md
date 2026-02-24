# Open Integration Platform by Pinquark.com — Agent Guidelines

This document governs all agent activity across the Open Integration Platform by Pinquark.com. Every agent (implementation, verification, maintenance) MUST read and follow these rules before writing any code, building any Docker image, or deploying to any environment. Use only English language for implementation and documentation. For every connector download logo and setup proper origin country (don't use global). Create validator for every connector.

---

## 1. Project Overview

The Open Integration Platform by Pinquark.com is an **open-source integration hub** (Apache 2.0) that connects **any system with any other system** — courier services, e-commerce platforms, ERP systems, WMS, and more. It is designed as a modular, SaaS-first platform that can also be self-hosted, and can be embedded into Angular applications like Pinquark WMS via the `@pinquark/integrations` npm library.

The platform uses an **any-to-any architecture** with a Flow Engine: every connected system is an equal peer that can act as both a source (emitting events) and a destination (receiving actions). Flows define rules like "when event X happens in system A, execute action Y in system B".

The platform is designed to be **autonomous** — integrations are continuously built, tested, versioned, deployed, and monitored with minimal human intervention.

### Integration Categories


| #   | Category                            | Examples                                                                                           | Typical Protocol             |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------- |
| 1   | **Systemy kurierskie** (Courier)    | DHL, InPost, DPD, GLS, FedEx, UPS, Poczta Polska, OrlenPaczka, Schenker, Geis, Paxy, Packeta, Suus | REST, SOAP (WSDL)            |
| 2   | **Systemy e-commerce**              | Allegro, BaseLinker, PrestaShop, WooCommerce, Shopify, Shoper, IdoSell, SellAsist                  | REST, OAuth2, Webhooks       |
| 3   | **Systemy ERP**                     | WAPRO, Comarch ERP, Subiekt GT, SAP, enova365                                                      | REST, SOAP, ODBC/SQL, Files  |
| 4   | **Systemy automatyki** (Automation) | Cameras (RTSP/ONVIF), Barriers, SMS Gateways, Info Kiosks, Drones, UWB Sensors, AMR                | MQTT, REST, RTSP, Custom TCP |
| 5   | **Pozostałe systemy** (Other)       | Custom APIs, FTP/SFTP data exchange, EDI, Marketplace aggregators                                  | Varies                       |


### Existing Codebases


| Directory                | Stack                                 | Purpose                                                            |
| ------------------------ | ------------------------------------- | ------------------------------------------------------------------ |
| `platform/`              | FastAPI, SQLAlchemy, asyncpg, Redis   | API Gateway, Flow Engine, Workflow Engine, Credential Vault        |
| `platform/dashboard/`    | Angular, `@pinquark/integrations`     | Admin Dashboard (standalone + embeddable library)                  |
| `integrators/courier/`   | FastAPI, httpx, zeep (SOAP)           | 15 courier connectors (InPost, DHL, DPD, GLS, FedEx, UPS, ...)     |
| `integrators/ecommerce/` | FastAPI, httpx, aiokafka              | E-commerce connectors (Allegro)                                    |
| `integrators/wms/`       | FastAPI, httpx                        | WMS connector (Pinquark WMS)                                       |
| `shared/python/`         | Pydantic, aiokafka, httpx, prometheus | Shared library: schemas, Kafka, REST/SOAP clients, circuit breaker |
| `sdk/python/`            | httpx                                 | Python SDK for Platform API                                        |
| `k8s/`                   | Kubernetes, Strimzi, Nginx Ingress    | Deployment manifests, HPA, Kafka cluster/topics                    |
| `onpremise/`             | Docker, SQLite                        | On-premise agent for local ERP connectivity                        |


### Platform Documentation

> **IMPORTANT**: The following documentation files MUST be kept up to date when making architectural changes, adding new connectors, or modifying scalability configuration.


| Document             | Path                                           | Contents                                                                                                                      | Update when                                                            |
| -------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Architecture**     | `[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)` | System architecture, data exchange patterns, scalability mechanisms, throughput estimates, platform configuration, deployment | Changing infrastructure, scaling config, adding communication patterns |
| **Connectors**       | `[docs/CONNECTORS.md](docs/CONNECTORS.md)`     | Configuration parameters for all 20 connectors, env vars, credentials API                                                     | Adding/modifying connectors, changing config schema                    |
| **Agent Guidelines** | `[AGENTS.md](AGENTS.md)`                       | This file — coding standards, CI/CD, security, interfaces                                                                     | Changing development standards or workflows                            |


---

## 2. Architecture Principles

### 2.1 Integrator-per-service pattern

Each external system gets its own **connector** — a self-contained module that:

- Implements a standardized interface (per category)
- Handles authentication, rate limiting, retries, error mapping
- Is independently versioned, built, and deployed as a Docker container
- Acts as both **source** (emits events) and **destination** (receives actions)
- Communicates with the platform via the API Gateway, Kafka topics, or REST API
- Includes a `connector.yaml` manifest describing its capabilities, events, actions, and config schema

### 2.1.1 Connector Manifest

Every connector MUST include a `connector.yaml` in its version root:

```yaml
name: inpost
category: courier
version: 3.0.0
display_name: "InPost"
description: "InPost courier integration - Paczkomaty, Kurier, Returns"
interface: courier
capabilities:
  - create_shipment
  - get_label
  - get_shipment_status
  - cancel_shipment
  - get_pickup_points
  - create_return_shipment
events:
  - shipment.status_changed
  - shipment.created
actions:
  - shipment.create
  - label.get
  - shipment.cancel
  - pickup_points.list
  - return.create
config_schema:
  required:
    - organization_id
    - access_token
  optional:
    - sandbox_mode
    - default_currency
health_endpoint: /health
docs_url: /docs
```

### 2.1.2 Any-to-any topology

Unlike a hub-and-spoke model, every connector is an **equal peer**. The Flow Engine connects any source event to any destination action:

- Allegro `order.created` → InPost `shipment.create`
- InPost `shipment.status_changed` → Allegro `order.status_update`
- Shopify `order.created` → WAPRO `document.create`
- Any combination of connectors

WMS (e.g., Pinquark) is a connector like any other — not the center of the architecture.

### 2.2 Version isolation

Every integrator version is a separate, immutable artifact:

```
integrators/
  courier/
    dhl/
      v1.0.0/         ← full working integrator
      v1.1.0/         ← newer version, both coexist
      v2.0.0/         ← breaking change, separate container
    inpost/
      v1.0.0/
      v1.1.0-international/
  ecommerce/
    allegro/
      v1.0.0/
      v2.0.0/
  erp/
    wapro/
      v1.0.0/
  automation/
    cameras/
      v1.0.0/
  other/
    custom-ftp/
      v1.0.0/
```

Rules:

- **Never delete or overwrite** a released version — clients may depend on it
- Semantic versioning: `MAJOR.MINOR.PATCH` (`MAJOR` = breaking API changes)
- Each version has its own `Dockerfile`, config, and documentation
- The platform UI lets the client select which integrator version to use
- Deprecated versions are marked but remain available until all clients migrate

### 2.3 Communication patterns


| Pattern      | When to use                                                                          |
| ------------ | ------------------------------------------------------------------------------------ |
| **Kafka**    | Asynchronous data sync (documents, articles, contractors, orders, stock levels)      |
| **REST API** | Synchronous operations (create shipment, get label, check status, real-time queries) |
| **Webhooks** | Event-driven notifications from external systems (order placed, status changed)      |
| **Polling**  | When external system provides no push mechanism (scheduled scraping)                 |
| **gRPC**     | High-throughput internal service-to-service communication (future)                   |


### 2.4 Kafka topic naming

```
{system}.{direction}.{domain}.{entity}.{action}

system     = idosell | sap |inpost
direction  = input | output | errors | dlq
domain     = wms | erp | ecommerce | courier | automation
entity     = documents | articles | contractors | orders | shipments | statuses
action     = save | delete | update | sync | notify
```

Examples:

- `sap.input.wms.documents.save` — WMS sends document to integrator
- `inpost.output.courier.shipments.save` — integrator sends created shipment back to WMS
- `idosell.errors.ecommerce.orders.sync` — failed order sync from e-commerce platform
- `sap.dlq.erp.contractors.save` — dead letter queue for failed contractor sync

### 2.5 Flow Engine

The Flow Engine is the core component that enables any-to-any integration. Flows are per-tenant rules:

```
Source connector (event) → Field mapping → Destination connector (action)
```

Flow definition:

```yaml
flows:
  - name: "Allegro -> InPost shipment"
    source:
      connector: allegro
      event: order.created
      filter:
        delivery_method: inpost_paczkomat
    destination:
      connector: inpost
      action: shipment.create
    mapping:
      - from: order.buyer.name       -> to: receiver.first_name
      - from: order.buyer.address    -> to: receiver.address
      - from: order.point_id         -> to: extras.target_point
    on_error: retry
    max_retries: 3
```

### 2.6 Field mapping (hybrid model)

Field mappings use a two-layer hybrid model:

- **Layer 1 (files)**: Default mappings shipped with each connector, version-controlled in Git
- **Layer 2 (database)**: Per-tenant overrides, editable via the dashboard or API
- **Resolution**: merge defaults with tenant overrides, cache in Redis, invalidate on change

### 2.7 Platform Core

The platform core (`platform/`) provides:

- **API Gateway** (FastAPI): unified REST API for all connectors
- **Flow Engine**: any-to-any event routing and execution
- **Tenant Manager**: multi-tenant isolation with API keys
- **Credential Vault**: encrypted credential storage (AES-256-GCM per-tenant)
- **Mapping Resolver**: hybrid field mapping with caching
- **Admin Dashboard** (Angular): web UI + `@pinquark/integrations` npm library
- **Database**: PostgreSQL with Row-Level Security for tenant isolation

### 2.8 Dashboard distribution

The Admin Dashboard is distributed in two forms:

- **Standalone app**: full Angular application for self-hosted and SaaS deployments
- **Angular library** (`@pinquark/integrations`): npm package with components and services, embeddable in any Angular application (e.g., Pinquark WMS)

---

## 3. Security & Encryption

### 3.1 Secrets management

- **NEVER** commit credentials, API keys, tokens, certificates, or keystores to the repository
- Store all secrets in a dedicated secrets manager (HashiCorp Vault, AWS Secrets Manager, or environment-level CI/CD variables)
- Use `.env.example` files with placeholder values for documentation
- `.env` files MUST be in `.gitignore` and `.dockerignore`
- Kafka keystores (`*.jks`, `*.keystore`) MUST NOT be in the repo — inject them at deployment time via volume mounts or CI/CD secrets

### 3.2 Credential encryption

- All external system credentials (API keys, OAuth tokens, passwords) stored in the database MUST be encrypted at rest using AES-256-GCM
- Encryption keys MUST be stored separately from encrypted data (use envelope encryption)
- OAuth refresh tokens: encrypt before storage, decrypt only in memory during token refresh
- Database connection strings: use SSL/TLS, never plaintext connections in production
- Courier credentials passed in API calls MUST be base64-encoded and validated server-side — never log decoded credentials

### 3.3 Data protection (RODO/GDPR)

- **Never log** personally identifiable information (PII): names, addresses, phone numbers, email addresses
- **Never log** authentication data: passwords, tokens, API keys, certificates
- Use the `obfuscate()` utility for any sensitive data that must appear in debug logs
- Log retention: max 30 days in production, auto-purge after that
- All data transfers to external systems MUST use TLS 1.2+ (never HTTP, always HTTPS)
- Implement data anonymization for test/UAT environments — never use production customer data

### 3.4 Network security

- All inter-service communication within Docker network: use internal Docker networks, no exposed ports except the API gateway
- External-facing services: expose only through a reverse proxy (nginx/traefik) with rate limiting
- Kafka connections: SASL_SSL with certificate-based authentication
- Database connections: SSL required, IP allowlisting for production
- Health check endpoints (`/health`, `/readiness`): no authentication required but MUST NOT expose sensitive information

### 3.5 Container security

- Base images: use official slim/distroless images, pin exact versions (never `latest`)
- Run containers as non-root user (`USER 1001` in Dockerfile)
- No package managers in production images (multi-stage builds only)
- Scan images for vulnerabilities in CI/CD (Trivy, Snyk, or equivalent)
- Read-only filesystem where possible (`--read-only` flag)
- Set resource limits (CPU, memory) for every container
- No `--privileged` flag, no `SYS_ADMIN` capability

---

## 4. Docker Standards

### 4.1 Dockerfile conventions

Every integrator Dockerfile MUST follow this structure:

```dockerfile
# --- Build stage ---
FROM python:3.12-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
COPY . .

# --- Production stage ---
FROM python:3.12-slim
LABEL maintainer="integrations@Pinquark.com"
LABEL version="1.0.0"
LABEL category="courier"
LABEL system="dhl"

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=build /install /usr/local
COPY --from=build /app .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
```

For Java/Kotlin integrators:

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY . .
RUN ./gradlew bootJar -x test --no-daemon

FROM eclipse-temurin:21-jre-alpine
LABEL maintainer="integrations@Pinquark.com"
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
COPY --from=build /app/build/libs/*.jar app.jar
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
```

### 4.2 Docker Compose structure

Every integrator MUST include a `docker-compose.yml` for local development with:

- The integrator service
- Required dependencies (database, Kafka, Redis if needed)
- A test runner service
- Network isolation (dedicated bridge network per integrator)
- Volume mounts for local development (code hot-reload)
- Environment variable file reference (`.env`)

### 4.3 Image naming and tagging

```
registry.Pinquark.com/integrations/{category}/{system}:{version}

Examples:
  registry.Pinquark.com/integrations/courier/dhl:1.0.0
  registry.Pinquark.com/integrations/ecommerce/allegro:2.1.3
  registry.Pinquark.com/integrations/erp/wapro:1.0.0-onpremise
```

- Every push to `main`/`master` → build and tag with git SHA + `latest`
- Every git tag `v*` → build and tag with version number
- UAT deployments: tagged with `-uat` suffix during testing

---

## 5. CI/CD Pipeline

### 5.1 Pipeline stages

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│   Lint   │──▶│  Build   │──▶│   Test   │──▶│  Deploy  │──▶│  Verify  │
│ & Audit  │   │  Docker  │   │  Unit +  │   │   UAT    │   │  Agent   │
│          │   │  Image   │   │  Integr. │   │          │   │  Loop    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                                  │
                                                    ┌─────────────┘
                                                    ▼
                                              ┌──────────┐
                                              │ Feedback │──▶ Fix ──▶ Re-deploy ──▶ Re-verify
                                              │   Loop   │
                                              └──────────┘
```

### 5.2 Stage details

**Stage 1: Lint & Security Audit**

- Python: `ruff check`, `ruff format --check`, `mypy`
- Java/Kotlin: Checkstyle, SpotBugs
- Security: Semgrep scan, dependency vulnerability check (pip-audit / OWASP dependency-check)
- Secrets detection: truffleHog or gitleaks scan
- Docker: hadolint for Dockerfile linting

**Stage 2: Build Docker Image**

- Multi-stage build (see section 4.1)
- Image vulnerability scan (Trivy)
- Push to container registry with SHA tag

**Stage 3: Test**

- Unit tests (pytest / JUnit+Spock): MUST pass with >80% coverage
- Integration tests: run against sandbox/mock APIs of external systems
- Contract tests: verify API contracts match documentation

**Stage 4: Deploy to UAT**

- Deploy Docker container to UAT environment
- Run database migrations if needed
- Configure environment variables from secrets manager
- Wait for health check to pass

**Stage 5: Verification Agent Loop**

- Automated verification agent tests all documented endpoints
- Checks: response codes, response schemas, data integrity, error handling
- If verification fails → generates structured feedback → implementation agent fixes → re-deploy → re-verify
- Loop continues until all verification checks pass or max iterations (5) reached
- On max iterations: alert human operator

### 5.3 Branch strategy


| Branch                                     | Purpose                 | Deploys to                   |
| ------------------------------------------ | ----------------------- | ---------------------------- |
| `main` / `master`                          | Production-ready code   | Production (manual approval) |
| `uat`                                      | UAT testing             | UAT environment (auto)       |
| `dev`                                      | Active development      | Dev environment (auto)       |
| `feature/`*                                | New features            | — (PR only)                  |
| `hotfix/`*                                 | Urgent production fixes | UAT → Production             |
| `integrator/{category}/{system}/{version}` | New integrator work     | Dev → UAT                    |


### 5.4 Commit conventions

```
[CATEGORY-SYSTEM] action: description

Examples:
  [COURIER-DHL] feat: add multi-parcel shipment support
  [ECOMMERCE-ALLEGRO] fix: handle expired OAuth token gracefully
  [ERP-WAPRO] docs: update ODBC connection guide
  [PLATFORM] refactor: extract common retry logic to shared library
  [CI] fix: correct UAT deployment health check timeout
```

---

## 6. Agent Workflow

### 6.1 Implementation Agent

The implementation agent is responsible for building new integrators. Before writing any code:

1. **Read documentation** — Fetch and store the external system's API documentation (REST API docs, WSDL files, SDK references) into `docs/{category}/{system}/{version}/`
2. **Check existing integrators** — Look at similar integrators in the same category for patterns
3. **Implement the base interface** — Every integrator implements the category-specific interface (see section 7)
4. **Write tests** — Unit tests and integration tests (with sandbox/mock APIs) MUST be written alongside implementation
5. **Create Dockerfile** — Following section 4.1 standards
6. **Create documentation** — `README.md` with setup instructions, API mapping, configuration reference
7. **Create sandbox accounts** — Register sandbox/test accounts with external system if required, document credentials storage location

### 6.2 Verification & Maintenance Agent

The verification agent (`platform/verification-agent/`) is a single FastAPI microservice that combines continuous health monitoring with deep functional verification of every connector. It runs on a configurable schedule (default: every 7 days) and can also be triggered on-demand via the dashboard or API.

#### 6.2.1 Architecture

```
platform/verification-agent/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── src/
    ├── main.py                  # FastAPI app + APScheduler
    ├── config.py                # Pydantic settings
    ├── db.py                    # SQLAlchemy models (verification_reports, verification_settings)
    ├── discovery.py             # Connector discovery (connector.yaml + DB instances)
    ├── credential_vault.py      # AES-256-GCM credential decryption
    ├── runner.py                # Orchestrates 3-tier verification run
    ├── reporter.py              # Persists results to PostgreSQL
    ├── api/
    │   └── routes.py            # REST API: trigger runs, scheduler, reports, errors
    └── checks/
        ├── common.py            # Shared utilities (result, get_check, req_check, PDF_STUB)
        ├── base.py              # Tier 1: health, readiness, docs
        ├── auth.py              # Tier 2: credentials, auth status, connection status
        ├── functional.py        # Tier 3 dispatcher — routes to per-category module
        ├── courier/             # Tier 3: Courier connector tests
        │   ├── __init__.py
        │   └── generic.py       #   Fallback for couriers without a dedicated file
        ├── ecommerce/           # Tier 3: E-commerce connector tests
        │   ├── __init__.py
        │   └── generic.py       #   Fallback for e-commerce without a dedicated file
        ├── erp/                 # Tier 3: ERP connector tests
        │   └── __init__.py
        ├── automation/          # Tier 3: Automation connector tests
        │   └── __init__.py
        └── other/               # Tier 3: Other connector tests
            ├── __init__.py
            ├── skanuj_fakture.py  # SkanujFakture (20+ endpoints, full CRUD cycle)
            └── account_based.py   # Email, FTP/SFTP (generic account-based)
```

The directory layout mirrors `integrators/` categories. Each category folder contains:

- **`generic.py`** — fallback tests for connectors without a dedicated file (tests common endpoints based on `connector.yaml` capabilities)
- **`{connector_name}.py`** — connector-specific tests that exercise all documented endpoints

#### 6.2.2 Three-tier verification

Every connector goes through all three tiers in sequence. If a tier fails critically, subsequent tiers may be skipped.

**Tier 1 — Infrastructure (all connectors, no credentials needed)**

| Check | Endpoint | Pass condition |
| --- | --- | --- |
| Health | `GET /health` | HTTP 200, `status: "healthy"` |
| Readiness | `GET /readiness` | HTTP 200, all dependency checks pass |
| API docs | `GET /docs` | HTTP 200, Swagger/OpenAPI UI reachable |

**Tier 2 — Authentication (requires credentials from Credential Vault)**

| Check | Endpoint | Pass condition |
| --- | --- | --- |
| Account provisioning | `POST /accounts` | Account created or already exists |
| Auth status | `GET /auth/{account}/status` | `authenticated: true` |
| Connection status | `GET /connection/{account}/status` | `connected: true` |

**Tier 3 — Functional smoke tests (per-connector, requires credentials)**

Each connector has its own test module in `checks/`. Tests exercise all documented endpoints, including:

- **Read-only endpoints** — listing, searching, fetching details
- **Write+cleanup cycles** — upload a test resource, exercise per-resource endpoints, delete it afterward
- **Error paths** — expected 404s for missing data (e.g., KSeF for non-KSeF documents) are accepted as PASS
- **Performance** — every check records `response_time_ms`

#### 6.2.3 Scheduling & triggers

| Mode | How | Description |
| --- | --- | --- |
| Scheduled | APScheduler `IntervalTrigger` | Runs every `VERIFICATION_INTERVAL_DAYS` (default: 7). Configurable via API or dashboard. |
| On-demand (all) | `POST /api/verification/run` | Verifies all discovered connectors. |
| On-demand (single) | `POST /api/verification/run?connector_filter={name}` | Verifies a single connector. |
| Dashboard | Verification page toggle + "Run now" button | UI controls for scheduler enable/disable and manual triggers. |

#### 6.2.4 Maintenance responsibilities

The agent also covers continuous maintenance tasks previously described as a separate "Maintenance Agent":

1. **Health monitoring** — Scheduled runs verify all deployed connectors are alive and functional
2. **Regression detection** — Functional tests catch external API changes that break integrations
3. **Performance tracking** — Response time baselines stored per check, regressions visible in reports
4. **Alerting** — Failed checks generate structured error reports visible in the dashboard with filtering and drill-down
5. **Dependency health** — Tier 1 readiness checks verify database, Kafka, and external API connectivity

#### 6.2.5 Report format

Results are persisted to the `verification_reports` table and exposed via the API. Each report follows this structure:

```json
{
  "integrator": "other/skanuj-fakture/v1.0.0",
  "timestamp": "2026-02-24T12:00:00Z",
  "status": "FAIL",
  "checks": [
    {
      "name": "list_companies",
      "status": "PASS",
      "response_time_ms": 340
    },
    {
      "name": "upload_document",
      "status": "PASS",
      "response_time_ms": 1200
    },
    {
      "name": "get_ksef_xml",
      "status": "SKIP",
      "response_time_ms": 85,
      "error": "Endpoint not found (404)"
    },
    {
      "name": "get_document_file",
      "status": "FAIL",
      "error": "HTTP 500: Internal Server Error",
      "suggestion": "Check file retrieval logic in get_document_file() method"
    }
  ],
  "summary": {
    "total": 20,
    "passed": 16,
    "failed": 2,
    "skipped": 2
  }
}
```

Check statuses:

| Status | Meaning |
| --- | --- |
| `PASS` | Endpoint responded correctly within thresholds |
| `FAIL` | Unexpected status code, timeout, or exception |
| `SKIP` | Check not applicable (e.g., no credentials, expected 404, capability not supported) |

#### 6.2.6 Adding tests for a new connector

When a new connector is implemented, a corresponding Tier 3 test file MUST be created. Follow these steps:

**Step 1 — Create the test file in the correct category folder**

Place the file under the matching category directory:

```
checks/{category}/{connector_name}.py

Examples:
  checks/courier/inpost.py
  checks/ecommerce/allegro.py
  checks/erp/wapro.py
  checks/other/skanuj_fakture.py
```

Use underscores for connector names (e.g., `skanuj_fakture.py`, `base_linker.py`).

The file MUST export a single `run()` function:

```python
"""Tier 3 functional checks — {ConnectorDisplayName} connector."""

from typing import Any

import httpx

from src.checks.common import get_check, req_check, result
from src.discovery import VerificationTarget


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url
    account = (target.credentials or {}).get("account_name", "verification-agent")
    # ... test all endpoints ...
    return results
```

If a category folder does not exist yet, create it with an `__init__.py`:

```python
"""Tier 3 checks — {Category} connector category."""
```

Each category folder may also contain a `generic.py` — a fallback module that tests common endpoints for connectors that don't have a dedicated file. Connector-specific files always take priority.

**Step 2 — Test every endpoint from `connector.yaml`**

Cross-reference the connector's `connector.yaml` to ensure every documented capability, action, and endpoint is covered. For each endpoint:

- **Read-only endpoints** — use `get_check()` to verify HTTP 200 and measure response time
- **Write endpoints** — use `req_check()` with a full cycle: create → verify → cleanup. Always delete test data afterward.
- **Endpoints that may legitimately fail** — pass `accept_statuses=(200, 404)` when a 404 is expected behavior (e.g., KSeF data for non-KSeF documents)

Available utilities from `checks/common.py`:

| Function | Purpose |
| --- | --- |
| `result(name, status, ms, error?, suggestion?)` | Build a check result dict |
| `get_check(client, url, name, params?)` | Execute GET, return check result |
| `req_check(client, method, url, name, *, params?, json_body?, files?, accept_statuses?)` | Execute any HTTP method, return `(check_result, response)` |
| `PDF_STUB` | Minimal valid PDF bytes for upload tests |

**Step 3 — Register in the dispatcher**

Add the connector to `platform/verification-agent/src/checks/functional.py`. The dispatcher uses three registries, checked in order:

```python
from src.checks.{category} import {connector_name} as {category}_{connector_name}

# 1. Connector-specific (highest priority — matches by connector name)
_CONNECTOR_REGISTRY: dict[str, Any] = {
    "new-connector": category_new_connector,
    # ...
}

# 2. Interface-based (matches by connector.yaml `interface` field)
_INTERFACE_REGISTRY: dict[str, Any] = { ... }

# 3. Category-based fallback (matches by connector.yaml `category` field)
_CATEGORY_REGISTRY: dict[str, Any] = { ... }
```

For a connector-specific test file, add an entry to `_CONNECTOR_REGISTRY`. For a generic category fallback, add to `_CATEGORY_REGISTRY`.

**Step 4 — Test checklist**

Every connector test file SHOULD cover:

- [ ] `list_accounts` — verify account listing works
- [ ] All read-only listing endpoints (companies, documents, orders, products, etc.)
- [ ] All detail/get endpoints with a valid resource ID
- [ ] At least one full write cycle (create → read → update → delete) with cleanup
- [ ] Authentication-dependent endpoints with the provisioned account
- [ ] Error cases where applicable (expected 404s, invalid IDs)
- [ ] All endpoint variants (e.g., `/documents` vs `/documents/simple`, upload v1 vs v2)

**Naming conventions for checks:**

- Use descriptive snake_case names: `list_companies`, `upload_document`, `get_document_file`
- Prefix variants: `list_dictionaries_CATEGORY`, `upload_document_v2`
- Suffix cleanup steps: `delete_documents_cleanup`, `delete_v2_cleanup`

**Step 5 — Rebuild and verify**

```bash
docker compose -f docker-compose.prod.yml build verification-agent
docker compose -f docker-compose.prod.yml up -d verification-agent
curl -X POST "http://localhost:18080/api/verification/run?connector_filter={name}"
```

---

## 7. Integration Interfaces

### 7.1 Courier integration interface

Every courier integrator MUST implement:

List will be created

### 7.2 E-commerce integration interface

List will be created

### 7.3 ERP integration interface

List will be created

### 7.4 Automation integration interface

List will be created

---

## 8. On-Premise Integrators

Some integrations (especially ERP systems like WAPRO, Subiekt GT, Comarch) require a locally installed program at the client site to bridge the gap between the local system and the cloud platform.

### 8.1 On-premise agent architecture

```
┌─────────────────────────────────────┐
│          Client's Network           │
│                                     │
│  ┌─────────────┐   ┌────────────┐  │
│  │  Local ERP  │◀─▶│  On-Prem   │  │         ┌──────────────────┐
│  │  (e.g.      │   │  Agent     │──│────────▶│  Pinquark Cloud  │
│  │   WAPRO)    │   │  (Docker)  │  │  HTTPS  │  Integration Hub │
│  └─────────────┘   └────────────┘  │         └──────────────────┘
│                         │          │
│                    ┌────┴─────┐    │
│                    │ SQLite   │    │
│                    │ local DB │    │
│                    └──────────┘    │
└─────────────────────────────────────┘
```

### 8.2 On-premise agent requirements

- **Runs as Docker container** on client's server/VM (Docker Desktop, Docker Engine, or Podman)
- **Auto-update mechanism** — agent checks for updates on startup and periodically (configurable interval)
- **Offline resilience** — queues operations locally (SQLite) when cloud connection is lost, syncs when restored
- **ERP health monitoring** — periodic ping via SQL query (e.g., `SELECT 1` or `SELECT COUNT(*) FROM config_table`)
- **Heartbeat** — sends heartbeat to Pinquark Cloud every 60 seconds with: client name, agent version, ERP connection status, queue depth, system resources
- **Secure tunnel** — all communication to Pinquark Cloud via HTTPS with mutual TLS (mTLS)
- **Minimal permissions** — ERP database access: read-only where possible, write only for specific sync operations
- **Log shipping** — forward structured logs to Pinquark Cloud for centralized monitoring (with PII redaction)

### 8.3 ERP connectivity check

The on-premise agent MUST implement a robust connectivity check:

```python
class ErpConnectionMonitor:
    def ping(self) -> PingResult:
        """
        Execute a simple SQL query against the ERP database.
        Returns PingResult with status, latency, and error details.
        Runs every check_interval_seconds (default: 30).
        """

    def report_status(self) -> None:
        """
        Send connection status to Pinquark Cloud.
        Includes: connected/disconnected, latency_ms, last_successful_ping,
        consecutive_failures, erp_version, agent_version.
        """
```

Alerting thresholds:

- 3 consecutive ping failures → WARNING alert to Pinquark Cloud dashboard
- 10 consecutive failures → CRITICAL alert + email/SMS notification to client admin
- Connection restored after outage → RECOVERY notification

### 8.4 On-premise agent configuration

Configuration via environment variables or `config.yaml`:

```yaml
agent:
  id: "unique-agent-id"
  cloud_url: "https://integrations.Pinquark.com"
  heartbeat_interval_seconds: 60
  update_check_interval_hours: 6

erp:
  type: "wapro"  # wapro | comarch | subiekt | custom_odbc
  connection_string: "${ERP_CONNECTION_STRING}"
  ping_query: "SELECT 1"
  ping_interval_seconds: 30
  read_only: true

sync:
  interval_seconds: 300
  batch_size: 100
  retry_max: 3
  retry_backoff_seconds: 10

logging:
  level: "INFO"
  ship_to_cloud: true
  redact_pii: true
```

---

## 9. Monitoring & Observability

### 9.1 Health endpoints

Every integrator (cloud and on-premise) MUST expose:


| Endpoint         | Purpose                                        | Auth required         |
| ---------------- | ---------------------------------------------- | --------------------- |
| `GET /health`    | Basic liveness check (is the process running?) | No                    |
| `GET /readiness` | Full readiness check (dependencies available?) | No                    |
| `GET /metrics`   | Prometheus metrics                             | Internal network only |


Health response format:

```json
{
  "status": "healthy",
  "version": "1.2.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": "ok",
    "kafka": "ok",
    "external_api": "ok"
  }
}
```

### 9.2 Structured logging

All integrators MUST use structured JSON logging:

```json
{
  "timestamp": "2026-02-20T12:00:00.000Z",
  "level": "INFO",
  "service": "courier-dhl-v1.0.0",
  "trace_id": "abc123",
  "message": "Shipment created successfully",
  "shipment_id": "DHL-12345",
  "response_time_ms": 340
}
```

Rules:

- Log levels: `DEBUG` (dev only), `INFO` (operations), `WARNING` (degraded), `ERROR` (failures), `CRITICAL` (system down)
- Every external API call MUST be logged with: method, URL (without query params containing secrets), response status, response time
- Never log request/response bodies in production (may contain PII) — use `DEBUG` level only for development
- Include `trace_id` for distributed tracing across services

### 9.3 Metrics

Every integrator MUST expose Prometheus metrics:


| Metric                                      | Type      | Labels                          | Description                     |
| ------------------------------------------- | --------- | ------------------------------- | ------------------------------- |
| `integrator_requests_total`                 | Counter   | `method`, `endpoint`, `status`  | Request counter                 |
| `integrator_request_duration_seconds`       | Histogram | `method`, `endpoint`            | Request latency                 |
| `integrator_external_api_calls_total`       | Counter   | `system`, `operation`, `status` | External API call counter       |
| `integrator_external_api_duration_seconds`  | Histogram | `system`, `operation`           | External API latency            |
| `integrator_errors_total`                   | Counter   | `type`                          | Error counter by type           |
| `integrator_kafka_messages_processed_total` | Counter   | `topic`, `status`               | Kafka message counter           |
| `integrator_active_connections`             | Gauge     | `system`                        | Active connections (on-premise) |


### 9.4 Alerting rules


| Metric                       | Threshold         | Severity |
| ---------------------------- | ----------------- | -------- |
| Error rate                   | > 5% over 5 min   | WARNING  |
| Error rate                   | > 20% over 5 min  | CRITICAL |
| Response time p95            | > 5s              | WARNING  |
| Response time p95            | > 15s             | CRITICAL |
| Health check failing         | > 3 consecutive   | CRITICAL |
| On-premise heartbeat missing | > 5 min           | WARNING  |
| On-premise heartbeat missing | > 15 min          | CRITICAL |
| Kafka consumer lag           | > 1 000 messages  | WARNING  |
| Kafka consumer lag           | > 10 000 messages | CRITICAL |


---

## 10. Documentation Standards

### 10.0 Platform-level documentation

The following files document the platform as a whole and MUST be updated when relevant changes are made:


| Document                   | Path                                           | Update trigger                                         |
| -------------------------- | ---------------------------------------------- | ------------------------------------------------------ |
| Architecture & scalability | `[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)` | Infrastructure, scaling, data flow, deployment changes |
| Connector configuration    | `[docs/CONNECTORS.md](docs/CONNECTORS.md)`     | New connector, config schema change, new env var       |


When adding a new connector, the agent MUST:

1. Add the connector's config parameters to `docs/CONNECTORS.md`
2. Verify `docs/ARCHITECTURE.md` connector count is still accurate
3. Update the "Existing Codebases" table in this file if a new category is introduced

### 10.1 Per-integrator documentation

Every integrator version MUST have:

```
docs/{category}/{system}/{version}/
  ├── README.md              # Setup, configuration, deployment guide
  ├── API_MAPPING.md         # WMS fields ↔ external system fields mapping
  ├── CHANGELOG.md           # Version history
  ├── external-api-docs/     # Downloaded/saved external API documentation
  │   ├── openapi.yaml       # or swagger.json, WSDL files
  │   └── ...
  ├── sandbox-setup.md       # How to set up sandbox/test account
  └── known-issues.md        # Known limitations and workarounds
```

### 10.2 Documentation fetching

Before implementing any integration, the agent MUST:

1. Fetch the external system's latest API documentation
2. Store it in `docs/{category}/{system}/{version}/external-api-docs/`
3. Create `API_MAPPING.md` mapping every Pinquark WMS field to the external system's equivalent
4. Document authentication flow and required credentials
5. Document rate limits, sandbox URLs, and production URLs
6. Document all possible status codes and error responses

### 10.3 Changelog format

```markdown
# Changelog

## [1.1.0] - 2026-02-20
### Added
- Multi-parcel shipment support
- Pickup point search by coordinates

### Fixed
- OAuth token refresh race condition

### Changed
- Increased default timeout from 10s to 30s
```

---

## 11. Coding Standards

### 11.1 Python integrators

- **Python version**: 3.12+ (match base Docker image)
- **Framework**: FastAPI + Uvicorn for new integrators 
- **Type hints**: mandatory on all function signatures
- **Linting**: `ruff check` + `ruff format` (config in `pyproject.toml`)
- **Static analysis**: `mypy --strict` for new code
- **Testing**: `pytest` with `pytest-asyncio` for async code
- **Dependencies**: pin exact versions in `requirements.txt`, use `pip-compile` for reproducible builds
- **DTOs**: Pydantic v2 models for all API request/response schemas
- **HTTP client**: `httpx` (async) for external API calls — never raw `requests` in new code
- **SOAP client**: `zeep` for WSDL-based integrations
- **Configuration**: `pydantic-settings` for environment variable parsing

### 11.2 Java/Kotlin integrators

- **Java version**: 21+ (LTS)
- **Framework**: Spring Boot 3.x
- **Build tool**: Gradle with Kotlin DSL
- **Testing**: JUnit 5 + Spock for BDD-style tests
- **Dependencies**: use Spring dependency management BOM, pin versions
- **DTOs**: Java records or Kotlin data classes
- **HTTP client**: Spring WebClient (reactive) or RestClient (blocking)
- **Database**: Spring Data JPA with Flyway migrations
- **Kafka**: Spring Kafka with consumer/producer configuration per topic

### 11.3 Common rules (all languages)

- **No `any` types** — use strict typing everywhere
- **No hardcoded URLs** — all external URLs come from configuration/environment variables
- **No hardcoded credentials** — all secrets from environment variables or secrets manager
- **Retry logic** — use exponential backoff with jitter for all external API calls (max 3 retries)
- **Timeout** — every external API call MUST have explicit timeout (default: 30s connect, 60s read)
- **Rate limiting** — respect external system rate limits, implement client-side throttling
- **Idempotency** — all write operations MUST be idempotent (use idempotency keys where supported)
- **Error handling** — catch specific exceptions, never swallow errors silently
- **Status mapping** — use a unified status enum mapped to each external system's statuses
- **Line length**: max 120 characters
- **Naming**: snake_case for Python, camelCase for Java/Kotlin, kebab-case for URLs and Docker tags
- **No inline comments explaining obvious code** — self-documenting names

### 11.4 API design

- All integrator REST APIs follow OpenAPI 3.1 specification
- API documentation generated from code annotations (FastAPI auto-generates, Spring uses springdoc)
- Swagger UI available at `/docs` (FastAPI) or `/swagger-ui/` (Spring)
- Consistent error response format:

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

- HTTP status codes: use standard codes consistently (400 validation, 401 auth, 404 not found, 429 rate limited, 500 internal)
- Pagination: cursor-based for large datasets, `page`/`page_size` for simple lists

---

## 12. Testing Standards

### 12.1 Test categories


| Category    | Scope                                               | Runs in CI                | Required coverage   |
| ----------- | --------------------------------------------------- | ------------------------- | ------------------- |
| Unit        | Single function/class, mocked dependencies          | Always                    | >80%                |
| Integration | Real external sandbox APIs                          | `uat` and `main` branches | Key flows           |
| Contract    | API schema validation against docs                  | Always                    | All endpoints       |
| E2E         | Full flow: WMS → integrator → external system → WMS | UAT only                  | Critical paths      |
| Performance | Response time, throughput under load                | Pre-release               | Baseline thresholds |


### 12.2 Test naming

```python
# Python
def test_create_shipment_returns_waybill_number():
def test_create_shipment_raises_on_invalid_address():
def test_get_label_returns_pdf_bytes():
```

```java
// Java/Kotlin
def "create shipment returns waybill number"()
def "create shipment throws InvalidAddressException for missing city"()
```

### 12.3 Sandbox accounts

- Every external system integration MUST have a sandbox/test account
- Sandbox credentials stored in CI/CD secrets (never in code)
- If the external system provides no sandbox, create a mock server using WireMock (Java) or `respx`/`pytest-httpx` (Python)
- Document sandbox setup in `docs/{category}/{system}/{version}/sandbox-setup.md`

---

## 13. Project Structure

```
/
├── AGENTS.md                          # This file — global agent guidelines
├── docker-compose.yml                 # Root compose for full platform (dev)
├── .env.example                       # Environment template
├── .gitignore
│
├── platform/                          # Integration platform UI & orchestration
│   ├── Dockerfile
│   ├── src/
│   └── ...
│
├── shared/                            # Shared libraries across integrators
│   ├── python/
│   │   ├── Pinquark_common/           # Common DTOs, utils, base classes
│   │   ├── setup.py
│   │   └── requirements.txt
│   └── java/
│       └── common-lib/               # Common Java library
│
├── integrators/                       # All integrators organized by category
│   ├── courier/
│   │   ├── dhl/
│   │   │   └── v1.0.0/
│   │   │       ├── Dockerfile
│   │   │       ├── docker-compose.yml
│   │   │       ├── requirements.txt
│   │   │       ├── src/
│   │   │       └── tests/
│   │   ├── inpost/
│   │   ├── dpd/
│   │   └── ...
│   ├── ecommerce/
│   │   ├── allegro/
│   │   ├── baselinker/
│   │   ├── prestashop/
│   │   ├── woocommerce/
│   │   ├── shopify/
│   │   ├── shoper/
│   │   ├── idosell/
│   │   └── sellasist/
│   ├── erp/
│   │   ├── wapro/
│   │   ├── comarch/
│   │   ├── subiekt-gt/
│   │   └── sap/
│   ├── automation/
│   │   ├── cameras/
│   │   ├── barriers/
│   │   ├── sms-gateways/
│   │   ├── info-kiosks/
│   │   └── drones/
│   └── other/
│
├── onpremise/                         # On-premise agent (installed at client site)
│   ├── agent/
│   │   ├── Dockerfile
│   │   ├── src/
│   │   └── tests/
│   └── installers/                    # Platform-specific installers
│
├── docs/                              # Documentation per system per version
│   ├── courier/
│   ├── ecommerce/
│   ├── erp/
│   ├── automation/
│   └── other/
│
├── ci/                                # CI/CD pipeline configurations
│   ├── gitlab-ci.yml
│   ├── github-actions/
│   └── scripts/
│
├── monitoring/                        # Monitoring & alerting configuration
│   ├── prometheus/
│   ├── grafana/
│   └── alertmanager/
│
└── README.md
```

---

## 14. Autonomous Operation

### 14.1 Integration lifecycle

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌───────────────┐
│  Detect new  │────▶│  Fetch docs   │────▶│  Implement   │────▶│  Build &      │
│  API version │     │  & changelog  │     │  new version │     │  test locally │
└──────────────┘     └───────────────┘     └──────────────┘     └───────────────┘
                                                                        │
      ┌─────────────────────────────────────────────────────────────────┘
      ▼
┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌───────────────┐
│  Deploy to   │────▶│  Verification │────▶│  Feedback    │────▶│  Release to   │
│  UAT         │     │  agent tests  │     │  loop until  │     │  production   │
└──────────────┘     └───────────────┘     │  all pass    │     │  catalog      │
                                           └──────────────┘     └───────────────┘
```

### 14.2 Auto-update rules

- Monitor external API changelogs and versioning endpoints
- When a new API version is detected: create a new integrator version automatically
- The old version remains available and unchanged
- Notify platform administrators about new version availability
- Clients choose when to switch to the new version via the platform UI
- If an external API deprecates a version: warn all clients using that version 30 days in advance

### 14.3 Self-healing

- If an integrator fails health checks 5 consecutive times → automatic restart
- If restart doesn't resolve → roll back to previous healthy version
- If no healthy version exists → alert human operator with full diagnostic logs
- On-premise agents: if cloud connection lost → buffer locally → auto-sync on reconnection

---

## 15. Before Writing Code — Checklist

Every agent MUST verify before starting implementation:

- Read this entire AGENTS.md file
- Read `[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)` for system architecture and scalability context
- Read `[docs/CONNECTORS.md](docs/CONNECTORS.md)` for existing connector configurations
- Identify the integration category and target system
- Check if a similar integrator already exists (copy patterns, not code)
- Fetch and store external system API documentation
- Verify sandbox/test account is available (create one if not)
- Implement the correct category interface (section 7)
- Follow Docker standards (section 4)
- Follow security standards (section 3)
- Write tests meeting coverage requirements (section 12)
- Create documentation (section 10) — including updating `docs/CONNECTORS.md`
- Verify CI/CD pipeline passes all stages (section 5)
- Confirm the integrator passes verification agent checks (section 6.2)

---

## 16. Key Commands

```bash
# Development
docker compose up -d                      # Start full platform locally
docker compose up -d courier-dhl          # Start specific integrator
docker compose logs -f courier-dhl        # Follow integrator logs

# Testing
pytest tests/ -v                          # Run unit tests
pytest tests/ -m integration              # Run integration tests
pytest tests/ --cov --cov-report=html     # Coverage report

# Linting (Python)
ruff check .                              # Lint
ruff format .                             # Format
mypy src/ --strict                        # Type check

# Linting (Java/Kotlin)
./gradlew check                           # Checkstyle + tests
./gradlew spotbugsMain                    # Static analysis

# Docker
docker build -t integrations/courier/dhl:dev .   # Build image
docker run --rm -p 8000:8000 integrations/courier/dhl:dev  # Run locally
trivy image integrations/courier/dhl:dev          # Scan for vulnerabilities

# CI/CD
docker compose -f docker-compose.test.yml up --abort-on-container-exit  # Run full test suite
```


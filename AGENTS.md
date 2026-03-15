# Open Integration Platform by Pinquark.com — Agent Guidelines

This document governs all agent activity across the Open Integration Platform by Pinquark.com. Every agent (implementation, verification, maintenance) MUST read and follow these rules before writing any code, building any Docker image, or deploying to any environment. Use only English language for implementation and documentation. For every connector download logo and setup proper origin country (don't use global). Create validator for every connector.

**CRITICAL: Before every `git commit` and `git push`, the agent MUST ask the user for explicit permission. Never commit or push changes without the user's confirmation.**

> **Reference docs** (read on demand when working on related tasks):
> - [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture, database schema, scalability, deployment
> - [docs/CONNECTORS.md](docs/CONNECTORS.md) — configuration parameters for all connectors
> - [docs/STANDARDS.md](docs/STANDARDS.md) — Docker, CI/CD, security, monitoring, on-premise, documentation standards
> - [docs/CONNECTOR-DEVELOPMENT.md](docs/CONNECTOR-DEVELOPMENT.md) — connector.yaml spec, SDK, verification agent, testing guide

---

## 1. Project Overview

The Open Integration Platform by Pinquark.com is an **open-source integration hub** (Apache 2.0) that connects **any system with any other system** — courier services, e-commerce platforms, ERP systems, WMS, and more. It is designed as a modular, SaaS-first platform that can also be self-hosted, and can be embedded into Angular applications like Pinquark WMS via the `@pinquark/integrations` npm library.

The platform uses an **any-to-any architecture** with a Flow Engine: every connected system is an equal peer that can act as both a source (emitting events) and a destination (receiving actions). Flows define rules like "when event X happens in system A, execute action Y in system B".

The platform is designed to be **autonomous** — integrations are continuously built, tested, versioned, deployed, and monitored with minimal human intervention.

Categories: Courier (18 connectors), E-commerce (8), ERP (1), WMS (1), AI (1), Other (6). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full list.

### Existing Codebases


| Directory                      | Stack                                 | Purpose                                                                     |
| ------------------------------ | ------------------------------------- | --------------------------------------------------------------------------- |
| `platform/`                    | FastAPI, SQLAlchemy, asyncpg, Redis   | API Gateway, Flow Engine, Workflow Engine, Credential Vault                 |
| `platform/dashboard/`          | Angular, `@pinquark/integrations`     | Admin Dashboard (standalone + embeddable library)                           |
| `platform/verification-agent/` | FastAPI, APScheduler, httpx           | 3-tier connector verification & health monitoring                           |
| `integrators/courier/`         | FastAPI, httpx, zeep (SOAP)           | 18 courier connectors (InPost, DHL, DPD, GLS, FedEx, UPS, Raben, ...)       |
| `integrators/ecommerce/`       | FastAPI, httpx, aiokafka              | 8 e-commerce connectors (Allegro, Amazon, Apilo, BaseLinker, Shopify, ...)  |
| `integrators/erp/`             | FastAPI, Python.NET                   | ERP connectors (InsERT Nexo — hybrid on-premise + cloud)                    |
| `integrators/wms/`             | FastAPI, httpx                        | WMS connector (Pinquark WMS)                                                |
| `integrators/ai/`              | FastAPI, httpx                        | AI Agent (Gemini — risk analysis, courier recommendations, data extraction) |
| `integrators/other/`           | FastAPI, httpx                        | 5 connectors (Email Client, SkanujFakture, FTP/SFTP, Slack, BulkGate SMS)   |
| `shared/python/`               | Pydantic, aiokafka, httpx, prometheus | Shared library: schemas, Kafka, REST/SOAP clients, circuit breaker          |
| `sdk/python/`                  | httpx                                 | Python SDK for Platform API                                                 |
| `k8s/`                         | Kubernetes, Strimzi, Nginx Ingress    | Deployment manifests, HPA, Kafka cluster/topics                             |
| `onpremise/`                   | Docker, Python.NET, SQLite            | On-premise agent for local ERP connectivity + Windows installer             |


### Platform Documentation

> **IMPORTANT**: The following documentation files MUST be kept up to date when making architectural changes, adding new connectors, or modifying scalability configuration.


| Document              | Path                                                   | Update when                                                            |
| --------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------- |
| **Architecture**      | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)           | Changing infrastructure, scaling config, adding communication patterns |
| **DB Schema Diagram** | [docs/database-schema.png](docs/database-schema.png)   | Adding/removing tables, columns, or foreign keys (any migration)       |
| **Connectors**        | [docs/CONNECTORS.md](docs/CONNECTORS.md)               | Adding/modifying connectors, changing config schema                    |
| **Standards**         | [docs/STANDARDS.md](docs/STANDARDS.md)                 | Changing Docker, CI/CD, security, monitoring, or documentation rules   |
| **Connector Dev**     | [docs/CONNECTOR-DEVELOPMENT.md](docs/CONNECTOR-DEVELOPMENT.md) | Changing connector.yaml spec, SDK, verification agent, or testing guide |
| **Agent Guidelines**  | [AGENTS.md](AGENTS.md)                                 | Changing core development rules or workflows                           |


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

> Full connector.yaml spec: [docs/CONNECTOR-DEVELOPMENT.md#1-connector-manifest-connectoryaml](docs/CONNECTOR-DEVELOPMENT.md#1-connector-manifest-connectoryaml)

### 2.2 Any-to-any topology

Unlike a hub-and-spoke model, every connector is an **equal peer**. The Flow Engine connects any source event to any destination action. WMS (e.g., Pinquark) is a connector like any other — not the center of the architecture.

### 2.3 Version isolation

Every integrator version is a separate, immutable artifact under `integrators/{category}/{system}/{version}/`.

Rules:

- **Never delete or overwrite** a released version — clients may depend on it
- Semantic versioning: `MAJOR.MINOR.PATCH` (`MAJOR` = breaking API changes)
- Each version has its own `Dockerfile`, config, and documentation
- The platform UI lets the client select which integrator version to use
- Deprecated versions are marked but remain available until all clients migrate

### 2.4 Communication patterns


| Pattern      | When to use                                                                          |
| ------------ | ------------------------------------------------------------------------------------ |
| **Kafka**    | Asynchronous data sync (documents, articles, contractors, orders, stock levels)      |
| **REST API** | Synchronous operations (create shipment, get label, check status, real-time queries) |
| **Webhooks** | Event-driven notifications from external systems (order placed, status changed)      |
| **Polling**  | When external system provides no push mechanism (scheduled scraping)                 |
| **gRPC**     | High-throughput internal service-to-service communication (future)                   |


### 2.5 Kafka topic naming

```
{system}.{direction}.{domain}.{entity}.{action}

system     = idosell | sap | inpost
direction  = input | output | errors | dlq
domain     = wms | erp | ecommerce | courier | automation
entity     = documents | articles | contractors | orders | shipments | statuses
action     = save | delete | update | sync | notify
```

### 2.6 Flow Engine

The Flow Engine is the core component that enables any-to-any integration. Flows are per-tenant rules:

```
Source connector (event) → Field mapping → Destination connector (action)
```

### 2.7 Field mapping (hybrid model)

- **Layer 1 (files)**: Default mappings shipped with each connector, version-controlled in Git
- **Layer 2 (database)**: Per-tenant overrides, editable via the dashboard or API
- **Resolution**: merge defaults with tenant overrides, cache in Redis, invalidate on change

### 2.8 Platform Core

The platform core (`platform/`) provides: API Gateway (FastAPI), Flow Engine, Tenant Manager, Credential Vault (AES-256-GCM), Mapping Resolver, Admin Dashboard (Angular + `@pinquark/integrations` npm library), PostgreSQL with Row-Level Security.

---

## 3. Security & Encryption (summary)

Core security rules — every agent MUST follow these at all times:

- **NEVER** commit credentials, API keys, tokens, certificates, or keystores to the repository
- All credentials in the database MUST be encrypted at rest using AES-256-GCM with envelope encryption
- **Never log** PII (names, addresses, phone numbers, emails) or authentication data (passwords, tokens, API keys)
- Use the `obfuscate()` utility for sensitive data in debug logs
- All data transfers to external systems MUST use TLS 1.2+ (never HTTP, always HTTPS)
- `.env` files MUST be in `.gitignore` and `.dockerignore`; use `.env.example` with placeholders
- Containers: non-root user, pinned base images (never `latest`), no `--privileged`, multi-stage builds only
- Public workflow endpoints MUST support per-workflow client IP allowlists (exact IPs + CIDR ranges)

> Full details: [docs/STANDARDS.md#1-security--encryption](docs/STANDARDS.md#1-security--encryption)

---

## 4. Docker Standards (summary)

- Multi-stage builds, non-root user, health checks in every Dockerfile
- Every integrator MUST include a `docker-compose.yml` for local development
- Image naming: `ghcr.io/{your-org}/oip/{category}/{system}:{version}`

> Full templates and details: [docs/STANDARDS.md#2-docker-standards](docs/STANDARDS.md#2-docker-standards)

---

## 5. CI/CD Pipeline (summary)

Pipeline: Lint & Audit → Build Docker → Test (>80% coverage) → Deploy UAT → Verification Agent Loop.

### Branch strategy


| Branch                                     | Purpose                 | Deploys to                   |
| ------------------------------------------ | ----------------------- | ---------------------------- |
| `main` / `master`                          | Production-ready code   | Production (manual approval) |
| `uat`                                      | UAT testing             | UAT environment (auto)       |
| `dev`                                      | Active development      | Dev environment (auto)       |
| `feature/`*                                | New features            | — (PR only)                  |
| `hotfix/`*                                 | Urgent production fixes | UAT → Production             |
| `integrator/{category}/{system}/{version}` | New integrator work     | Dev → UAT                    |


### Commit conventions

```
[CATEGORY-SYSTEM] action: description

Examples:
  [COURIER-DHL] feat: add multi-parcel shipment support
  [ECOMMERCE-ALLEGRO] fix: handle expired OAuth token gracefully
  [PLATFORM] refactor: extract common retry logic to shared library
```

> Full pipeline details: [docs/STANDARDS.md#3-cicd-pipeline](docs/STANDARDS.md#3-cicd-pipeline)

---

## 6. Agent Workflow (summary)

### Implementation Agent

Before writing code: fetch API docs → check existing integrators → implement interface → write tests → create Dockerfile → create documentation → create sandbox accounts.

### Verification & Maintenance Agent

Three-tier verification: Tier 1 (health, readiness, docs) → Tier 2 (auth, account provisioning) → Tier 3 (functional smoke tests per connector). Runs on schedule (default: 7 days) or on-demand.

> Full workflow, architecture, and test writing guide: [docs/CONNECTOR-DEVELOPMENT.md](docs/CONNECTOR-DEVELOPMENT.md)

---

## 7. Coding Standards

### 7.1 Python integrators

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

### 7.2 Java/Kotlin integrators

- **Java version**: 21+ (LTS)
- **Framework**: Spring Boot 3.x
- **Build tool**: Gradle with Kotlin DSL
- **Testing**: JUnit 5 + Spock for BDD-style tests
- **Dependencies**: use Spring dependency management BOM, pin versions
- **DTOs**: Java records or Kotlin data classes
- **HTTP client**: Spring WebClient (reactive) or RestClient (blocking)
- **Database**: Spring Data JPA with Flyway migrations
- **Kafka**: Spring Kafka with consumer/producer configuration per topic

### 7.3 Common rules (all languages)

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

### 7.4 API design

- All integrator REST APIs follow OpenAPI 3.1 specification
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

## 8. Testing Standards

### 8.1 Test categories


| Category    | Scope                                               | Runs in CI                | Required coverage   |
| ----------- | --------------------------------------------------- | ------------------------- | ------------------- |
| Unit        | Single function/class, mocked dependencies          | Always                    | >80%                |
| Integration | Real external sandbox APIs                          | `uat` and `main` branches | Key flows           |
| Contract    | API schema validation against docs                  | Always                    | All endpoints       |
| E2E         | Full flow: WMS → integrator → external system → WMS | UAT only                  | Critical paths      |
| Performance | Response time, throughput under load                | Pre-release               | Baseline thresholds |


### 8.2 Test naming

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

### 8.3 Sandbox accounts

- Every external system integration MUST have a sandbox/test account
- Sandbox credentials stored in CI/CD secrets (never in code)
- If the external system provides no sandbox, create a mock server using WireMock (Java) or `respx`/`pytest-httpx` (Python)
- Document sandbox setup in `docs/{category}/{system}/{version}/sandbox-setup.md`

---

## 9. Project Structure

```
/
├── AGENTS.md                          # This file — global agent guidelines
├── docker-compose.yml                 # Root compose for full platform (dev)
├── .env.example                       # Environment template
├── platform/                          # API Gateway, Flow Engine, Dashboard, Verification Agent
├── shared/python/                     # Common DTOs, utils, base classes
├── integrators/                       # All integrators organized by category
│   ├── courier/                       #   dhl/, inpost/, dpd/, gls/, ...
│   ├── ecommerce/                     #   allegro/, shopify/, shoper/, ...
│   ├── erp/                           #   wapro/, comarch/, subiekt-gt/, sap/
│   ├── automation/                    #   cameras/, barriers/, sms-gateways/, ...
│   └── other/                         #   email-client/, skanuj-fakture/, ftp-sftp/, ...
├── onpremise/                         # On-premise agent for local ERP
├── docs/                              # Documentation per system per version
├── ci/                                # CI/CD pipeline configurations
├── monitoring/                        # Prometheus, Grafana, Alertmanager
└── README.md
```

---

## 10. Before Writing Code — Checklist

Every agent MUST verify before starting implementation:

- Read this entire AGENTS.md file
- Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system architecture and scalability context
- Read [docs/CONNECTORS.md](docs/CONNECTORS.md) for existing connector configurations
- Identify the integration category and target system
- Check if a similar integrator already exists (copy patterns, not code)
- Fetch and store external system API documentation
- Verify sandbox/test account is available (create one if not)
- Implement the correct category interface (see [docs/CONNECTOR-DEVELOPMENT.md#5-integration-interfaces](docs/CONNECTOR-DEVELOPMENT.md#5-integration-interfaces))
- Follow Docker standards (see [docs/STANDARDS.md#2-docker-standards](docs/STANDARDS.md#2-docker-standards))
- Follow security standards (see [docs/STANDARDS.md#1-security--encryption](docs/STANDARDS.md#1-security--encryption))
- If a workflow can be triggered directly over HTTP, verify whether it needs a trigger-level IP allowlist and document the expected allowed IPs/CIDR ranges.
- Write tests meeting coverage requirements (section 8)
- Create documentation — including updating `docs/CONNECTORS.md` (see [docs/STANDARDS.md#6-documentation-standards](docs/STANDARDS.md#6-documentation-standards))
- If database schema was modified: regenerate `docs/database-schema.png` and update section 4 of `docs/ARCHITECTURE.md`
- Verify CI/CD pipeline passes all stages (see [docs/STANDARDS.md#3-cicd-pipeline](docs/STANDARDS.md#3-cicd-pipeline))
- Confirm the integrator passes verification agent checks (see [docs/CONNECTOR-DEVELOPMENT.md#4-verification--maintenance-agent](docs/CONNECTOR-DEVELOPMENT.md#4-verification--maintenance-agent))

---

## 11. Key Commands

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

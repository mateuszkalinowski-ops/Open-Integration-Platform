# Open Integration Platform — Standards & Operations Reference

> **Parent document**: [AGENTS.md](../AGENTS.md) (core agent rules)
> **Related**: [ARCHITECTURE.md](ARCHITECTURE.md) | [CONNECTORS.md](CONNECTORS.md) | [CONNECTOR-DEVELOPMENT.md](CONNECTOR-DEVELOPMENT.md)

This file contains the full reference material for Docker, CI/CD, security, monitoring, documentation, on-premise, and autonomous operation standards. Agents should read specific sections on demand when working on related tasks.

---

## Table of contents

1. [Security & Encryption](#1-security--encryption)
2. [Docker Standards](#2-docker-standards)
3. [CI/CD Pipeline](#3-cicd-pipeline)
4. [On-Premise Integrators](#4-on-premise-integrators)
5. [Monitoring & Observability](#5-monitoring--observability)
6. [Documentation Standards](#6-documentation-standards)
7. [Autonomous Operation](#7-autonomous-operation)

---

## 1. Security & Encryption

### 1.1 Secrets management

- **NEVER** commit credentials, API keys, tokens, certificates, or keystores to the repository
- Store all secrets in a dedicated secrets manager (HashiCorp Vault, AWS Secrets Manager, or environment-level CI/CD variables)
- Use `.env.example` files with placeholder values for documentation
- `.env` files MUST be in `.gitignore` and `.dockerignore`
- Kafka keystores (`*.jks`, `*.keystore`) MUST NOT be in the repo — inject them at deployment time via volume mounts or CI/CD secrets

### 1.2 Credential encryption

- All external system credentials (API keys, OAuth tokens, passwords) stored in the database MUST be encrypted at rest using AES-256-GCM
- Encryption keys MUST be stored separately from encrypted data (use envelope encryption)
- OAuth refresh tokens: encrypt before storage, decrypt only in memory during token refresh
- Database connection strings: use SSL/TLS, never plaintext connections in production
- Courier credentials passed in API calls MUST be base64-encoded and validated server-side — never log decoded credentials

### 1.2.1 Credential tokens

Each credential set (per tenant, connector, and credential name) is assigned an opaque **credential token** (`ctok_xxx`). Tokens provide two security benefits:

1. **GET response masking**: `GET /api/v1/credentials/{connector}` returns the token instead of actual credential values — no secrets are ever exposed in API responses.
2. **Lightweight authentication for public endpoints**: the workflow `GET /api/v1/workflows/{id}/call` endpoint accepts `?token=ctok_xxx` in the query string instead of the full platform API key (`pk_live_xxx`). The token identifies the tenant without granting full API access.

Token lifecycle:
- **Created** automatically on `POST /api/v1/credentials` — returned in the response
- **Returned** in `GET /api/v1/credentials` and `GET /api/v1/credentials/{connector}` responses
- **Regenerated** via `POST /api/v1/credentials/{connector}/token/regenerate` (old token immediately invalidated)
- **Deleted** automatically when credentials are deleted
- **Resolved** via `POST /api/v1/credentials/resolve-token` (tenant-scoped, for internal use)

Tokens are stored in the `credential_tokens` table with RLS and a unique index on the `token` column.

### 1.3 Data protection (RODO/GDPR)

- **Never log** personally identifiable information (PII): names, addresses, phone numbers, email addresses
- **Never log** authentication data: passwords, tokens, API keys, certificates
- Use the `obfuscate()` utility for any sensitive data that must appear in debug logs
- Log retention: max 30 days in production, auto-purge after that
- All data transfers to external systems MUST use TLS 1.2+ (never HTTP, always HTTPS)
- Implement data anonymization for test/UAT environments — never use production customer data

### 1.4 Network security

- All inter-service communication within Docker network: use internal Docker networks, no exposed ports except the API gateway
- External-facing services: expose only through a reverse proxy (nginx/traefik) with rate limiting
- Public or semi-public workflow HTTP endpoints (for example `GET /api/v1/workflows/{id}/call` and direct workflow execution endpoints) MUST support per-workflow client IP allowlists. Store the allowlist in the workflow trigger configuration, support both exact IPs and CIDR ranges, and return HTTP 403 for disallowed clients. These endpoints accept credential tokens (`?token=ctok_xxx`) for tenant identification instead of the full API key — never expose `pk_live_*` keys in URLs.
- Kafka connections: SASL_SSL with certificate-based authentication
- Database connections: SSL required, IP allowlisting for production
- Health check endpoints (`/health`, `/readiness`): no authentication required but MUST NOT expose sensitive information

### 1.5 Container security

- Base images: use official slim/distroless images, pin exact versions (never `latest`)
- Run containers as non-root user (`USER 1001` in Dockerfile)
- No package managers in production images (multi-stage builds only)
- Scan images for vulnerabilities in CI/CD (Trivy, Snyk, or equivalent)
- Read-only filesystem where possible (`--read-only` flag)
- Set resource limits (CPU, memory) for every container
- No `--privileged` flag, no `SYS_ADMIN` capability

---

## 2. Docker Standards

### 2.1 Dockerfile conventions

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

### 2.2 Docker Compose structure

Every integrator MUST include a `docker-compose.yml` for local development with:

- The integrator service
- Required dependencies (database, Kafka, Redis if needed)
- A test runner service
- Network isolation (dedicated bridge network per integrator)
- Volume mounts for local development (code hot-reload)
- Environment variable file reference (`.env`)

### 2.3 Image naming and tagging

```
ghcr.io/{your-org}/oip/{category}/{system}:{version}

Examples:
  ghcr.io/your-org/oip/courier/dhl:1.0.0
  ghcr.io/your-org/oip/ecommerce/allegro:2.1.3
  ghcr.io/your-org/oip/erp/wapro:1.0.0-onpremise
```

- Every push to `main`/`master` -> build and tag with git SHA + `latest`
- Every git tag `v*` -> build and tag with version number
- UAT deployments: tagged with `-uat` suffix during testing

---

## 3. CI/CD Pipeline

### 3.1 Pipeline stages

```
Lint & Audit -> Build Docker -> Test (Unit+Integr.) -> Deploy UAT -> Verify Agent Loop
                                                                          |
                                                            Feedback -> Fix -> Re-deploy -> Re-verify
```

### 3.2 Stage details

**Stage 1: Lint & Security Audit**

- Python: `ruff check`, `ruff format --check`, `mypy`
- Java/Kotlin: Checkstyle, SpotBugs
- Security: Semgrep scan, dependency vulnerability check (pip-audit / OWASP dependency-check)
- Secrets detection: truffleHog or gitleaks scan
- Docker: hadolint for Dockerfile linting

**Stage 2: Build Docker Image**

- Multi-stage build (see section 2.1)
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
- If verification fails -> generates structured feedback -> implementation agent fixes -> re-deploy -> re-verify
- Loop continues until all verification checks pass or max iterations (5) reached
- On max iterations: alert human operator

### 3.3 Branch strategy


| Branch                                     | Purpose                 | Deploys to                   |
| ------------------------------------------ | ----------------------- | ---------------------------- |
| `main` / `master`                          | Production-ready code   | Production (manual approval) |
| `uat`                                      | UAT testing             | UAT environment (auto)       |
| `dev`                                      | Active development      | Dev environment (auto)       |
| `feature/`*                                | New features            | -- (PR only)                 |
| `hotfix/`*                                 | Urgent production fixes | UAT -> Production            |
| `integrator/{category}/{system}/{version}` | New integrator work     | Dev -> UAT                   |


### 3.4 Commit conventions

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

## 4. On-Premise Integrators

Some integrations (especially ERP systems like WAPRO, Subiekt GT, Comarch) require a locally installed program at the client site to bridge the gap between the local system and the cloud platform.

### 4.1 On-premise agent architecture

```
+-------------------------------------+
|          Client's Network           |
|                                     |
|  +-----------+   +------------+    |
|  | Local ERP |<->|  On-Prem   |    |         +------------------+
|  | (e.g.     |   |  Agent     |----|-------->|  Pinquark Cloud  |
|  |  WAPRO)   |   |  (Docker)  |    |  HTTPS  |  Integration Hub |
|  +-----------+   +------------+    |         +------------------+
|                       |            |
|                  +----+-----+      |
|                  | SQLite   |      |
|                  | local DB |      |
|                  +----------+      |
+-------------------------------------+
```

### 4.2 On-premise agent requirements

- **Runs as Docker container** on client's server/VM (Docker Desktop, Docker Engine, or Podman)
- **Auto-update mechanism** -- agent checks for updates on startup and periodically (configurable interval)
- **Offline resilience** -- queues operations locally (SQLite) when cloud connection is lost, syncs when restored
- **ERP health monitoring** -- periodic ping via SQL query (e.g., `SELECT 1` or `SELECT COUNT(*) FROM config_table`)
- **Heartbeat** -- sends heartbeat to Pinquark Cloud every 60 seconds with: client name, agent version, ERP connection status, queue depth, system resources
- **Secure tunnel** -- all communication to Pinquark Cloud via HTTPS with mutual TLS (mTLS)
- **Minimal permissions** -- ERP database access: read-only where possible, write only for specific sync operations
- **Log shipping** -- forward structured logs to Pinquark Cloud for centralized monitoring (with PII redaction)

### 4.3 ERP connectivity check

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

- 3 consecutive ping failures -> WARNING alert to Pinquark Cloud dashboard
- 10 consecutive failures -> CRITICAL alert + email/SMS notification to client admin
- Connection restored after outage -> RECOVERY notification

### 4.4 On-premise agent configuration

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

## 5. Monitoring & Observability

### 5.1 Health endpoints

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

### 5.2 Structured logging

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
- Never log request/response bodies in production (may contain PII) -- use `DEBUG` level only for development
- Include `trace_id` for distributed tracing across services

### 5.3 Metrics

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


### 5.4 Alerting rules


| Metric                       | Threshold         | Severity |
| ---------------------------- | ----------------- | -------- |
| Error rate                   | > 5% over 5 min   | WARNING  |
| Error rate                   | > 20% over 5 min  | CRITICAL |
| Response time p95            | > 5s              | WARNING  |
| Response time p95            | > 15s             | CRITICAL |
| Health check failing         | > 3 consecutive   | CRITICAL |
| On-premise heartbeat missing | > 5 min           | WARNING  |
| On-premise heartbeat missing | > 15 min          | CRITICAL |
| Kafka consumer lag           | > 1000 messages   | WARNING  |
| Kafka consumer lag           | > 10000 messages  | CRITICAL |


---

## 6. Documentation Standards

### 6.0 Platform-level documentation

The following files document the platform as a whole and MUST be updated when relevant changes are made:


| Document                   | Path                                                   | Update trigger                                                   |
| -------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------- |
| Architecture & scalability | [docs/ARCHITECTURE.md](ARCHITECTURE.md)                | Infrastructure, scaling, data flow, deployment changes           |
| Database schema diagram    | [docs/database-schema.png](database-schema.png)        | Any migration that adds/removes tables, columns, or foreign keys |
| Connector configuration    | [docs/CONNECTORS.md](CONNECTORS.md)                    | New connector, config schema change, new env var                 |


When adding a new connector, the agent MUST:

1. Add the connector's config parameters to `docs/CONNECTORS.md`
2. Verify `docs/ARCHITECTURE.md` connector count is still accurate
3. Update the "Existing Codebases" table in `AGENTS.md` if a new category is introduced

When modifying the database schema (new migration), the agent MUST:

1. Regenerate `docs/database-schema.png` to reflect the current state of all tables, columns, and relationships
2. Verify the table overview in `docs/ARCHITECTURE.md` section 4 is still accurate

### 6.1 Per-integrator documentation

Every integrator version MUST have:

```
docs/{category}/{system}/{version}/
  +-- README.md              # Setup, configuration, deployment guide
  +-- API_MAPPING.md         # WMS fields <-> external system fields mapping
  +-- CHANGELOG.md           # Version history
  +-- external-api-docs/     # Downloaded/saved external API documentation
  |   +-- openapi.yaml       # or swagger.json, WSDL files
  |   +-- ...
  +-- sandbox-setup.md       # How to set up sandbox/test account
  +-- known-issues.md        # Known limitations and workarounds
```

### 6.2 Documentation fetching

Before implementing any integration, the agent MUST:

1. Fetch the external system's latest API documentation
2. Store it in `docs/{category}/{system}/{version}/external-api-docs/`
3. Create `API_MAPPING.md` mapping every Pinquark WMS field to the external system's equivalent
4. Document authentication flow and required credentials
5. Document rate limits, sandbox URLs, and production URLs
6. Document all possible status codes and error responses

### 6.3 Changelog format

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

## 7. Autonomous Operation

### 7.1 Integration lifecycle

```
Detect new API version -> Fetch docs -> Implement new version -> Build & test locally
    -> Deploy to UAT -> Verification agent tests -> Feedback loop until all pass -> Release to production
```

### 7.2 Auto-update rules

- Monitor external API changelogs and versioning endpoints
- When a new API version is detected: create a new integrator version automatically
- The old version remains available and unchanged
- Notify platform administrators about new version availability
- Clients choose when to switch to the new version via the platform UI
- If an external API deprecates a version: warn all clients using that version 30 days in advance

### 7.3 Self-healing

- If an integrator fails health checks 5 consecutive times -> automatic restart
- If restart doesn't resolve -> roll back to previous healthy version
- If no healthy version exists -> alert human operator with full diagnostic logs
- On-premise agents: if cloud connection lost -> buffer locally -> auto-sync on reconnection

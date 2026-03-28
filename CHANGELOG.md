# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0] — 2026-03-28

Initial public release of the Open Integration Platform by Pinquark.com.

### Platform Core

- **API Gateway** — FastAPI-based gateway with tenant isolation, Row-Level Security (PostgreSQL), and AES-256-GCM credential vault
- **Flow Engine** — any-to-any rule engine connecting source events to destination actions across all connectors
- **Mapping Resolver** — hybrid field mapping (file-based defaults + per-tenant DB overrides, cached in Redis)
- **Credential Vault** — envelope encryption for all connector credentials at rest
- **Workflow Engine** — HTTP-triggered workflows with per-workflow client IP allowlists
- **Tenant Manager** — multi-tenant architecture with per-tenant API keys and RLS isolation
- **Admin Dashboard** — Angular application with embeddable `@pinquark/integrations` npm library
- **Verification Agent** — 3-tier health monitoring (readiness → auth → functional smoke tests) with APScheduler
- **SDK** — Python SDK for the Platform API (`sdk/python/`)

### Connectors — Courier (18)

| Connector | Version | Protocol |
|---|---|---|
| InPost | v1, v2, v3 | REST |
| DHL | v1 | REST |
| DHL Express | v1 | REST |
| DPD | v1 | SOAP |
| FedEx | v1 | REST |
| FedEx PL | v1 | REST |
| GLS | v1 | REST |
| FX Couriers | v1 | REST |
| GEIS | v1 | REST |
| Orlen Paczka | v1 | REST |
| Packeta | v1 | REST |
| Paxy | v1 | REST |
| Poczta Polska | v1 | REST |
| Raben | v1 | REST |
| Schenker | v1 | REST |
| Sellasist | v1 | REST |
| SUUS | v1 | REST |
| UPS | v1 | REST |

### Connectors — E-commerce (8)

| Connector | Version |
|---|---|
| Allegro | v1 |
| Amazon | v1 |
| Apilo | v1 |
| BaseLinker | v1 |
| IdoSell | v1 |
| Shoper | v1 |
| Shopify | v1 |
| WooCommerce | v1 |

### Connectors — ERP / WMS / AI / Other

| Connector | Category | Version |
|---|---|---|
| InsERT Nexo | ERP | v1 |
| Pinquark WMS | WMS | v1 |
| AI Agent (Gemini) | AI | v1 |
| Email Client | Other | v1 |
| SkanujFakture | Other | v1 |
| FTP/SFTP | Other | v1 |
| Slack | Other | v1 |
| BulkGate SMS | Other | v1 |
| AWS S3 | Other | v1 |

### Infrastructure

- Kubernetes manifests with HPA and Strimzi Kafka cluster (`k8s/`)
- Docker Compose for full local development stack
- VPS single-node deployment (Hetzner) with Let's Encrypt TLS
- On-premise agent for local ERP connectivity with Windows installer (`onpremise/`)
- Prometheus + Grafana + Alertmanager monitoring stack

### CI/CD

- GitHub Actions pipeline: Lint (Ruff) → Test (pytest >80%) → Security scan (pip-audit, npm audit, Trivy) → Build Docker → Push to GHCR → Deploy to VPS
- Gitleaks secret scanning on every push
- Dependabot for automated dependency updates

### Security

- TLS 1.2+ enforced on all external connections
- Non-root containers with pinned base images
- Multi-stage Docker builds
- AES-256-GCM envelope encryption for credentials at rest
- Per-tenant Row-Level Security in PostgreSQL

[v1.0.0]: https://github.com/pinquark/open-integration-platform/releases/tag/v1.0.0

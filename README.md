# Open Integration Platform by Pinquark.com

**Open-source integration hub that connects any system with any other system.**

Courier services, e-commerce platforms, ERP systems, WMS, automation — all connected through configurable flows and workflows with a visual dashboard.

[![CI](https://github.com/mateuszkalinowski-ops/Open-Integration-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mateuszkalinowski-ops/Open-Integration-Platform/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://python.org)
[![Angular](https://img.shields.io/badge/Angular-18+-red.svg)](https://angular.dev)

Try it instantly with `./setup.sh` — no manual configuration required.

---

## Why Pinquark?

| Feature | BaseLinker | Workato | Pinquark |
|---------|-----------|---------|----------|
| Open-source | No | No | **Yes (Apache 2.0)** |
| Self-hosted | No | No (enterprise on-prem available) | **Yes** |
| Pricing | From ~€50/mo | From ~$10k/year | **Free** |
| Connectors | 100+ (e-commerce focused) | 1000+ (enterprise IT) | 35 (logistics + e-commerce) |
| Any-to-any flows | No (hub-and-spoke) | Yes (recipes) | **Yes (Flow Engine)** |
| Visual workflow builder | Limited automation rules | Yes | **Yes (DAG-based, 18 node types)** |
| Visual field mapper | No | Yes | **Yes (drag & drop)** |
| Custom connectors | No | Connector SDK (closed) | **Yes (connector.yaml manifest)** |
| Zero platform-code connectors | No | No | **Yes** |
| Embeddable UI | No | Embedded iPaaS (extra cost) | **Yes (Angular library, free)** |
| API + SDK | REST only | REST | **REST + Python SDK** |
| On-premise ERP agents | No | Yes | **Yes (Docker-based)** |
| OAuth2 lifecycle | Via platform | Yes | **Yes (auto-refresh)** |
| Webhook ingestion | No | Yes | **Yes (signature verification)** |
| Connector health monitoring | No | Basic | **Yes (real-time, auto-disable)** |
| Automated verification | No | No | **Yes (3-tier: health → auth → functional)** |
| Audit trail | No | Yes | **Yes (entity + workflow versioning)** |
| Per-connector rate limiting | No | Yes | **Yes (token bucket)** |
| Connector version isolation | No | No | **Yes (multiple versions coexist)** |
| Polish/CEE system coverage | Strong | Weak | **Strong (InPost, Allegro, DPD PL, Poczta Polska, …)** |

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Pinquark Platform Core                       │
│                                                                  │
│  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────┐ │
│  │API Gateway│  │ Flow Engine │  │ Workflow │  │  Dashboard   │ │
│  │ (FastAPI) │  │ (any→any)   │  │  Engine  │  │ (Angular)    │ │
│  └────┬─────┘  └──────┬──────┘  └────┬─────┘  └──────────────┘ │
│       │               │              │                           │
│  ┌────┴───────────────┴──────────────┴───────────────────────┐  │
│  │  Connector Registry  │  Credential Vault  │  Mapping       │  │
│  │  (connector.yaml)    │  (AES-256-GCM)     │  Resolver      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Verification Agent (3-tier: health → auth → functional) │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────────┐
     │                     │                         │
┌────┴──────┐    ┌─────────┴─────────┐    ┌──────────┴──────────┐
│  Courier  │    │    E-commerce     │    │  ERP / WMS / Other  │
│  (18)     │    │    (8)            │    │                     │
│ InPost    │    │ Allegro           │    │ Pinquark WMS        │
│ DHL       │    │ Amazon            │    │ InsERT Nexo         │
│ DPD       │    │ Apilo             │    │ AI Agent            │
│ FedEx     │    │ BaseLinker        │    │ SkanujFakture       │
│ GLS       │    │ Shopify           │    │ Email Client        │
│ UPS       │    │ WooCommerce       │    │ FTP/SFTP            │
│ Raben     │    │ Shoper            │    │ Slack               │
│ 11 more…  │    │ IdoSell           │    │ BulkGate SMS        │
└───────────┘    └───────────────────┘    └─────────────────────┘
```

**Every system is an equal peer.** Connectors act as both **source** (emit events) and **destination** (receive actions). The Flow Engine connects any source event to any destination action.

**Zero-impact connector architecture.** Adding a new connector requires only creating a folder with a `connector.yaml` manifest — no platform code changes needed. The platform discovers connectors automatically at startup.

## Screenshots

### Connector catalog

Browse all connectors with search, status, category, and country filters.

![Connectors list](docs/Screenshots/connectors-list.png)

### Connector detail

Version selector, interactive Swagger UI, capabilities, events, actions, and configuration — all loaded from the connector service.

![Connector detail](docs/Screenshots/connector.png)

### Credentials

Manage credentials for connected systems. Each card shows the connector, config fields, last update time, and real-time connection health status.

![Credentials](docs/Screenshots/credentials.png)

### Flows & Workflows

Create simple flows (source event to destination action) or advanced DAG-based workflows with multiple node types.

![Workflow list](docs/Screenshots/workflow-list.png)

### Visual Workflow Builder

Drag-and-drop DAG editor with 18 node types — triggers, conditions, actions, AI nodes, loops, and more. Test and activate workflows from the builder.

![Workflow builder](docs/Screenshots/workflow.png)

### Operation Log

Monitor all workflow and flow executions with status, duration, connector info, and error details. Filter by status, type, connector, and date range.

![Operation log](docs/Screenshots/operation-log.png)

### Execution details

Drill into any execution to see the workflow graph with per-node status (success, failed, filtered, not executed), trigger data, and GDPR-compliant data masking.

![Operation log details](docs/Screenshots/operation-log-details.png)

## Quick Start

### Self-hosted (Docker Compose)

```bash
git clone https://github.com/pinquark/open-integration-platform.git
cd open-integration-platform
./setup.sh
```

`setup.sh` generates a `.env` with secure random keys (encryption key, JWT secret, DB password, admin secret, internal secret) and starts all services via Docker Compose.

Open `http://localhost:3000` for the dashboard.

### Embed in your Angular app

```bash
npm install @pinquark/integrations
```

```typescript
import { PinquarkIntegrationsModule } from '@pinquark/integrations';

@NgModule({
  imports: [
    PinquarkIntegrationsModule.forRoot({
      apiUrl: 'http://localhost:8080',
      apiKey: environment.pinquarkApiKey,
    })
  ]
})
export class AppModule {}
```

```html
<pinquark-connector-list [category]="'courier'"></pinquark-connector-list>
<pinquark-credential-form [connectorId]="'inpost'"></pinquark-credential-form>
```

### Use via Python SDK

```bash
pip install pinquark-sdk
```

```python
from pinquark_sdk import PinquarkClient

client = PinquarkClient(api_key="pk_live_xxx")

# Create a shipment via any courier
shipment = await client.courier.create_shipment(
    connector="inpost",
    receiver={"name": "Jan Kowalski", "phone": "+48600100200",
              "address": {"city": "Warszawa", "postal_code": "00-001"}},
    parcels=[{"weight": 2.5, "width": 30, "height": 20, "length": 40}],
)

# Get the label
label_pdf = await client.courier.get_label(shipment.waybill_number)
```

## Flow Engine — connect anything to anything

Define flows that trigger actions across systems automatically:

```yaml
# When an Allegro order arrives, create an InPost shipment
flows:
  - name: "Allegro -> InPost"
    source:
      connector: allegro
      event: order.created
      filter:
        delivery_method: inpost_paczkomat
    destination:
      connector: inpost
      action: shipment.create
    mapping:
      - from: order.buyer.name      -> to: receiver.first_name
      - from: order.buyer.address   -> to: receiver.address
      - from: order.point_id        -> to: extras.target_point
```

Flows and workflows are configured via the dashboard UI or REST API. Default field mappings ship with each connector; tenants can override them per-instance.

## Connectors — 35 and growing

Every connector is a self-contained microservice with its own API, versioning, and documentation. Browse them all in the [dashboard](#connector-catalog) or via the REST API.

| Category | # | Connectors |
|----------|---|------------|
| **Courier** | 18 | InPost (v1–v3) · DHL · DHL Express · DPD · FedEx · FedEx PL · FX Couriers · GLS · UPS · Poczta Polska · Orlen Paczka · Packeta · Paxy · Raben Group · DB Schenker · Geis · SUUS · SellAsist |
| **E-commerce** | 8 | Allegro · Amazon · Apilo · BaseLinker · Shopify · WooCommerce · Shoper · IdoSell |
| **ERP** | 1 | InsERT Nexo (Subiekt) — hybrid: on-premise agent + cloud connector |
| **WMS** | 1 | Pinquark WMS |
| **AI** | 1 | AI Agent (Gemini) — risk analysis, courier recommendations, data extraction |
| **Other** | 6 | Email Client (IMAP/SMTP) · SkanujFakture (invoice OCR + KSeF) · FTP/SFTP · Slack · BulkGate SMS · Amazon S3 |

> **Coming soon:** PrestaShop, WAPRO, Comarch ERP, SAP, enova365, and more.
>
> See [docs/CONNECTORS.md](docs/CONNECTORS.md) for full configuration reference.

## Zero-impact connector architecture

Adding a new connector requires **zero changes** to the platform core. Each connector is fully defined by its `connector.yaml` manifest:

```yaml
name: my-connector
category: ecommerce
version: 1.0.0
display_name: "My Connector"
service_name: connector-my-connector

action_routes:
  order.list:
    method: GET
    path: /orders
    query_from_payload: [account_name, page, page_size]

credential_validation:
  required_fields: [api_key]
  test_request:
    method: GET
    url_template: "{api_url}/ping"
    headers_template:
      Authorization: "Bearer {api_key}"
    success_status: 200
```

The platform reads `connector.yaml` at startup for action routing, credential provisioning, credential validation, and verification agent test discovery. No platform files (`gateway.py`, `action_dispatcher.py`, `discovery.py`) need modification.

See [docs/CONNECTOR-DEVELOPMENT.md](docs/CONNECTOR-DEVELOPMENT.md) for the full connector.yaml field reference.

## On-premise agents

For ERP systems that run behind firewalls (InsERT Nexo, WAPRO, SAP), the platform provides a Docker-based on-premise agent:

```
┌──────────────────────────┐
│    Client's Network      │
│                          │
│  ┌─────────┐ ┌────────┐ │         ┌─────────────────┐
│  │Local ERP│◀▶│On-Prem │─│────────▶│ Pinquark Cloud  │
│  │(Nexo)   │ │Agent   │ │  HTTPS  │ Integration Hub  │
│  └─────────┘ └────────┘ │         └─────────────────┘
│                  │       │
│             ┌────┴────┐  │
│             │ SQLite  │  │
│             └─────────┘  │
└──────────────────────────┘
```

- Auto-update, offline resilience (local queue), heartbeat monitoring
- Windows installer wizard for easy client deployment
- Downloadable from the connector's detail page in the dashboard

## Verification agent

A built-in 3-tier verification agent continuously monitors all connectors:

| Tier | Scope | Checks |
|------|-------|--------|
| **1 — Infrastructure** | All connectors | `/health`, `/readiness`, `/docs` |
| **2 — Authentication** | With credentials | Account provisioning, auth status, connection status |
| **3 — Functional** | Per-connector | All endpoints, CRUD cycles, error paths, response times |

Runs on schedule (default: every 7 days), on-demand via API, or from the dashboard.

## Project Structure

```
├── platform/                  # Core platform (API Gateway, Flow & Workflow Engine)
│   ├── api/                   # FastAPI application + credential validator
│   ├── core/                  # Business logic (action dispatcher, connector registry,
│   │                          #   flow engine, workflow engine, mapping resolver)
│   ├── db/                    # PostgreSQL models & migrations
│   ├── verification-agent/    # 3-tier connector verification service
│   └── dashboard/             # Angular workspace
│       ├── projects/
│       │   ├── integrations-lib/   # @pinquark/integrations (npm library)
│       │   └── dashboard-app/      # Standalone dashboard
│       └── angular.json
│
├── integrators/               # All connectors by category
│   ├── courier/               # InPost, DHL, DPD, FedEx, GLS, UPS, Raben, ...
│   ├── ecommerce/             # Allegro, Amazon, Apilo, BaseLinker, Shopify, ...
│   ├── erp/                   # InsERT Nexo (on-premise + cloud)
│   ├── wms/                   # Pinquark WMS
│   ├── ai/                    # AI Agent (Gemini)
│   └── other/                 # Email, SkanujFakture, FTP/SFTP, Slack, BulkGate
│
├── shared/                    # Shared Python library (pinquark-common)
│   └── python/
│       └── pinquark_common/   # Interfaces, schemas, utilities
│
├── sdk/                       # Client SDKs
│   └── python/                # pinquark-sdk (PyPI)
│
├── onpremise/                 # On-premise agent for local ERP connectivity
│   └── nexo-agent/            # InsERT Nexo agent (Python.NET + FastAPI)
│
├── docs/                      # Per-connector documentation & architecture
│   ├── ARCHITECTURE.md        # System architecture & scalability
│   ├── CONNECTORS.md          # Connector configuration reference
│   ├── courier/
│   ├── ecommerce/
│   ├── erp/
│   └── other/
│
├── k8s/                       # Kubernetes deployment configs
├── ci/                        # CI/CD pipelines
├── monitoring/                # Prometheus, Grafana configs
├── AGENTS.md                  # Agent guidelines, coding standards, full reference
└── README.md
```

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Alembic, Pydantic v2
- **Database**: PostgreSQL 16 (RLS for multi-tenant), Redis 7 (cache, rate limiting)
- **Frontend**: Angular 18+, Angular Material, TypeScript strict
- **Messaging**: Kafka / Redis Streams (event bus)
- **Connectors**: FastAPI microservices, httpx (async HTTP), zeep (SOAP)
- **On-premise**: Python.NET (pythonnet) for .NET SDK bridges, SQLite for local queuing
- **Infrastructure**: Docker, Kubernetes, Helm, Prometheus, Grafana
- **Security**: AES-256-GCM credential encryption, TLS 1.2+, non-root containers

## Documentation

| Document | Path | Description |
|----------|------|-------------|
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, scalability, deployment |
| Connectors | [docs/CONNECTORS.md](docs/CONNECTORS.md) | Configuration reference for all connectors |
| Connector Development | [docs/CONNECTOR-DEVELOPMENT.md](docs/CONNECTOR-DEVELOPMENT.md) | connector.yaml spec, SDK, verification, testing guide |
| Standards | [docs/STANDARDS.md](docs/STANDARDS.md) | Docker, CI/CD, security, monitoring, documentation |
| Agent Guidelines | [AGENTS.md](AGENTS.md) | Coding standards, CI/CD, security, interfaces |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and how to create new connectors.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

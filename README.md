# Open Integration Platform by Pinquark.com

**Open-source integration hub that connects any system with any other system.**

Courier services, e-commerce platforms, ERP systems, WMS, automation — all connected through configurable flows with a visual dashboard.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://python.org)
[![Angular](https://img.shields.io/badge/Angular-18+-red.svg)](https://angular.dev)

---

## Why Pinquark?

| Feature | BaseLinker | Pinquark |
|---------|-----------|----------|
| Self-hosted | No | Yes |
| Open-source | No | Yes (Apache 2.0) |
| Any-to-any flows | No (hub-and-spoke) | Yes (Flow Engine) |
| Plugin system | Closed | Open (connector.yaml) |
| Embeddable UI | No | Yes (Angular library) |
| API + SDK | REST only | REST + Python/JS SDK |
| Custom connectors | No | Yes |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Pinquark Platform Core                    │
│                                                             │
│  ┌──────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│  │API Gateway│  │ Flow Engine │  │  Admin Dashboard       │ │
│  │ (FastAPI) │  │ (any→any)   │  │  (Angular / npm lib)   │ │
│  └────┬─────┘  └──────┬──────┘  └────────────────────────┘ │
│       │               │                                     │
│  ┌────┴───────────────┴──────────────────────────────────┐  │
│  │  Connector Registry  │  Credential Vault  │  Mappings │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────────┐
        │                  │                      │
  ┌─────┴─────┐    ┌──────┴──────┐    ┌──────────┴──────────┐
  │  Courier   │    │  E-commerce │    │  ERP / WMS / Other  │
  │            │    │             │    │                     │
  │ InPost     │    │ Allegro     │    │ Pinquark WMS        │
  │ DHL        │    │ Shopify     │    │ WAPRO               │
  │ DPD        │    │ WooCommerce │    │ SAP                 │
  │ FedEx      │    │ Shoper      │    │ Comarch             │
  │ GLS        │    │ IdoSell     │    │ Custom              │
  │ UPS        │    │ BaseLinker  │    │                     │
  │ 12 more... │    │ ...         │    │                     │
  └────────────┘    └─────────────┘    └─────────────────────┘
```

**Every system is an equal peer.** Connectors act as both **source** (emit events) and **destination** (receive actions). The Flow Engine connects any source event to any destination action.

## Screenshots

<table>
  <tr>
    <td><a href="./docs/Screenshots/connectors-list.png"><img src="./docs/Screenshots/connectors-list.png" alt="Connectors list" width="260"/></a></td>
    <td><a href="./docs/Screenshots/connector.png"><img src="./docs/Screenshots/connector.png" alt="Connector details" width="260"/></a></td>
    <td><a href="./docs/Screenshots/credentials.png"><img src="./docs/Screenshots/credentials.png" alt="Credentials management" width="260"/></a></td>
  </tr>
  <tr>
    <td style="text-align:center;">Connectors</td>
    <td style="text-align:center;">Connector Details</td>
    <td style="text-align:center;">Credentials</td>
  </tr>
  <tr>
    <td><a href="./docs/Screenshots/workflow-list.png"><img src="./docs/Screenshots/workflow-list.png" alt="Workflow list" width="260"/></a></td>
    <td><a href="./docs/Screenshots/workflow.png"><img src="./docs/Screenshots/workflow.png" alt="Workflow editor" width="260"/></a></td>
    <td><a href="./docs/Screenshots/operation-log.png"><img src="./docs/Screenshots/operation-log.png" alt="Operation log" width="260"/></a></td>
  </tr>
  <tr>
    <td style="text-align:center;">Flows &amp; Workflows</td>
    <td style="text-align:center;">Workflow Editor</td>
    <td style="text-align:center;">Operation Log</td>
  </tr>
  <tr>
    <td><a href="./docs/Screenshots/operation-log-details.png"><img src="./docs/Screenshots/operation-log-details.png" alt="Operation log details" width="260"/></a></td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td style="text-align:center;">Execution Details</td>
    <td></td>
    <td></td>
  </tr>
</table>

## Quick Start

### Self-hosted (Docker Compose)

```bash
git clone https://github.com/pinquark/integrations.git
cd integrations
cp .env.example .env
docker compose -f docker-compose.prod.yml up -d
```

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
      apiUrl: 'https://api.pinquark.com',
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

Flows are configured via the dashboard UI or REST API. Default field mappings ship with each connector; tenants can override them.

## Connectors — 28 and growing

Every connector is a self-contained microservice with its own API, versioning, and documentation. Browse them all in the [dashboard](#screenshots) or via the REST API.

| Category | # | Connectors |
|----------|---|------------|
| **Courier** | 18 | InPost (v1–v3) · DHL · DHL Express · DPD · FedEx · FedEx PL · GLS · UPS · Poczta Polska · Orlen Paczka · Packeta · Paxy · Raben Group · DB Schenker · Geis · SUUS · SellAsist |
| **E-commerce** | 6 | Allegro · BaseLinker · Shopify · WooCommerce · Shoper · IdoSell |
| **WMS** | 1 | Pinquark WMS |
| **AI** | 1 | AI Agent (Gemini) — risk analysis, courier recommendations, data extraction |
| **Other** | 2 | Email Client (IMAP/SMTP) · SkanujFakture (invoice OCR + KSeF) |

> **Coming soon:** PrestaShop, WAPRO, Comarch ERP, SAP, Subiekt GT, and more.
>
> See [docs/CONNECTORS.md](docs/CONNECTORS.md) for full configuration reference.

## Project Structure

```
├── platform/                  # Core platform (API Gateway, Flow Engine)
│   ├── api/                   # FastAPI application
│   ├── core/                  # Business logic (flows, mappings, tenants)
│   ├── db/                    # PostgreSQL models & migrations
│   └── dashboard/             # Angular workspace
│       ├── projects/
│       │   ├── integrations-lib/   # @pinquark/integrations (npm library)
│       │   └── dashboard-app/      # Standalone dashboard
│       └── angular.json
│
├── integrators/               # All connectors by category
│   ├── courier/               # InPost, DHL, DPD, FedEx, GLS, UPS, ...
│   ├── ecommerce/             # Allegro, (Shopify, WooCommerce, ...)
│   ├── erp/                   # (WAPRO, SAP, Comarch, ...)
│   └── other/                 # Custom connectors
│
├── shared/                    # Shared Python library (pinquark-common)
│   └── python/
│       └── pinquark_common/   # Interfaces, schemas, utilities
│
├── sdk/                       # Client SDKs
│   ├── python/                # pinquark-sdk (PyPI)
│   └── javascript/            # @pinquark/sdk (npm)
│
├── docs/                      # Per-connector documentation
├── k8s/                       # Kubernetes deployment configs
├── ci/                        # CI/CD pipelines
└── monitoring/                # Prometheus, Grafana configs
```

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Alembic, Pydantic v2
- **Database**: PostgreSQL 16 (RLS for multi-tenant), Redis 7 (cache, rate limiting)
- **Frontend**: Angular 18+, Angular Material, TypeScript strict
- **Messaging**: Kafka / Redis Streams (event bus)
- **Connectors**: FastAPI microservices, httpx (async HTTP), zeep (SOAP)
- **Infrastructure**: Docker, Kubernetes, Helm, Prometheus, Grafana

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and how to create new connectors.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

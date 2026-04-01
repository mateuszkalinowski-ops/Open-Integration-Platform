# enova365 — Integration Guide

## Overview

This integration connects **enova365 ERP** (by Soneta sp. z o.o.) with the Pinquark Integration Platform. enova365 is a comprehensive Polish ERP system used by over 22,000 organizations, covering finance & accounting, trade & warehouse, payroll & HR, CRM, production, business intelligence, and more.

### Architecture

**Scenario A — enova365 Multi (cloud / accessible over network):**

```
┌──────────────────────────┐              ┌──────────────────────┐
│  enova365 Multi          │              │  Pinquark Cloud      │
│  (IIS + Soneta WebAPI)   │◄───REST/JWT──│  enova365 Connector  │
│                          │    HTTPS     │  (erp/enova365)      │
│  MS SQL Server           │              │                      │
└──────────────────────────┘              └──────────────────────┘
```

**Scenario B — enova365 Standard (on-premise, no public access):**

```
┌─────────────────────────────────────────────┐
│  Client's Windows Server                     │
│                                              │
│  ┌──────────────┐    ┌────────────────────┐ │
│  │ enova365     │    │ On-Premise Agent   │ │
│  │ Standard +   │◄──►│ (reverse proxy +   │ │     ┌──────────────────┐
│  │ Soneta WebAPI│    │  sync service)     │─│─►───│  Pinquark Cloud  │
│  │ (IIS)       │    │                    │ │HTTPS│  enova365 Connector│
│  │ MS SQL      │    └────────────────────┘ │     └──────────────────┘
│  └──────────────┘                           │
└─────────────────────────────────────────────┘
```

**Cloud Connector** (`integrators/erp/enova365/v1.0.0/`):
- Communicates with enova365 via Soneta WebAPI (REST, JWT tokens)
- Supports both cloud (Multi) and on-premise (Standard) deployments
- Implements the ERP integration interface

## Supported Modules

| enova365 Module | Integration Scope |
|---|---|
| Handel i magazyn (Trade & Warehouse) | Products, stock levels, warehouse documents |
| Finanse i księgowość (Finance & Accounting) | Sales documents, invoices, payments |
| Sprzedaż i CRM (Sales & CRM) | Contractors, orders, CRM contacts |
| Kadry i płace (Payroll & HR) | Employee data (read-only) |
| Business Intelligence | Reports, KPIs (read-only) |

## Supported Entities

| Entity | Operations | enova365 Module |
|---|---|---|
| Contractors (Kontrahenci) | CRUD + search by NIP | Handel / CRM |
| Products (Towary) | CRUD + search by EAN/SKU | Handel i magazyn |
| Sales Documents (Dokumenty sprzedaży) | List, Get, Create (Invoice, Receipt, Proforma) | Finanse i księgowość |
| Warehouse Documents (Dokumenty magazynowe) | List, Get, Create (PZ, WZ, MM) | Handel i magazyn |
| Orders (Zamówienia) | CRUD (from customers / to suppliers) | Handel |
| Stock Levels (Stany magazynowe) | Read (by warehouse, by product) | Handel i magazyn |

## Prerequisites

1. **enova365** instance — Multi (cloud/browser) or Standard (on-premise)
2. **Soneta WebAPI module** — licensed and enabled (or legacy Harmonogram Zadań license)
3. **IIS server** configured with enova365 WebAPI services
4. **MS SQL Server** — 2016, 2017, 2019, 2022, or 2025 (Standard or Express)
5. **JWT credentials** — operator login/password for token-based authentication (since enova365 v11.1)
6. **.NET 8 Runtime** on the enova365 server
7. **enova365 version** — 2512+ recommended

## Deployment

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your values:
# - enova365 API URL
# - OAuth2 client credentials or API key
# - enova365 database/company name
```

### 2. Build and run (Docker)

```bash
docker compose up -d connector-enova365

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## API Endpoints

### System
- `GET /health` — Health check
- `GET /readiness` — Readiness check
- `GET /docs` — Swagger UI

### Contractors
- `GET /contractors?page=1&page_size=50&search=` — List
- `GET /contractors/{id}` — Get by ID
- `GET /contractors/by-nip/{nip}` — Get by NIP
- `POST /contractors` — Create
- `PUT /contractors/{id}` — Update
- `DELETE /contractors/{id}` — Delete

### Products
- `GET /products?page=1&search=` — List
- `GET /products/{id}` — Get by ID
- `GET /products/by-ean/{ean}` — Get by EAN
- `POST /products` — Create
- `PUT /products/{id}` — Update
- `DELETE /products/{id}` — Delete

### Documents
- `GET /documents/sales` — List sales documents
- `GET /documents/sales/{id}` — Get by ID
- `POST /documents/sales` — Create (invoice, receipt, proforma)
- `GET /documents/warehouse` — List warehouse documents
- `POST /documents/warehouse` — Create (PZ, WZ, MM)

### Orders
- `GET /orders?order_type=from_customer` — List
- `GET /orders/{id}` — Get by ID
- `POST /orders` — Create
- `PUT /orders/{id}` — Update

### Stock
- `GET /stock?warehouse=` — All stock levels
- `GET /stock/{product_id}` — Stock for single product

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `ENOVA_API_URL` | — | Soneta WebAPI base URL (e.g. `https://enova.client.local:5007/api`) |
| `ENOVA_OPERATOR_LOGIN` | — | enova365 operator login (for JWT token) |
| `ENOVA_OPERATOR_PASSWORD` | — | enova365 operator password |
| `ENOVA_DATABASE_NAME` | — | enova365 company database name in MS SQL |
| `ENOVA_SYNC_INTERVAL_SECONDS` | `300` | Background sync interval |
| `ENOVA_DEFAULT_WAREHOUSE` | — | Default warehouse symbol |
| `ENOVA_LOG_LEVEL` | `INFO` | Log level |
| `ENOVA_TOKEN_REFRESH_SECONDS` | `3600` | JWT token refresh interval |

## Troubleshooting

### "Authentication failed"
- Verify OAuth2 client credentials or API key in enova365 administration panel
- Check that API access is enabled for the configured user/application
- Ensure the enova365 instance URL is correct and reachable

### "Database not found"
- Verify `ENOVA_DATABASE_NAME` matches the company database name in enova365
- Check that the API user has access to the specified database

### "Module not available"
- Some enova365 modules require separate licenses (e.g., Handel, CRM, BI)
- Verify the required modules are licensed and enabled in the enova365 instance

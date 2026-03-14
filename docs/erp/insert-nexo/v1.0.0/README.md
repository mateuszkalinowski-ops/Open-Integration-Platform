# InsERT Nexo (Subiekt) — Integration Guide

## Overview

This integration connects **InsERT Nexo ERP (Subiekt)** with the Pinquark Integration Platform using a hybrid on-premise/cloud architecture.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Client's Windows Server                             │
│                                                      │
│  ┌──────────────┐    ┌─────────────────────────────┐│
│  │  InsERT Nexo │◄──►│  On-Premise Agent           ││
│  │  (SQL Server) │    │  Python + FastAPI            ││    ┌──────────────────┐
│  └──────────────┘    │  + pythonnet (SDK bridge)    ││───►│  Pinquark Cloud  │
│                      │  + SQLite (offline queue)    ││HTTPS│  Nexo Connector  │
│                      │  + Heartbeat & Sync          ││    │  (erp/insert-nexo)│
│                      └─────────────────────────────┘│    └──────────────────┘
└─────────────────────────────────────────────────────┘
```

**On-Premise Agent** (`onpremise/nexo-agent/`):
- Runs on Windows (required by Nexo SDK)
- Uses `pythonnet` to call InsERT Nexo SDK DLLs from Python
- Exposes REST API for all ERP operations
- Sends heartbeats and syncs data to cloud

**Cloud Connector** (`integrators/erp/insert-nexo/v1.0.0/`):
- Runs in the cloud as a standard integrator
- Proxies platform requests to the on-premise agent
- Receives sync data and heartbeats from agents

## Supported Entities

| Entity | Operations | Nexo Interface |
|---|---|---|
| Contractors (Podmioty) | CRUD + search by NIP | `IPodmioty` / `IPodmiot` |
| Products (Asortyment) | CRUD + search by EAN | `IAsortymenty` / `IAsortyment` |
| Sales Documents | List, Get, Create (Invoice, Receipt, Proforma) | `IDokumentySprzedazy` |
| Warehouse Documents | List, Create (WZ, PZ) | `IWydaniaZewnetrzne` / `IPrzyjeciaZewnetrzne` |
| Orders | CRUD (from customers / to suppliers) | `IZamowieniaOdKlientow` / `IZamowieniaDoDostawcow` |
| Stock Levels | Read (by warehouse, by product) | `IAsortymenty.StanyMagazynowe` |

## Prerequisites

### On the client's Windows server:

1. **InsERT Nexo** installed and running (Subiekt module)
2. **SQL Server** with the Nexo database accessible
3. **InsERT Nexo SDK** (`nexoSDK`) — extract to `C:\nexoSDK\`
4. **Docker Desktop for Windows** (with Windows containers mode)
5. **.NET 8.0 Runtime** (installed in Docker image)
6. **Python 3.12** (installed in Docker image)

### Nexo SDK Setup

Extract the SDK so the DLL files are at:
```
C:\nexoSDK\Bin\InsERT.Moria.API.dll
C:\nexoSDK\Bin\InsERT.Moria.ModelDanych.dll
C:\nexoSDK\Bin\InsERT.Moria.Sfera.dll
C:\nexoSDK\Bin\InsERT.Mox.Core.dll
```

## Deployment

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your values:
# - SQL Server connection details
# - Nexo operator credentials
# - Cloud platform URL and API key
```

### 2. Build and run (Docker)

```powershell
# Switch Docker to Windows containers
& $Env:ProgramFiles\Docker\Docker\DockerCli.exe -SwitchWindowsEngine

# Build and start
docker compose up -d

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

### 3. Run without Docker

```powershell
pip install -r requirements.txt
$env:NEXO_SQL_SERVER="(local)\INSERTNEXO"
$env:NEXO_SQL_DATABASE="Nexo_demo"
$env:NEXO_OPERATOR_LOGIN="Admin"
$env:NEXO_OPERATOR_PASSWORD="password"
$env:NEXO_SDK_BIN_PATH="C:\nexoSDK\Bin"

uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### System
- `GET /health` — Health check
- `GET /readiness` — Readiness check (pings Nexo)
- `GET /connection/status` — Nexo connection details
- `POST /connection/reconnect` — Force reconnection
- `GET /docs` — Swagger UI

### Contractors
- `GET /contractors?page=1&page_size=50&search=` — List
- `GET /contractors/{symbol}` — Get by symbol
- `GET /contractors/by-nip/{nip}` — Get by NIP
- `POST /contractors` — Create
- `PUT /contractors/{symbol}` — Update
- `DELETE /contractors/{symbol}` — Delete

### Products
- `GET /products?page=1&search=&group=` — List
- `GET /products/{symbol}` — Get by symbol
- `GET /products/by-ean/{ean}` — Get by EAN
- `POST /products` — Create
- `PUT /products/{symbol}` — Update
- `DELETE /products/{symbol}` — Delete

### Documents
- `GET /documents/sales` — List sales documents
- `GET /documents/sales/{doc_id}` — Get by ID
- `POST /documents/sales` — Create (invoice, receipt, proforma)
- `GET /documents/warehouse/issues` — List warehouse issues (WZ)
- `GET /documents/warehouse/receipts` — List warehouse receipts (PZ)
- `POST /documents/warehouse/issue` — Create WZ
- `POST /documents/warehouse/receipt` — Create PZ

### Orders
- `GET /orders?order_type=from_customer` — List
- `GET /orders/{order_id}` — Get by ID
- `POST /orders` — Create
- `PUT /orders/{order_id}` — Update

### Stock
- `GET /stock?warehouse=MAG&only_available=false` — All stock levels
- `GET /stock/{product_symbol}` — Stock for single product

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `NEXO_AGENT_ID` | `nexo-agent-001` | Unique agent identifier |
| `NEXO_SQL_SERVER` | `(local)\INSERTNEXO` | SQL Server instance |
| `NEXO_SQL_DATABASE` | `Nexo_demo` | Database name |
| `NEXO_SQL_AUTH_WINDOWS` | `true` | Use Windows Authentication |
| `NEXO_OPERATOR_LOGIN` | — | Nexo operator login |
| `NEXO_OPERATOR_PASSWORD` | — | Nexo operator password |
| `NEXO_PRODUCT` | `Subiekt` | Nexo product module |
| `NEXO_SDK_BIN_PATH` | `C:\nexoSDK\Bin` | Path to SDK DLLs |
| `NEXO_AGENT_DEFAULT_WAREHOUSE` | `MAG` | Default warehouse |
| `NEXO_AGENT_DEFAULT_BRANCH` | `CENTRALA` | Default branch |
| `CLOUD_PLATFORM_URL` | `http://localhost:8080` | Cloud platform URL |
| `CLOUD_API_KEY` | — | Cloud API key |
| `NEXO_AGENT_SYNC_INTERVAL_SECONDS` | `300` | Sync interval |
| `NEXO_AGENT_HEARTBEAT_INTERVAL_SECONDS` | `60` | Heartbeat interval |

## Troubleshooting

### "SDK assembly not found"
Ensure `NEXO_SDK_BIN_PATH` points to the directory containing `InsERT.Moria.API.dll`. When using Docker, verify the volume mount: `-v C:\nexoSDK\Bin:C:\nexo-sdk:ro`

### "Could not connect to InsERT Nexo"
- Verify SQL Server is running and accessible
- Check the database name matches the Nexo installation
- Verify operator credentials are correct
- Ensure the Nexo product (Subiekt) is licensed

### "CLR initialization failed"
- Ensure .NET 8.0 Runtime is installed
- Set `PYTHONNET_RUNTIME=coreclr` environment variable
- Verify `DOTNET_ROOT` points to the .NET installation

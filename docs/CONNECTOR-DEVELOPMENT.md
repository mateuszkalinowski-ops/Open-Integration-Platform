# Open Integration Platform — Connector Development Guide

> **Parent document**: [AGENTS.md](../AGENTS.md) (core agent rules)
> **Related**: [ARCHITECTURE.md](ARCHITECTURE.md) | [CONNECTORS.md](CONNECTORS.md) | [STANDARDS.md](STANDARDS.md)

This file contains the full reference for building new connectors and writing verification tests. Agents should read this when implementing or verifying connectors.

---

## Table of contents

1. [Connector Manifest (connector.yaml)](#1-connector-manifest-connectoryaml)
2. [Implementation Agent Workflow](#2-implementation-agent-workflow)
3. [Verification & Maintenance Agent](#3-verification--maintenance-agent)
4. [Integration Interfaces](#4-integration-interfaces)

---

## 1. Connector Manifest (connector.yaml)

Every connector MUST include a `connector.yaml` in its version root. The manifest is the **single source of truth** for all connector configuration -- the platform reads it at startup and requires zero per-connector code. Adding a new connector means creating its folder with a `connector.yaml`; no platform files need to change.

### 1.1 Full example

```yaml
name: inpost
category: courier
version: 3.0.0
display_name: "InPost"
description: "InPost courier integration - Paczkomaty, Kurier, Returns"
interface: courier

# Docker service name (convention: connector-{name})
service_name: connector-inpost

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

# Action routing -- tells the platform how to call each action on the connector
action_routes:
  shipment.create:
    method: POST
    path: /shipments
  label.get:
    method: GET
    path: /shipments/{shipment_id}/label
  shipment.cancel:
    method: POST
    path: /shipments/{shipment_id}/cancel
  pickup_points.list:
    method: GET
    path: /pickup-points
  return.create:
    method: POST
    path: /returns
  rates.get:
    method: POST
    path: /rates

# Credential validation -- how the platform validates credentials for this connector
credential_validation:
  required_fields: [organization_id, access_token]
  test_request:
    method: GET
    url_template: "{base_url}/v1/organizations/{organization_id}/shipments"
    headers_template:
      Authorization: "Bearer {access_token}"
    params_template:
      per_page: "1"
    success_status: 200
    defaults:
      base_url: "https://api-shipx-pl.easypack24.net"
    sandbox:
      flag: sandbox_mode
      base_url: "https://sandbox-api-shipx-pl.easypack24.net"

health_endpoint: /health
docs_url: /docs
```

### 1.2 Field reference


| Field                     | Required | Description                                                               |
| ------------------------- | -------- | ------------------------------------------------------------------------- |
| `name`                    | Yes      | Unique connector identifier (kebab-case)                                  |
| `category`                | Yes      | One of: `courier`, `ecommerce`, `erp`, `wms`, `ai`, `automation`, `other` |
| `version`                 | Yes      | Semantic version                                                          |
| `display_name`            | Yes      | Human-readable name                                                       |
| `description`             | Yes      | Short description                                                         |
| `interface`               | Yes      | Category interface type                                                   |
| `service_name`            | No       | Docker service name (default: `connector-{name}`)                         |
| `capabilities`            | No       | List of supported capabilities                                            |
| `events`                  | No       | List of events the connector emits                                        |
| `actions`                 | No       | List of actions the connector accepts                                     |
| `config_schema`           | No       | Required/optional configuration fields                                    |
| `action_routes`           | No       | Maps action names to HTTP method + path on the connector                  |
| `credential_provisioning` | No       | How credentials are provisioned on the connector (see below)              |
| `credential_validation`   | No       | How the platform validates credentials (see below)                        |
| `payload_hints`           | No       | Field coercion hints (list fields, enum mappings)                         |
| `event_fields`            | No       | Per-event field schemas for workflow builder                              |
| `action_fields`           | No       | Per-action input field schemas                                            |
| `output_fields`           | No       | Per-action output field schemas                                           |


### 1.3 action_routes

Each entry maps an action name to its HTTP endpoint on the connector:

```yaml
action_routes:
  document.upload:
    method: POST
    path: /companies/{company_id}/documents
    query_from_payload: [account_name, single_document]
    multipart: true  # sends file as multipart/form-data
```

Path parameters like `{company_id}` are resolved from the action payload. Fields listed in `query_from_payload` are moved from the body to query string parameters.

### 1.4 credential_provisioning

Defines how the platform provisions credentials on the connector before dispatching actions:


| Mode             | Description                                                                                           |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| `account`        | POST credentials to `account_endpoint` (e.g. `/accounts`), inject `payload_field` into action payload |
| `inject`         | Inject credential fields flat into action payload                                                     |
| `inject_nested`  | Inject credentials as `payload[inject_key] = {...}`                                                   |
| `none` / omitted | Default: set `account_name` from credentials                                                          |


```yaml
credential_provisioning:
  mode: account
  account_endpoint: /accounts
  payload_field: account_name
  credential_mapping:
    name: account_name
    login: login
    password: password
    api_url:
      source: api_url
      default: "https://example.com/api"
```

### 1.5 credential_validation

Defines how the platform validates credentials when a user stores them:

```yaml
credential_validation:
  required_fields: [login, password]
  # Option A: HTTP test request
  test_request:
    method: GET
    url_template: "{api_url}/users/currentUser"
    auth: basic
    auth_fields: [login, password]
    success_status: 200
    defaults:
      api_url: "https://example.com/api"
  # Option B: connector-side validation endpoint
  validate_endpoint: /auth/{account_name}/status
  # Option C: special mode for email (IMAP+SMTP)
  validate_mode: email_imap_smtp
```

---

## 2. Implementation Agent Workflow

The implementation agent is responsible for building new integrators. Before writing any code:

1. **Read documentation** -- Fetch and store the external system's API documentation (REST API docs, WSDL files, SDK references) into `docs/{category}/{system}/{version}/`
2. **Check existing integrators** -- Look at similar integrators in the same category for patterns
3. **Implement the base interface** -- Every integrator implements the category-specific interface (see section 4)
4. **Write tests** -- Unit tests and integration tests (with sandbox/mock APIs) MUST be written alongside implementation
5. **Create Dockerfile** -- Following standards in [docs/STANDARDS.md#2-docker-standards](STANDARDS.md#2-docker-standards)
6. **Create documentation** -- `README.md` with setup instructions, API mapping, configuration reference
7. **Create sandbox accounts** -- Register sandbox/test accounts with external system if required, document credentials storage location

---

## 3. Verification & Maintenance Agent

The verification agent (`platform/verification-agent/`) is a single FastAPI microservice that combines continuous health monitoring with deep functional verification of every connector. It runs on a configurable schedule (default: every 7 days) and can also be triggered on-demand via the dashboard or API.

### 3.1 Architecture

```
platform/verification-agent/
+-- Dockerfile
+-- requirements.txt
+-- pyproject.toml
+-- src/
    +-- main.py                  # FastAPI app + APScheduler
    +-- config.py                # Pydantic settings
    +-- db.py                    # SQLAlchemy models (verification_reports, verification_settings)
    +-- discovery.py             # Connector discovery (connector.yaml + DB instances)
    +-- credential_vault.py      # AES-256-GCM credential decryption
    +-- runner.py                # Orchestrates 3-tier verification run
    +-- reporter.py              # Persists results to PostgreSQL
    +-- api/
    |   +-- routes.py            # REST API: trigger runs, scheduler, reports, errors
    +-- checks/
        +-- common.py            # Shared utilities (result, get_check, req_check, PDF_STUB)
        +-- base.py              # Tier 1: health, readiness, docs
        +-- auth.py              # Tier 2: credentials, auth status, connection status
        +-- functional.py        # Tier 3 dispatcher -- routes to per-category module
        +-- courier/             # Tier 3: Courier connector tests
        |   +-- __init__.py
        |   +-- generic.py       #   Fallback for couriers without a dedicated file
        +-- ecommerce/           # Tier 3: E-commerce connector tests
        |   +-- __init__.py
        |   +-- generic.py       #   Fallback for e-commerce without a dedicated file
        +-- erp/                 # Tier 3: ERP connector tests
        |   +-- __init__.py
        +-- automation/          # Tier 3: Automation connector tests
        |   +-- __init__.py
        +-- other/               # Tier 3: Other connector tests
            +-- __init__.py
            +-- skanuj_fakture.py  # SkanujFakture (20+ endpoints, full CRUD cycle)
            +-- account_based.py   # Email, FTP/SFTP (generic account-based)
```

The directory layout mirrors `integrators/` categories. Each category folder contains:

- `**generic.py**` -- fallback tests for connectors without a dedicated file (tests common endpoints based on `connector.yaml` capabilities)
- `**{connector_name}.py**` -- connector-specific tests that exercise all documented endpoints

### 3.2 Three-tier verification

Every connector goes through all three tiers in sequence. If a tier fails critically, subsequent tiers may be skipped.

**Tier 1 -- Infrastructure (all connectors, no credentials needed)**


| Check     | Endpoint         | Pass condition                         |
| --------- | ---------------- | -------------------------------------- |
| Health    | `GET /health`    | HTTP 200, `status: "healthy"`          |
| Readiness | `GET /readiness` | HTTP 200, all dependency checks pass   |
| API docs  | `GET /docs`      | HTTP 200, Swagger/OpenAPI UI reachable |


**Tier 2 -- Authentication (requires credentials from Credential Vault)**


| Check                | Endpoint                           | Pass condition                    |
| -------------------- | ---------------------------------- | --------------------------------- |
| Account provisioning | `POST /accounts`                   | Account created or already exists |
| Auth status          | `GET /auth/{account}/status`       | `authenticated: true`             |
| Connection status    | `GET /connection/{account}/status` | `connected: true`                 |


**Tier 3 -- Functional smoke tests (per-connector, requires credentials)**

Each connector has its own test module in `checks/`. Tests exercise all documented endpoints, including:

- **Read-only endpoints** -- listing, searching, fetching details
- **Write+cleanup cycles** -- upload a test resource, exercise per-resource endpoints, delete it afterward
- **Error paths** -- expected 404s for missing data (e.g., KSeF for non-KSeF documents) are accepted as PASS
- **Performance** -- every check records `response_time_ms`

### 3.3 Scheduling & triggers


| Mode               | How                                                  | Description                                                                              |
| ------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Scheduled          | APScheduler `IntervalTrigger`                        | Runs every `VERIFICATION_INTERVAL_DAYS` (default: 7). Configurable via API or dashboard. |
| On-demand (all)    | `POST /api/verification/run`                         | Verifies all discovered connectors.                                                      |
| On-demand (single) | `POST /api/verification/run?connector_filter={name}` | Verifies a single connector.                                                             |
| Dashboard          | Verification page toggle + "Run now" button          | UI controls for scheduler enable/disable and manual triggers.                            |


### 3.4 Maintenance responsibilities

1. **Health monitoring** -- Scheduled runs verify all deployed connectors are alive and functional
2. **Regression detection** -- Functional tests catch external API changes that break integrations
3. **Performance tracking** -- Response time baselines stored per check, regressions visible in reports
4. **Alerting** -- Failed checks generate structured error reports visible in the dashboard with filtering and drill-down
5. **Dependency health** -- Tier 1 readiness checks verify database, Kafka, and external API connectivity

### 3.5 Report format

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


| Status | Meaning                                                                             |
| ------ | ----------------------------------------------------------------------------------- |
| `PASS` | Endpoint responded correctly within thresholds                                      |
| `FAIL` | Unexpected status code, timeout, or exception                                       |
| `SKIP` | Check not applicable (e.g., no credentials, expected 404, capability not supported) |


### 3.6 Adding tests for a new connector

When a new connector is implemented, a corresponding Tier 3 test file MUST be created. Follow these steps:

**Step 1 -- Create the test file in the correct category folder**

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
"""Tier 3 functional checks -- {ConnectorDisplayName} connector."""

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
"""Tier 3 checks -- {Category} connector category."""
```

Each category folder may also contain a `generic.py` -- a fallback module that tests common endpoints for connectors that don't have a dedicated file. Connector-specific files always take priority.

**Step 2 -- Test every endpoint from `connector.yaml`**

Cross-reference the connector's `connector.yaml` to ensure every documented capability, action, and endpoint is covered. For each endpoint:

- **Read-only endpoints** -- use `get_check()` to verify HTTP 200 and measure response time
- **Write endpoints** -- use `req_check()` with a full cycle: create -> verify -> cleanup. Always delete test data afterward.
- **Endpoints that may legitimately fail** -- pass `accept_statuses=(200, 404)` when a 404 is expected behavior (e.g., KSeF data for non-KSeF documents)

Available utilities from `checks/common.py`:


| Function                                                                                 | Purpose                                                    |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `result(name, status, ms, error?, suggestion?)`                                          | Build a check result dict                                  |
| `get_check(client, url, name, params?)`                                                  | Execute GET, return check result                           |
| `req_check(client, method, url, name, *, params?, json_body?, files?, accept_statuses?)` | Execute any HTTP method, return `(check_result, response)` |
| `PDF_STUB`                                                                               | Minimal valid PDF bytes for upload tests                   |


**Step 3 -- Auto-discovery (no registration needed)**

The dispatcher in `platform/verification-agent/src/checks/functional.py` uses `importlib` to auto-discover test modules by convention. No manual registration is required -- placing a file in the correct category folder is enough:

```python
# Resolution order (automatic):
# 1. src.checks.{category}.{connector_name}  -- connector-specific
# 2. src.checks.{category}.generic           -- category fallback
```

For example, adding `checks/courier/inpost.py` automatically makes it the test module for the InPost connector. If no connector-specific file exists, `checks/courier/generic.py` is used as fallback.

**Step 4 -- Test checklist**

Every connector test file SHOULD cover:

- `list_accounts` -- verify account listing works
- All read-only listing endpoints (companies, documents, orders, products, etc.)
- All detail/get endpoints with a valid resource ID
- At least one full write cycle (create -> read -> update -> delete) with cleanup
- Authentication-dependent endpoints with the provisioned account
- Error cases where applicable (expected 404s, invalid IDs)
- All endpoint variants (e.g., `/documents` vs `/documents/simple`, upload v1 vs v2)

**Naming conventions for checks:**

- Use descriptive snake_case names: `list_companies`, `upload_document`, `get_document_file`
- Prefix variants: `list_dictionaries_CATEGORY`, `upload_document_v2`
- Suffix cleanup steps: `delete_documents_cleanup`, `delete_v2_cleanup`

**Step 5 -- Rebuild and verify**

```bash
docker compose -f docker-compose.prod.yml build verification-agent
docker compose -f docker-compose.prod.yml up -d verification-agent
curl -X POST "http://localhost:18080/api/verification/run?connector_filter={name}"
```

---

## 4. Integration Interfaces

### 4.1 Courier integration interface

Every courier integrator MUST implement:

List will be created

### 4.2 E-commerce integration interface

List will be created

### 4.3 ERP integration interface

List will be created

### 4.4 Automation integration interface

List will be created

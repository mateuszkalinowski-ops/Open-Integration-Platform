# Pinquark WMS Connector v1.0.0

Connector for the **Pinquark WMS Integration REST API**, enabling data exchange between external ERP systems and the Pinquark WMS via REST.

## Overview

The Pinquark WMS integration-rest application communicates with ERP systems via Kafka, but also exposes a REST API for sending data via POST and retrieving data via GET. This connector wraps that REST API.

## API Coverage

All endpoints from the Pinquark Integration REST API documentation are implemented:

| Domain | Operations |
|---|---|
| **Auth** | Login (`/auth/sign-in`), token refresh (automatic) |
| **Articles** | GET, CREATE, CREATE LIST, DELETE, DELETE LIST, GET DELETE COMMANDS |
| **Article Batches** | GET, CREATE, CREATE LIST |
| **Documents** | GET, CREATE, CREATE LIST (wrapper with `continueOnFail`), DELETE, DELETE LIST, GET DELETE COMMANDS |
| **Positions** | GET, CREATE, CREATE LIST, DELETE, DELETE LIST, GET DELETE COMMANDS |
| **Contractors** | GET, CREATE, CREATE LIST, DELETE, DELETE LIST, GET DELETE COMMANDS |
| **Feedback** | GET |
| **JSON Errors** | GET |

## Authentication

The WMS API uses JWT Bearer tokens:

1. Login with `POST /auth/sign-in` using `username` + `password`
2. Access token valid for 24 hours, refresh token for 7 days
3. The connector handles token caching and automatic refresh

## Configuration

Environment variables (prefix `PINQUARK_WMS_`):

| Variable | Default | Description |
|---|---|---|
| `PINQUARK_WMS_API_URL` | `http://localhost:8090` | WMS integration-rest base URL |
| `PINQUARK_WMS_USERNAME` | (empty) | Auth username |
| `PINQUARK_WMS_PASSWORD` | (empty) | Auth password |
| `PINQUARK_WMS_HTTP_CONNECT_TIMEOUT` | `30` | HTTP connect timeout (seconds) |
| `PINQUARK_WMS_HTTP_READ_TIMEOUT` | `60` | HTTP read timeout (seconds) |

## Running Locally

```bash
cd integrators/wms/pinquark-wms/v1.0.0
cp .env.example .env
# Edit .env with your WMS credentials
docker compose up -d
```

The connector runs on port **8000**. Swagger UI: `http://localhost:8000/docs`

## Key Design Decisions

- **Connector as proxy**: The connector forwards requests to the actual WMS integration-rest app, handling auth transparently.
- **Credentials per request**: Each request includes credentials, allowing multi-tenant usage.
- **GET → POST mapping**: Since the connector needs credentials in every call, WMS GET endpoints are exposed as POST on the connector side (credentials in body).
- **camelCase fields**: All schemas use camelCase to match the WMS API exactly.

## Endpoints Summary

See [API_MAPPING.md](API_MAPPING.md) for the full endpoint and field mapping.

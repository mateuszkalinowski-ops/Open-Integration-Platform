# InPost International API 2024 — Authentication

> Source: https://developers.inpost-group.com/authentication

## Overview

The InPost International API uses OAuth 2.1 access tokens. The connector uses the **Client Credentials Flow** (machine-to-machine).

## Environments

| Environment | Token Endpoint |
|---|---|
| **Production** | `https://api.inpost-group.com/auth/token` |
| **Sandbox** | `https://sandbox-api.inpost-group.com/auth/token` |

Note: The 2024 version uses `/auth/token`, while the 2025 version uses `/oauth2/token`.

## Client Credentials Flow (RFC 6749)

Used for M2M applications — the connector authenticates using `client_id` (organization_id) and `client_secret`.

### Token Request

```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

client_id={organization_id}
&client_secret={client_secret}
&grant_type=client_credentials
&scope=openid api:points:read api:shipments:write api:tracking:read api:one-time-pickups:write api:one-time-pickups:read
```

### Token Response

```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5c...",
    "token_type": "Bearer",
    "expires_in": 599
}
```

- `access_token`: JWT Bearer token
- `token_type`: Always `Bearer`
- `expires_in`: Token validity in seconds (typically ~10 minutes)

## Using the Token

Include the token in the `Authorization` header for all API calls:

```
Authorization: Bearer {access_token}
```

## Token Refresh

Tokens are short-lived (~10 minutes). When expired, request a new token via the same Client Credentials flow. The connector handles this automatically with a retry-on-401 decorator.

## Credential Requirements

| Parameter | Description | Source |
|---|---|---|
| `organization_id` | Client ID provided by InPost | InPost Integration Team |
| `client_secret` | Secret key paired with organization_id | InPost Integration Team |

To obtain credentials, contact the InPost Integration Team or register at https://merchant.inpost-group.com (self-service in progress).

## Required Scopes

| Scope | Purpose |
|---|---|
| `openid` | OpenID Connect base scope |
| `api:points:read` | Access locker and PUDO point data |
| `api:shipments:write` | Create and manage shipments |
| `api:tracking:read` | Read tracking events |
| `api:one-time-pickups:write` | Create pickup orders |
| `api:one-time-pickups:read` | Read pickup order data |

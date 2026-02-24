# InPost International API 2025 (Global API) — Authentication

> Source: https://developers.inpost-group.com/authentication

## Overview

The Global API uses OAuth 2.1 for authentication. It supports two flows:
1. **Client Credentials Flow** (M2M) — used by this connector
2. **Authorization Code Flow with PKCE** — for broker applications

## Environments

| Environment | Token Endpoint | Auth Portal |
|---|---|---|
| **Production** | `https://api.inpost-group.com/oauth2/token` | `https://account.inpost-group.com` |
| **Stage** | `https://stage-api.inpost-group.com/oauth2/token` | `https://stage-account.inpost-group.com` |

Note: The 2025 API uses `/oauth2/token` (changed from `/auth/token` in the 2024 version).

## Client Credentials Flow (RFC 6749)

### Method 1: Credentials in request body

```
POST /oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&scope=openid api:points:read api:shipments:write api:tracking:read api:one-time-pickups:write api:one-time-pickups:read
&client_id={organization_id}
&client_secret={client_secret}
```

### Method 2: Credentials via Basic Auth header

```
POST /oauth2/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic BASE64({client_id}:{client_secret})

grant_type=client_credentials
&scope=openid api:points:read api:shipments:write
```

Choose **exactly one** method per request. Do not mix both.

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

Include in `Authorization` header for all API calls:

```
Authorization: Bearer {access_token}
```

## Token Refresh

The connector automatically refreshes tokens on 401 response using the retry-on-unauthorized decorator. Simply call `/oauth2/token` again with the same credentials.

## Authorization Code Flow with PKCE (RFC 7636)

For broker applications that act on behalf of InPost users. Not used by this connector but documented for completeness.

### Step 1: Generate PKCE Verifier & Challenge

```python
import base64, hashlib, os

code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).rstrip(b'=').decode('utf-8')
```

### Step 2: Redirect user to authorization page

```
GET /oauth2/authorize?response_type=code
    &redirect_uri=https://your-app.com/callback
    &client_id={client_id}
    &scope=openid api:points:read api:shipments:write
    &code_challenge={code_challenge}
    &code_challenge_method=S256
```

Host: `https://stage-account.inpost-group.com` (stage) or `https://account.inpost-group.com` (production)

### Step 3: User logs in and provides consent

### Step 4: Exchange authorization code for tokens

```
POST /oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&redirect_uri=https://your-app.com/callback
&code={authorization_code}
&code_verifier={code_verifier}
&client_id={client_id}
&client_secret={client_secret}
```

Response includes both `access_token` and `refresh_token`.

### Step 5: Refresh expired access token

```
POST /oauth2/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic BASE64({client_id}:{client_secret})

grant_type=refresh_token
&refresh_token={refresh_token}
```

## Available Scopes

| Scope | Purpose |
|---|---|
| `openid` | OpenID Connect base scope |
| `api:points:read` | Access locker/PUDO point data |
| `api:shipments:write` | Create and manage shipments |
| `api:shipments:read` | Read shipment data |
| `api:tracking:read` | Read tracking events |
| `api:one-time-pickups:write` | Create pickup orders |
| `api:one-time-pickups:read` | Read pickup orders |
| `api:returns:write` | Create return shipments |
| `api:returns:read` | Read return shipment data |
| `api:labels:read` | Retrieve shipping labels |

## Credential Requirements

| Parameter | Description | Source |
|---|---|---|
| `organization_id` | Client ID / Organization ID | InPost Integration Team |
| `client_secret` | Secret key for authentication | InPost Integration Team |

Self-service portal at https://merchant.inpost-group.com is in development.

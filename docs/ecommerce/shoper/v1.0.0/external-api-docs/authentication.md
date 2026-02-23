# Shoper REST API — Authentication

Source: https://developers.shoper.pl/developers/api/getting-started
Reference: https://cwsi.pl/ecommerce/shoper/podstawy-restapi-obsluga-api-platformy-shoper/
Fetched: 2026-02-22

## Overview

Shoper uses a simplified OAuth2 flow based on Basic Auth → Bearer token exchange.
There is **no OAuth2 device code flow** or authorization code grant — access is
granted directly via admin credentials.

## Prerequisites

1. **Create an administrator group** with WebAPI access:
   - Panel admin → Konfiguracja → Administracja, system
   - Create a new admin group (e.g. "api-access")
   - Set access type to **"Dostęp do WebApi"**
   - Configure permissions (read, write) per resource as needed

2. **Create an administrator account** in that group:
   - The login and password are used for API authentication

## Authentication Flow

### Step 1: Obtain Access Token

```
POST /webapi/rest/auth
Authorization: Basic {base64(login:password)}
```

The `Authorization` header contains `Basic` + base64-encoded `login:password`.

**Response (200 OK):**
```json
{
  "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "expires_in": 2592000,
  "token_type": "bearer"
}
```

| Field          | Type    | Description                                    |
|----------------|---------|------------------------------------------------|
| `access_token` | string  | Bearer token for subsequent requests           |
| `expires_in`   | integer | Token lifetime in seconds (default: 2592000 = 30 days) |
| `token_type`   | string  | Always `"bearer"`                              |

### Step 2: Use Bearer Token

All subsequent API requests must include the token in the `Authorization` header:

```
GET /webapi/rest/orders
Authorization: Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Token Refresh

When the token expires, simply repeat Step 1 to obtain a new token.
There is no dedicated refresh token endpoint — re-authentication is done
with the original credentials.

## Token Lifecycle

```
┌──────────────────┐
│ POST /auth       │
│ Basic Auth       │──────► access_token (valid ~30 days)
│ (login:password) │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ GET /orders      │
│ Bearer {token}   │──────► 200 OK / data
└──────────────────┘
        │
        ▼ (after expiry or 401)
┌──────────────────┐
│ POST /auth       │
│ Basic Auth       │──────► new access_token
└──────────────────┘
```

## Error Responses

| Scenario                  | HTTP Code | Description                          |
|---------------------------|-----------|--------------------------------------|
| Invalid credentials       | 401       | Wrong login or password              |
| Expired token             | 401       | Token has expired, re-authenticate   |
| No WebAPI permission      | 403       | Admin group lacks WebAPI access      |
| Insufficient permissions  | 403       | Resource-level permission missing    |

## Security Notes

- Credentials are sent via Basic Auth only to the `/auth` endpoint
- All communication MUST use HTTPS
- Token lifetime is 30 days by default — the connector refreshes proactively
  60 seconds before expiry to avoid request failures
- Credentials should be stored encrypted (AES-256-GCM in Pinquark Credential Vault)
- Never log credentials or tokens in production

## Example (Python)

```python
import httpx
import base64

shop_url = "https://mystore.shoparena.pl"
login = "api-user"
password = "secret"

credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

# Step 1: Get token
response = httpx.post(
    f"{shop_url}/webapi/rest/auth",
    headers={"Authorization": f"Basic {credentials}"},
)
token = response.json()["access_token"]

# Step 2: Use token
orders = httpx.get(
    f"{shop_url}/webapi/rest/orders",
    headers={"Authorization": f"Bearer {token}"},
)
print(orders.json())
```

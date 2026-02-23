# IdoSell API — Authentication

## Admin API (Primary — used by this integrator)

The IdoSell Admin Panel API uses **API key authentication** via a custom HTTP header.

### Header
```
X-API-KEY: <your_api_key>
```

### How to obtain an API key

1. Log in to the IdoSell administration panel
2. Navigate to **Administration → API → Access Keys for Admin API**
3. Generate a new API key
4. Copy and store securely

### Key properties

- Static key (no expiration, no refresh needed)
- Key is valid until manually revoked
- One key per application (multiple keys can be created)
- Scoped to the panel (all shops within the panel are accessible)

### Required headers for every request

```
X-API-KEY: <api_key>
Accept: application/json
Content-Type: application/json
```

---

## Legacy Authentication (SHA-1 key)

Older IdoSell API versions (pre-v6) and the CustomerAPI (ICDF/dropshipping) use a different mechanism:

1. Generate `systemKey = SHA1(YYYYMMDD + SHA1(password))` daily
2. Include in the request body:

```json
{
  "authenticate": {
    "userLogin": "mylogin",
    "systemLogin": "mylogin",
    "authenticateKey": "<daily_sha1_key>",
    "systemKey": "<daily_sha1_key>"
  }
}
```

This integrator does NOT use legacy authentication — it uses the modern `X-API-KEY` header.

---

## Error Response on Auth Failure

```json
{
  "_error": {
    "status_code": 401,
    "reason": "Unauthorized"
  }
}
```

Or in the body errors object:
```json
{
  "errors": {
    "faultCode": 1,
    "faultString": "Login error"
  }
}
```

`faultCode: 1` = authentication/login error.

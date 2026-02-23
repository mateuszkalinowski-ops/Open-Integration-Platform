# Raben Group — Sandbox Setup

## Overview

Raben Group provides a sandbox environment for testing integrations before going to production.

## Getting a Sandbox Account

1. Visit [myRaben](https://myraben.com/) and create an account
2. Contact Raben IT integration team to request sandbox/test access:
   - Email: integration support via your Raben account manager
   - Specify that you need API access for the sandbox environment
3. Raben will provide sandbox credentials (username + password) and a customer number

## Sandbox Environment

| Parameter | Value |
|---|---|
| Sandbox API URL | `https://sandbox.myraben.com/api/v1` |
| Production API URL | `https://myraben.com/api/v1` |

## Configuration

Set in `.env` or environment variables:

```bash
APP_ENV=development
RABEN_SANDBOX_API_URL=https://sandbox.myraben.com/api/v1
```

When using the API, set `sandbox_mode: true` in credentials:

```json
{
  "credentials": {
    "username": "sandbox_user",
    "password": "sandbox_pass",
    "customer_number": "TEST-001",
    "sandbox_mode": true
  }
}
```

## Sandbox Limitations

- Orders created in sandbox are not processed by Raben operations
- Tracking data is simulated
- Labels generated are marked as TEST/SANDBOX
- PCD photos are not available in sandbox
- ETA calculations use mock data

## Testing Workflow

1. Configure sandbox credentials
2. Create a test transport order (`POST /shipments`)
3. Verify the order was created and has a waybill number
4. Test tracking (`GET /tracking/{waybill}`)
5. Test label retrieval (`POST /labels`)
6. Test claim submission (`POST /claims`)
7. Verify all responses match expected schemas

## Mock Server (Alternative)

If sandbox access is not available, use `pytest-httpx` or `respx` to mock Raben API responses. See `tests/` directory for examples of mocked API calls.

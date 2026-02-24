# FX Couriers — Sandbox Setup

## Overview

FX Couriers (KurierSystem) does not provide a separate sandbox environment. All API calls go to the production endpoint:

```
https://fxcouriers.kuriersystem.pl/api/rest
```

## Obtaining Test Credentials

1. Contact FX Couriers sales representative to obtain a test API token
2. The token is a Bearer token used in the `Authorization` header
3. A `company_id` will be assigned to your test account

## Testing Recommendations

- Use the test API token only for creating test orders
- Delete test orders promptly to avoid unnecessary processing
- For CI/CD integration tests, use `respx` or `pytest-httpx` to mock API responses
- The test suite in `tests/` demonstrates mocking patterns

## API Rate Limits

- No documented rate limits, but recommended to respect reasonable call frequency
- Recommended: cache `/services` response daily (via CRON)

## Known Limitations

- No sandbox/staging environment available
- Label PDF generation requires an existing accepted order
- Orders can only be deleted before a pickup is scheduled
- Maximum 100 orders returned per `/orders` call (use `offset` for pagination)

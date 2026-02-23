# IdoSell API — Rate Limits

## Monthly Quotas

IdoSell uses **monthly aggregate quotas** rather than per-second throttling:

| Plan | Monthly API Calls | Can Purchase More |
|---|---|---|
| Smart CLOUD | 100,000 | No |
| Elastic CLOUD | 100,000 (free tier) | Yes |
| Cloud PRO | 1,000,000 (free tier) | Yes |

### Excluded from limits

Calls from IdoSell's own applications (POS, Bridge, Scanner, Printer, wFirma integration) do not count against the monthly quota.

## Per-Request Throttling

The IdoSell documentation does **not** specify per-second or per-minute rate limits. There is no documented HTTP 429 behavior or `Retry-After` header support.

However, this integrator implements defensive rate-limit handling:
- Checks for HTTP 429 responses and respects `Retry-After` if present
- Implements exponential backoff for 5xx errors
- Uses configurable scraping intervals to avoid excessive API calls

## Recommendations

- Keep scraping intervals at 120 seconds or more
- Batch product/stock updates (max 100 per request)
- Monitor monthly usage via the IdoSell admin panel
- Use search endpoints with date filters to minimize result sets

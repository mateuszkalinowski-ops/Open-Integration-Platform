# Shopify API Rate Limits

Source: https://shopify.dev/docs/api/usage/rate-limits

## REST Admin API — Leaky Bucket Algorithm

Shopify REST Admin API uses a **leaky bucket** rate limit model:

- **Bucket size**: 80 requests
- **Leak rate**: 40 requests/second (2 requests removed from bucket per 50ms)
- When the bucket is full → HTTP **429 Too Many Requests**
- Response includes `Retry-After` header (seconds to wait)

### Rate Limit Headers

Every response includes:

```
X-Shopify-Shop-Api-Call-Limit: 32/40
```

Format: `{current_usage}/{bucket_size_per_second}`

### Best Practices

1. Monitor `X-Shopify-Shop-Api-Call-Limit` header
2. Stop requests when usage > 80%
3. Use exponential backoff on 429 responses
4. Cache responses where possible
5. Use `fields` parameter to limit response size
6. Use `since_id` for incremental pagination instead of `page`
7. For bulk operations, consider GraphQL Bulk Operations API

### Plan-Based Limits

| Plan | REST API Bucket | GraphQL Points/sec |
|---|---|---|
| Standard | 40 req/s (bucket 80) | 100 points/s |
| Advanced | 40 req/s (bucket 80) | 200 points/s |
| Plus | 80 req/s (bucket 160) | 1000 points/s |
| Enterprise | 80 req/s (bucket 160) | 2000 points/s |

### Resource-Based Limits

Stores with >50,000 product variants: max 1,000 new variants per day.
(Does not apply to Shopify Plus.)

### Pagination Limits

- Maximum array size in input: 250 items
- Maximum pagination depth: 25,000 objects
- For larger datasets: use filters or GraphQL Bulk Operations

## Connector Implementation

The Shopify connector handles rate limits by:
1. Monitoring `X-Shopify-Shop-Api-Call-Limit` header on every response
2. Warning when usage exceeds 80%
3. Automatic retry with `Retry-After` value on 429 responses
4. Exponential backoff on 5xx server errors
5. Maximum 3 retry attempts per request

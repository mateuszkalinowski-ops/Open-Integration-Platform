# Shoper REST API — Rate Limits & Pagination

Source: https://developers.shoper.pl/
Fetched: 2026-02-22

## Rate Limiting

Shoper enforces rate limiting on the REST API to protect platform stability.

### Known Behavior

| Aspect              | Value                                          |
|---------------------|------------------------------------------------|
| Rate limit response | HTTP 429 Too Many Requests                     |
| Retry header        | `Retry-After` (seconds to wait)                |
| Typical limit       | Not officially documented; empirically ~100-200 requests/minute |
| Bulk endpoint       | Recommended for batch operations to reduce request count |

### Handling Rate Limits

When receiving HTTP 429:
1. Read the `Retry-After` header value (seconds)
2. Wait for the specified duration
3. Retry the request

The connector implements this automatically with exponential backoff:

```python
if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", "5"))
    await asyncio.sleep(retry_after)
    # retry...
```

### Best Practices

- **Use the Bulk API** (`POST /webapi/rest/bulk`) to batch multiple requests
  into a single HTTP call — this dramatically reduces the number of requests
- **Implement client-side throttling** — add small delays between consecutive
  requests (e.g. 100-200ms)
- **Cache static data** — categories, shipping methods, payment methods, and
  currencies rarely change; cache them for hours instead of re-fetching
- **Use filters** — always filter by date when polling for changes instead of
  fetching all records every time
- **Paginate efficiently** — use `page` parameter, don't fetch all pages if
  only recent changes are needed

---

## Pagination

All list endpoints return paginated responses using the `ShoperPage` format.

### Response Format

```json
{
  "count": 254,
  "pages": 6,
  "page": 1,
  "list": [ ... ]
}
```

### Request Parameters

| Parameter | Type    | Default | Description                |
|-----------|---------|---------|----------------------------|
| `page`    | integer | 1       | Page number (1-based)      |
| `limit`   | integer | ~50     | Items per page             |

### Iterating All Pages

```python
page = 1
all_items = []

while True:
    response = client.get(f"/webapi/rest/orders?page={page}")
    data = response.json()
    all_items.extend(data["list"])
    
    if page >= data["pages"]:
        break
    page += 1
```

### Filtering

Filters are JSON-encoded and passed as the `filters` query parameter:

```
GET /webapi/rest/orders?filters={"date":{">":"2026-01-01 00:00:00"}}
```

Multiple filters can be combined:
```json
{
  "status_id": {"=": "2"},
  "date": {">=": "2026-01-01 00:00:00"}
}
```

Supported operators:
- `=` — equal
- `!=` — not equal
- `>`, `>=`, `<`, `<=` — comparison
- `IN` — value in array: `{"order_id": {"IN": ["1", "2", "3"]}}`
- `LIKE` — partial text match

### Sorting

Use the `order` query parameter:

```
GET /webapi/rest/orders?order=date+desc
GET /webapi/rest/products?order=edit_date+asc
```

Format: `field_name+direction` where direction is `asc` or `desc`.

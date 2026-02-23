# Known Issues & Limitations — IdoSell Integrator v1.0.0

## Limitations

### 1. Single-size product mapping
The current mapper extracts EAN from `productSizesAttributes[0]` — only the first size variant. Multi-size products will only report the first variant's EAN code.

### 2. No webhook support
This integrator uses polling (scraping). IdoSell supports webhooks but the payload format is not publicly documented. Future versions may add webhook receiver endpoints.

### 3. Stock sync uses absolute quantities
The `PUT /products/stockQuantity` endpoint sets absolute stock levels. IdoSell also supports `add` and `substract` modes — these are not yet exposed.

### 4. Product sync is limited
`sync_products` currently only supports editing existing products (via `settingModificationType: "edit"`). Creating new products requires additional fields (descriptions, categories, prices) that are not yet mapped.

### 5. No returns/refund support
The `fetch_returns` method is not implemented. IdoSell has a returns API (`/orders/returns/*`) that could be integrated in a future version.

### 6. Monthly API quota
IdoSell enforces monthly API call limits (100k–1M depending on plan). The integrator does not track quota usage — monitor it in the IdoSell admin panel.

## IdoSell API Quirks

### Inconsistent naming
Some endpoints use `camelCase` (`resultsPage`) while others use `snake_case` (`results_page`). The integrator handles the more common `camelCase` variant.

### DELETE operations use POST
IdoSell uses `POST` to delete sub-paths (e.g., `POST /products/products/delete`) instead of HTTP DELETE.

### 0-based pagination
IdoSell uses 0-based `resultsPage` (page 0 = first page). The integrator converts from 1-based pagination in the REST API.

### Date format
IdoSell uses `YYYY-MM-DD HH:MM:SS` (space-separated), not ISO 8601 with `T`. The mapper handles this format explicitly.

### Error responses
Error codes are returned in the response body (`errors.faultCode`), not as HTTP status codes. Common codes:
- `0` = success
- `1` = login/auth error
- `2` = empty results (not an error)
- `5` = shop blocked
- `6` = duplicate entry

### Boolean serialization
IdoSell serializes booleans as `"y"/"n"` strings in some endpoints, not `true/false`. The Java implementation uses custom `IdoBooleanSerializer`/`IdoBooleanDeserializer` for this.

### Legacy auth (v7) — GET converted to POST
When using `auth_mode: legacy`, all GET requests are internally converted to POST because the `authenticate` block must be sent in the request body. This is consistent with how the Java implementation works (all calls go through POST `IdoSender`).

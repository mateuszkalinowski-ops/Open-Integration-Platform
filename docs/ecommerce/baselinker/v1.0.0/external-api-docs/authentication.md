# BaseLinker API — Authentication & Configuration

> Source: https://api.baselinker.com/
> Fetched: 2026-02-24

## Authentication

BaseLinker uses token-based authentication via HTTP header.

### Token Generation

1. Log in to BaseLinker panel
2. Navigate to: **Account & other → My account → API**
3. Generate an API token

### Authorization Method

Send the token in the `X-BLToken` HTTP header:

```
X-BLToken: <your-api-token>
```

> **Note:** Passing the token as a POST parameter (`token`) is **deprecated** since
> 2021-11-05. Use the `X-BLToken` header.

### Request Format

All API calls use a single endpoint via POST:

```
POST https://api.baselinker.com/connector.php
Content-Type: application/x-www-form-urlencoded
X-BLToken: <your-api-token>

method=<method_name>&parameters=<json_encoded_params>
```

## Rate Limiting

- **100 requests per minute** per account
- When exceeded, the API returns HTTP 429
- Recommended: implement client-side throttling with exponential backoff

## Encoding

- All data uses **UTF-8** encoding
- Base64 content: replace `+` with `%2B` before sending to avoid decoding issues

## URLs

| Environment | URL |
|-------------|-----|
| Production  | `https://api.baselinker.com/connector.php` |

BaseLinker does not provide a separate sandbox/testing environment. Testing must be
done with a live account (recommend creating a separate test account).

## Error Handling

All methods return a `status` field:

- `"SUCCESS"` — request executed correctly
- `"ERROR"` — error occurred; check `error_message` and `error_code` fields

```json
{
  "status": "ERROR",
  "error_message": "The provided API key is invalid or expired",
  "error_code": "ERROR_INVALID_TOKEN"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `ERROR_INVALID_TOKEN` | Invalid or expired API token |
| `ERROR_UNKNOWN_METHOD` | Method name not recognized |
| `ERROR_TOO_MANY_REQUESTS` | Rate limit exceeded (100 req/min) |

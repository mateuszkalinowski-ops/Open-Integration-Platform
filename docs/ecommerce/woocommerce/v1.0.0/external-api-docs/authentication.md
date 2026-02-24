# WooCommerce REST API — Authentication

> Source: https://woocommerce.github.io/woocommerce-rest-api-docs/v3.html
> Fetched: 2026-02-24

## API Key Generation

1. Go to **WooCommerce > Settings > Advanced > REST API**
2. Click **Add key**
3. Set description, select user with appropriate permissions, grant Read/Write
4. Click **Generate API key**
5. Copy `consumer_key` and `consumer_secret` (secret shown only once)

## Authentication Methods

### Over HTTPS (Recommended) — Basic Auth

Use HTTP Basic Authentication with `consumer_key` as username and `consumer_secret`
as password.

```bash
curl https://example.com/wp-json/wc/v3/orders \
  -u consumer_key:consumer_secret
```

**Fallback for servers not parsing Authorization header:**

```
https://example.com/wp-json/wc/v3/orders?consumer_key=XXX&consumer_secret=XXX
```

### Over HTTP — OAuth 1.0a

Required when SSL is not available. Uses HMAC-SHA256 one-legged OAuth.

**Required OAuth parameters:**

| Parameter | Description |
|-----------|-------------|
| `oauth_consumer_key` | Consumer key |
| `oauth_nonce` | Unique 32-char random string |
| `oauth_timestamp` | Unix timestamp (15-minute window) |
| `oauth_signature_method` | `HMAC-SHA256` |
| `oauth_signature` | Generated signature |

**Signature generation steps:**

1. Set HTTP method (e.g. `GET`)
2. URL-encode the base request URI (without query string)
3. Collect all `oauth_*` params (except signature), normalize and URL-encode per RFC 3986
4. Sort parameters by byte-order
5. Join param key=value pairs with `&`
6. Form signature base string: `{METHOD}&{encoded_url}&{encoded_params}`
7. Sign with HMAC-SHA256 using `{consumer_secret}&` as key
8. Base64-encode the signature

**OAuth tips:**

- Authorization header supported since WooCommerce 3.0
- The request body is NOT signed per OAuth spec
- Use the store URL from the index endpoint for the base string
- `oauth_version` parameter should be omitted

## Connection Troubleshooting

### 401 Unauthorized

- Verify consumer key and secret are correct
- Ensure the API user has appropriate permissions
- Try regenerating API keys

### Consumer key is missing

Server may not parse Authorization header correctly. Use query string auth instead:

```
?consumer_key=XXX&consumer_secret=XXX
```

### FastCGI issues

Ensure authorization headers are properly forwarded in FastCGI configurations.

### SSL certificate issues (development)

For localhost/self-signed certificates, disable SSL verification in your HTTP client.

### Server doesn't support PUT/DELETE

Use the `_method` parameter or `X-HTTP-Method-Override` header:

```
POST /wp-json/wc/v3/orders/123?_method=PUT
```

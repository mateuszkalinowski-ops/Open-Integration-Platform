# WooCommerce REST API — Webhooks

> Source: https://woocommerce.github.io/woocommerce-rest-api-docs/v3.html
> Fetched: 2026-02-24

## Overview

Webhooks allow event-driven notifications to be sent to a URL when resources change.
Can be managed via the WooCommerce admin or REST API.

Each webhook has:

| Property | Description |
|----------|-------------|
| `hooks` | Array of WordPress hook names bound to the webhook |
| `secret` | Optional secret for HMAC-SHA256 signature verification |
| `delivery_url` | Payload delivery URL (HTTP or HTTPS) |
| `topic` | Resource + event combination (e.g. `order.created`) |
| `status` | `active`, `paused`, or `disabled` |

## Core Topics

| Topic | Description |
|-------|-------------|
| `product.created` | Product created |
| `product.updated` | Product updated |
| `product.deleted` | Product deleted |
| `order.created` | Order created |
| `order.updated` | Order updated |
| `order.deleted` | Order deleted |
| `customer.created` | Customer created |
| `customer.updated` | Customer updated |
| `customer.deleted` | Customer deleted |
| `coupon.created` | Coupon created |
| `coupon.updated` | Coupon updated |
| `coupon.deleted` | Coupon deleted |

**Custom topics:** Use `action.{hook_name}` to trigger on any WordPress action hook.
Example: `action.woocommerce_add_to_cart`

## Delivery

- Method: HTTP POST via `wp_remote_post()`
- Processing: background via wp-cron (default)
- Payload: JSON, same structure as REST API responses

### Delivery Headers

| Header | Description |
|--------|-------------|
| `X-WC-Delivery-ID` | Delivery log ID |
| `X-WC-Webhook-ID` | Webhook post ID |
| `X-WC-Webhook-Signature` | Base64-encoded HMAC-SHA256 of payload body |
| `X-WC-Webhook-Event` | Event name (e.g. `updated`) |
| `X-WC-Webhook-Resource` | Resource name (e.g. `order`) |
| `X-WC-Webhook-Topic` | Full topic (e.g. `order.updated`) |

## Signature Verification

The `X-WC-Webhook-Signature` header contains a base64-encoded HMAC-SHA256 hash
generated using the webhook's secret and the request body:

```python
import hashlib
import hmac
import base64

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = base64.b64encode(
        hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)
```

## Retry / Failure Behavior

- After **5 consecutive failed deliveries** (non-2xx response), the webhook is
  automatically **disabled**
- Must be re-enabled via REST API or admin panel
- Only the 25 most recent delivery logs are retained

## Logging

Each delivery is logged with:
- Request: URL, method, headers, body
- Response: code, message, headers, body
- Duration

## Admin UI

Settings location: **WooCommerce > Settings > Advanced > Webhooks**

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/webhooks` | List all webhooks |
| `GET` | `/webhooks/{id}` | Get single webhook |
| `POST` | `/webhooks` | Create webhook |
| `PUT` | `/webhooks/{id}` | Update webhook |
| `DELETE` | `/webhooks/{id}` | Delete webhook |
| `GET` | `/webhooks/count` | Get webhook count |
| `GET` | `/webhooks/{id}/deliveries` | Get delivery logs |
| `GET` | `/webhooks/{id}/deliveries/{delivery_id}` | Get single delivery log |

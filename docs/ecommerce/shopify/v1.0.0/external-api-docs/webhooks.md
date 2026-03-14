# Shopify Webhooks Reference

Source: https://shopify.dev/docs/api/admin-rest/2024-07/resources/webhook

> **Note**: This connector v1.0.0 uses polling instead of webhooks.
> Webhook support is planned for v1.1.0.

## Overview

Shopify webhooks send HTTP POST notifications when events occur in a store.
They provide near-real-time event delivery, reducing the need for polling.

## Relevant Webhook Topics

### Orders

| Topic | Description |
|---|---|
| `orders/create` | New order placed |
| `orders/updated` | Order updated (any change) |
| `orders/cancelled` | Order cancelled |
| `orders/fulfilled` | All items fulfilled |
| `orders/partially_fulfilled` | Some items fulfilled |
| `orders/paid` | Payment captured |

### Products

| Topic | Description |
|---|---|
| `products/create` | Product created |
| `products/update` | Product updated |
| `products/delete` | Product deleted |

### Inventory

| Topic | Description |
|---|---|
| `inventory_levels/update` | Inventory level changed |
| `inventory_levels/connect` | Inventory item connected to location |
| `inventory_levels/disconnect` | Inventory item disconnected |

### Customers

| Topic | Description |
|---|---|
| `customers/create` | Customer created |
| `customers/update` | Customer updated |

## Webhook Registration

```
POST /admin/api/2024-07/webhooks.json
```

```json
{
  "webhook": {
    "topic": "orders/create",
    "address": "https://your-platform.example.com/shopify/webhooks",
    "format": "json"
  }
}
```

## Webhook Verification

Shopify signs webhooks with HMAC-SHA256 using the app's Client Secret.
Verify via `X-Shopify-Hmac-SHA256` header.

```python
import hmac
import hashlib
import base64

def verify_webhook(data: bytes, hmac_header: str, secret: str) -> bool:
    digest = hmac.new(secret.encode(), data, hashlib.sha256).digest()
    computed = base64.b64encode(digest).decode()
    return hmac.compare_digest(computed, hmac_header)
```

## Planned v1.1.0 Integration

- Register webhooks for `orders/create`, `orders/updated`, `orders/cancelled`
- Verify HMAC signatures
- Process events in real-time instead of polling
- Keep polling as fallback for missed webhooks

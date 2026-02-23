# Shoper REST API — Webhooks & Event Notifications

Source: https://developers.shoper.pl/
Fetched: 2026-02-22

## Webhook Support

Shoper provides a **Webhooks API** that allows registering HTTP callbacks
for store events. When an event occurs, Shoper sends a POST request to
the registered URL.

### Available Events

| Event                     | Description                          |
|---------------------------|--------------------------------------|
| `order/create`            | New order created                    |
| `order/edit`              | Order modified                       |
| `order/paid`              | Order marked as paid                 |
| `order/status`            | Order status changed                 |
| `order/delete`            | Order deleted                        |
| `product/create`          | New product created                  |
| `product/edit`            | Product modified                     |
| `product/delete`          | Product deleted                      |
| `client/create`           | New customer registered              |
| `client/edit`             | Customer data modified               |
| `parcel/create`           | Parcel created                       |
| `parcel/dispatch`         | Parcel dispatched                    |

### Webhook Registration

```
POST /webapi/rest/webhooks
```

Body:
```json
{
  "url": "https://integrations.pinquark.com/webhooks/shoper/orders",
  "event": "order/create",
  "active": 1,
  "secret": "optional-hmac-secret"
}
```

### Webhook Payload

Shoper sends a POST request with JSON body containing:

```json
{
  "event": "order/create",
  "shop": "mystore.shoparena.pl",
  "data": {
    "order_id": 12345
  }
}
```

The payload contains only the entity ID — the consumer must fetch full
details via the REST API.

### Webhook Security

- Webhooks support an optional `secret` field for HMAC signature verification
- The signature is sent in the request headers
- Always validate the signature before processing webhook data
- Use HTTPS endpoints only

## Current Connector Approach

The Shoper connector currently uses **polling** (scraping) instead of webhooks
because:

1. Webhooks require a publicly accessible HTTPS endpoint
2. The polling approach is simpler for on-premise deployments
3. Webhooks only send entity IDs, requiring additional API calls anyway
4. Polling interval is configurable (default: 300 seconds)

Future versions may add webhook support as an alternative to polling
for cloud-hosted deployments where a public endpoint is available.

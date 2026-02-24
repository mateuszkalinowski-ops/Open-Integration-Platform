# InPost International API 2025 (Global API) — Webhooks

> Source: https://developers.inpost-group.com/webhooks  
> Signature verification: https://developers.inpost-group.com/webhook-signature-verification

## Overview

Webhooks provide real-time event-driven notifications for tracking events. Instead of polling the Tracking API, merchants provide a URL and subscribe to event types. When events occur, InPost sends HTTP POST requests to the merchant's URL.

## Setup

Contact InPost Account Manager or Integration Team to configure:
1. Your webhook URL
2. Event types to subscribe to
3. Authentication method
4. Signing method and configuration

Self-service portal is under development.

## Notification Retry Policy

When InPost sends a webhook notification, it expects a `200 OK` response. If not received, retries follow this schedule:

| Attempt | Delay |
|---|---|
| 1st retry | 15 seconds |
| 2nd retry | 30 seconds |
| 3rd retry | 1 minute |
| 4th retry | 5 minutes |
| 5th retry | 30 minutes |

After all attempts fail, the notification is considered failed — no further retries.

## Webhook Headers

| Header | Example | Description |
|---|---|---|
| `x-inpost-api-version` | `2024-06-01` | Payload version (date-based) |
| `x-inpost-topic` | `Shipment.Tracking` | Event topic |
| `x-inpost-event-id` | `XXX123` | Unique event ID |
| `x-inpost-timestamp` | `2024-04-26T14:00:03.165Z` | UTC timestamp when event was sent |
| `x-inpost-signature` | `XXXXXXX12345` | Request signature |

## Versioning

Webhook payloads are versioned via `X-InPost-Api-Version` header (date format, e.g., `2024-06-01`):
- Non-breaking changes (new fields) — no new version
- Breaking changes (renamed/removed fields) — new version is introduced
- Subscriptions are tied to a specific version

## Authentication Methods

### 1. Basic Authentication

Standard HTTP basic auth:

```
Authorization: Basic BASE64({username}:{password})
```

Merchant provides username and password during setup.

### 2. API Key / Custom Headers

Pre-shared security key sent as a custom HTTP header:

```
x-api-key: {shared_secret}
```

Header name is customizable; multiple headers can be configured.

### 3. Webhook Signature Verification

The most secure method — InPost signs each request payload. Two signing methods are supported:

#### Digital Signature (RSA + SHA256withRSA)

InPost signs the message hash using its private key. The signature is placed in `x-inpost-signature` header as Base64-encoded data.

**What is signed** (configurable per client):
- Option A: Event payload body only
- Option B: `{x-inpost-timestamp}.{body}` (dot-separated)

**Verification** (Python example):

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64

def verify_signature(body: bytes, signature_b64: str, public_key_pem: bytes) -> bool:
    public_key = serialization.load_pem_public_key(public_key_pem)
    signature = base64.b64decode(signature_b64)
    try:
        public_key.verify(
            signature,
            body,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
```

Public certificates:
- Sandbox: https://github.com/InPost/webhooks-java/blob/main/src/main/resources/sandbox-certificate.pem
- Production: https://github.com/InPost/webhooks-java/blob/main/src/main/resources/production-certificate.pem

#### HMAC Signature (HMAC-SHA256)

Uses a shared secret key to compute HMAC-SHA256 of the payload. The computed signature is Base64-encoded and placed in `x-inpost-signature`.

**Verification** (Python example):

```python
import hmac
import hashlib
import base64

def verify_hmac(body: bytes, signature_b64: str, shared_secret: str) -> bool:
    computed = base64.b64encode(
        hmac.new(
            shared_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    return hmac.compare_digest(computed, signature_b64)
```

## Webhook Payload

The payload structure is identical to tracking events (see [tracking-api.md](tracking-api.md)):

```json
{
    "customerReference": "Order-123",
    "trackingNumber": "120000018332540090213375",
    "eventId": "fb2ace20-2d8c-41da-94c4-3bd93f1451a1#CRE.1001",
    "eventCode": "CRE.1001",
    "timestamp": "2025-01-08T14:02:55.374675Z",
    "location": null,
    "delivery": {
        "recipientName": null,
        "deliveryNotes": null
    },
    "shipment": {
        "type": null
    },
    "returnToSender": null,
    "newDestination": null
}
```

## Available Event Topics

All tracking events can be subscribed to via webhooks. The topic header is always `Shipment.Tracking`. See [tracking-api.md](tracking-api.md) for the complete event catalog.

## Best Practices

1. **Respond quickly**: Return `200 OK` as soon as possible — process the event asynchronously
2. **Idempotency**: Use `x-inpost-event-id` to detect and handle duplicate deliveries
3. **Verify signatures**: Always validate `x-inpost-signature` to prevent spoofed requests
4. **Handle retries**: Design your endpoint to gracefully handle repeated deliveries of the same event
5. **Monitor failures**: Track failed webhook deliveries — after 5 failed retries, InPost stops sending

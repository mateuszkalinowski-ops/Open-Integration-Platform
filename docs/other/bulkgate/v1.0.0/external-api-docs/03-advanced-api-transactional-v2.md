# BulkGate Advanced API v2.0 — Transactional SMS

Source: https://help.bulkgate.com/docs/en/http-advanced-transactional-v2.html

## API URL

```
https://portal.bulkgate.com/api/2.0/advanced/transactional
```

```http
POST /api/2.0/advanced/transactional HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache
```

It is strictly prohibited to exploit transactional SMS for promotional/marketing uses. It must be used for notification purposes only - as an SMS notification.

### Parameters table

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| application_id | Application identificator | Yes | - |
| application_token | Application authentication token | Yes | - |
| number | Recipient number or array of recipient numbers | Yes or `admin` or `groups` | - |
| admin | Number of BulkGate administrator receiving notification | Yes or `number` | - |
| text | Text of SMS message (max. 612 characters, or 268 if Unicode). Supports `<variable>` placeholders from `variables` array. | Yes | - |
| variables | Associative array for template variables, e.g.: `{"first_name": "John", "last_name": "Doe"}` | No | `[]` |
| channel | Alternative channels in cascade. If highest priority channel fails, lower channels are tried. If none deliver, SMS is used as fallback. | No | SMS object |
| country | ISO 3166-1 alpha-2 country code | No | `null` |
| schedule | Scheduled time in unix timestamp or ISO 8601 | No | Now |
| duplicates_check | `on` to prevent sending duplicate messages within 5 minutes. `off` - no duplicates removed. | No | `off` |
| tag | Message label for subsequent retrieval | No | - |

### Value number

Array of phone numbers:

```json
["420777777777", "420888888888", "420999999999"]
```

## Channels table

| VALUE | DESCRIPTION |
| --- | --- |
| `sms` | SMS channel object |
| `viber` | Viber channel object |
| `rcs` | RCS channel object |
| `whatsapp` | WhatsApp channel object |

## SMS object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| text | Text override for SMS channel (max. 612 chars, 268 if Unicode). If both SMS `text` and general `text` are present, SMS `text` is used. | No (if general `text` used) | - |
| sender_id | Sender ID type | No | `gSystem` |
| sender_id_value | Sender value | No | `null` |
| unicode | `true`/`false` for Unicode SMS | No | `false` |

### Sender ID type sender_id

| VALUE | DESCRIPTION |
| --- | --- |
| `gSystem` | System number |
| `gShort` | Short Code |
| `gText` | Text sender |
| `gMobile` | Mobile Connect |
| `gPush` | Mobile Connect push |
| `gOwn` | Own Number (verification required) |
| `gProfile` | BulkGate Profile ID |

## Viber object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| text | Viber message text override | No (if general `text` used) | - |
| sender | Sender name | Yes | `""` |
| expiration | Timeout before fallback to next channel (seconds) | No | `120` |
| use_template | Template mode (Belarus, Ukraine, Russia) | No | `false` |

## Full request example

```http
POST /api/2.0/advanced/transactional HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache

{
    "application_id": "APPLICATION_ID",
    "application_token": "APPLICATION_TOKEN",
    "number": ["777777777", "777777778"],
    "text": "example text <first_name>",
    "variables": {"first_name": "John"},
    "country": "cz",
    "schedule": "2023-08-14T18:30:00-01:00",
    "channel": {
        "whatsapp": {
            "sender": "420777777777",
            "expiration": 300,
            "message": {
                "text": "text"
            }
        },
        "rcs": {
            "sender": "BulkGate",
            "expiration": 300,
            "message": {
                "text": "text"
            }
        },
        "viber": {
            "sender": "BulkGate",
            "expiration": 100
        },
        "sms": {
            "sender_id": "gText",
            "sender_id_value": "Mr. Sender",
            "unicode": true
        }
    }
}
```

## Response — Success

```json
{
    "data": {
        "total": {
            "status": {
                "sent": 0,
                "accepted": 0,
                "scheduled": 2,
                "error": 0,
                "blacklisted": 0,
                "invalid_number": 0,
                "invalid_sender": 0,
                "duplicity_message": 0
            }
        },
        "response": [
            {
                "status": "scheduled",
                "message_id": "transactional-64afe5f28ffc2-0",
                "part_id": ["transactional-64afe5f28ffc2-0"],
                "number": "420777777777",
                "channel": "viber"
            },
            {
                "status": "scheduled",
                "message_id": "transactional-64afe5f28ffc2-1",
                "part_id": ["transactional-64afe5f28ffc2-1"],
                "number": "420777777778",
                "channel": "viber"
            }
        ]
    }
}
```

## Response — Error

```json
{
    "type": "invalid_phone_number",
    "code": 400,
    "error": "Invalid phone number",
    "detail": null
}
```

```json
{
    "type": "unknown_identity",
    "code": 401,
    "error": "Unknown identity / unauthorized / empty application_id",
    "detail": null
}
```

# BulkGate Simple API v1.0 — Transactional SMS

Source: https://help.bulkgate.com/docs/en/http-simple-transactional.html

## API URL

```
https://portal.bulkgate.com/api/1.0/simple/transactional
```

### Supported methods

- POST - application/json
- POST - application/x-www-form-urlencoded
- GET

It is strictly prohibited to exploit transactional SMS for promotional/marketing uses. It must be used for notification purposes only - as an SMS notification.

### Parameters table

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| application_id | Application identificator | Yes | - |
| application_token | Application authentication token | Yes | - |
| number | Recipient number | Yes | - |
| text | Text of SMS message (max. 612 characters, or 268 characters if Unicode is used), UTF-8 encoding | Yes | - |
| unicode | `Yes`/`true`/`1` for Unicode SMS, `no`/`false`/`0` for 7bit SMS | No | `false` |
| sender_id | Sender ID, see sender ID type table | No | `gSystem` |
| sender_id_value | Sender value - `gOwn` (e.g. "420 777 777 777"), `gText` (e.g. "BulkGate"), `gProfile` (e.g. "423"), `gMobile` or `gPush` (KEY) | No | `null` |
| country | Country code in ISO 3166-1 alpha-2 format (e.g. `GB`). If `null`, your set timezone will be used. | No | `null` |
| schedule | Schedule the sending time and date in unix timestamp, or ISO 8601. | No | Now |
| duplicates_check | `on` to prevent sending duplicate messages to the same phone number within 5 minutes. `off` - no duplicates removed. | No | `off` |
| tag | Message label for subsequent retrieval of the user. | No | - |

### Sender ID type sender_id

| VALUE | DESCRIPTION |
| --- | --- |
| `gSystem` | System number |
| `gShort` | Short Code |
| `gText` | Text sender |
| `gMobile` | Mobile Connect |
| `gPush` | Mobile Connect push |
| `gOwn` | Own Number (number verification required) |
| `gProfile` | BulkGate Profile ID |

## POST method - application/json

Example of full request:

```http
POST /api/1.0/simple/transactional HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache

{
    "application_id": "<APPLICATION_ID>",
    "application_token": "<APPLICATION_TOKEN>",
    "number": "7700900000",
    "text": "test_sms",
    "unicode": true,
    "sender_id": "gText",
    "sender_id_value": "BulkGate",
    "country": "gb"
}
```

Example of request with country prefix:

```http
POST /api/1.0/simple/transactional HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache

{
    "application_id": "<APPLICATION_ID>",
    "application_token": "<APPLICATION_TOKEN>",
    "number": "7700900000",
    "text": "test_sms",
    "country": "gb"
}
```

## Response — Success

```json
{
    "data": {
        "status": "accepted",
        "sms_id": "tmpde1bcd4b1d1",
        "part_id": [
            "tmpde1bcd4b1d1_1",
            "tmpde1bcd4b1d1_2",
            "tmpde1bcd4b1d1"
        ],
        "number": "447700900000"
    }
}
```

- `part_id` is the ID array of the parts of the original long message that were split because they did not meet the 160 character limit for a single message.

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

- `detail` is additional info about the error
- `code` represents HTTP error
- `type` and `error` can be found in the error types table

# BulkGate Simple API v1.0 — Promotional (Bulk) SMS

Source: https://help.bulkgate.com/docs/en/http-simple-promotional.html

## API URL

```
https://portal.bulkgate.com/api/1.0/simple/promotional
```

### Supported methods

- POST - application/json
- POST - application/x-www-form-urlencoded
- GET

### Parameters table

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| application_id | Application identificator | Yes | - |
| application_token | Application authentication token | Yes | - |
| number | Recipient number separated by `;` (semicolon) | Yes | - |
| text | Text of SMS message (max. 612 characters, or 268 characters if Unicode is used), UTF-8 encoding | Yes | - |
| unicode | `Yes`/`true`/`1` for Unicode SMS, `No`/`false`/`0` for 7bit SMS | No | `false` |
| sender_id | Sender ID, see sender ID type | No | `gSystem` |
| sender_id_value | Sender value | No | `null` |
| country | ISO 3166-1 alpha-2 country code | No | `null` |
| schedule | Schedule the sending date/time in unix timestamp, or ISO 8601. | No | Now |
| duplicates_check | `on` to prevent sending duplicate messages. `off` - no duplicates removed. | No | `off` |
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
POST /api/1.0/simple/promotional HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache

{
    "application_id": "<APPLICATION_ID>",
    "application_token": "<APPLICATION_TOKEN>",
    "number": "447700900000;7811901234;447712345678",
    "text": "test_sms",
    "unicode": true,
    "sender_id": "gText",
    "sender_id_value": "BulkGate",
    "country": "gb",
    "schedule": "2018-05-14T18:30:00-01:00"
}
```

Example with ISO 8601 schedule:

```http
POST /api/1.0/simple/promotional HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache

{
    "application_id": "<APPLICATION_ID>",
    "application_token": "<APPLICATION_TOKEN>",
    "number": "447700900000;7811901234;447712345678",
    "text": "test_sms",
    "schedule": "2018-05-14T18:30:00-01:00"
}
```

Example with unix timestamp schedule:

```http
POST /api/1.0/simple/promotional HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache

{
    "application_id": "<APPLICATION_ID>",
    "application_token": "<APPLICATION_TOKEN>",
    "number": "447700900000;7811901234;447712345678",
    "text": "test_sms",
    "schedule": 1526992636
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
                "error": 1
            }
        },
        "response": [
            {
                "status": "scheduled",
                "sms_id": "idfkvqrp-0",
                "part_id": ["idfkvqrp-0_1", "idfkvqrp-0_2", "idfkvqrp-0"],
                "number": "447700900000"
            },
            {
                "status": "scheduled",
                "sms_id": "idfkvqrp-1",
                "part_id": ["idfkvqrp-1_1", "idfkvqrp-1_2", "idfkvqrp-1"],
                "number": "447811901234"
            },
            {
                "status": "error",
                "code": 9,
                "error": "Invalid phone number",
                "number": "44771447678"
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

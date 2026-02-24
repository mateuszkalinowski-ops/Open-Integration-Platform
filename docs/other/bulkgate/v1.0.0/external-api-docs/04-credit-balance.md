# BulkGate Advanced API v2.0 — Check Credit Balance

Source: https://help.bulkgate.com/docs/en/http-advanced-check-credit-balance.html

## API URL

```
https://portal.bulkgate.com/api/2.0/advanced/info
```

```http
POST /api/2.0/advanced/info HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache
```

Supported versions: 1.0, 2.0.

### Parameters table

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| application_id | Application identificator | Yes | - |
| application_token | Application authentication token | Yes | - |

### Request example

```http
POST /api/2.0/advanced/info HTTP/1.1
Host: portal.bulkgate.com
Content-Type: application/json
Cache-Control: no-cache

{
    "application_id": "<APPLICATION_ID>",
    "application_token": "<APPLICATION_TOKEN>"
}
```

## Response — Success

```json
{
    "data": {
        "wallet": "bg1805151838000001",
        "credit": 215.8138,
        "currency": "credits",
        "free_messages": 51,
        "datetime": "2018-06-13T09:57:21+02:00"
    }
}
```

## Response — Error

```json
{
    "error": "authentication_failed",
    "code": 401
}
```

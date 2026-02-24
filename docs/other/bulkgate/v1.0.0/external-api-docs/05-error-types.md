# BulkGate API — Error Types

Source: https://help.bulkgate.com/docs/en/api-error-types.html

Error types applicable to both Advanced API and Simple API.

## Error types

| Type | Description | Info |
| --- | --- | --- |
| `unknown_identity` | Unknown identity / unauthorized / empty application_id | |
| `banned` | Account is blocked | |
| `invalid_numeric_sender` | Own sender not validated | |
| `empty_message` | Message text is empty | |
| `invalid_phone_number` | Invalid number | |
| `admin_not_found` | Admin not found | Transactional SMS only |
| `no_recipients` | Total recipients of bulk message is 0 | Bulk SMS only |
| `blacklisted_number` | Phone number is on Blacklist | |
| `low_credit` | Insufficient funds | |
| `method_not_allowed` | HTTP method is not allowed | |
| `unknown_action` | Unknown API action (Transactional/Bulk SMS) | |
| `unsupported_api_version` | Unknown/Deprecated API version | |
| `unknown` | Unknown error | |

## Response format

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

Fields:
- `detail` — additional info about the error
- `code` — HTTP error code
- `type` — error type identifier
- `error` — human-readable error description

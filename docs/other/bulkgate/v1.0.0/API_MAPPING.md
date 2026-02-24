# BulkGate SMS Gateway — API Field Mapping v1.0.0

## Platform ↔ BulkGate API Mapping

### Transactional SMS (Simple API v1.0)

| Platform Field | BulkGate API Field | Type | Required | Notes |
|---|---|---|---|---|
| `credentials.application_id` | `application_id` | string | Yes | From BulkGate Portal |
| `credentials.application_token` | `application_token` | string | Yes | From BulkGate Portal |
| `number` | `number` | string | Yes | International format |
| `text` | `text` | string | Yes | Max 612 chars (268 unicode) |
| `unicode` | `unicode` | bool | No | Default: `false` |
| `sender_id` | `sender_id` | enum | No | Default: `gSystem` |
| `sender_id_value` | `sender_id_value` | string | No | Required for gOwn/gText/gProfile |
| `country` | `country` | string | No | ISO 3166-1 alpha-2 |
| `schedule` | `schedule` | string | No | Unix timestamp or ISO 8601 |
| `duplicates_check` | `duplicates_check` | bool→string | No | Mapped to `on`/`off` |
| `tag` | `tag` | string | No | Message label |

### Promotional SMS (Simple API v1.0)

Same as Transactional except:

| Platform Field | BulkGate API Field | Type | Required | Notes |
|---|---|---|---|---|
| `number` | `number` | string | Yes | Semicolon-separated recipients |

### Advanced Transactional SMS (Advanced API v2.0)

| Platform Field | BulkGate API Field | Type | Required | Notes |
|---|---|---|---|---|
| `number` | `number` | string[] | Yes | Array of phone numbers |
| `text` | `text` | string | Yes | Supports `<variable>` placeholders |
| `variables` | `variables` | object | No | Key-value pairs for template |
| `channel.sms.sender_id` | `channel.sms.sender_id` | enum | No | |
| `channel.sms.sender_id_value` | `channel.sms.sender_id_value` | string | No | |
| `channel.sms.unicode` | `channel.sms.unicode` | bool | No | |
| `channel.sms.text` | `channel.sms.text` | string | No | SMS-specific text override |
| `channel.viber.sender` | `channel.viber.sender` | string | Yes* | Required if viber channel used |
| `channel.viber.expiration` | `channel.viber.expiration` | int | No | Default: 120 seconds |
| `channel.viber.text` | `channel.viber.text` | string | No | Viber-specific text override |

### Credit Balance (Advanced API v2.0)

| Platform Field | BulkGate API Field | Type | Notes |
|---|---|---|---|
| `credentials.application_id` | `application_id` | string | |
| `credentials.application_token` | `application_token` | string | |
| **Response:** | | | |
| `wallet` | `data.wallet` | string | Wallet ID |
| `credit` | `data.credit` | float | Current credit balance |
| `currency` | `data.currency` | string | Usually "credits" |
| `free_messages` | `data.free_messages` | int | Remaining free messages |

## Sender ID Types

| Platform Value | BulkGate Value | Description |
|---|---|---|
| `gSystem` | `gSystem` | System number |
| `gShort` | `gShort` | Short Code |
| `gText` | `gText` | Text sender (alphanumeric) |
| `gMobile` | `gMobile` | Mobile Connect |
| `gPush` | `gPush` | Mobile Connect push |
| `gOwn` | `gOwn` | Own verified number |
| `gProfile` | `gProfile` | BulkGate Sender ID Profile |

## Error Types

| BulkGate Error Type | HTTP Code | Description |
|---|---|---|
| `unknown_identity` | 401 | Invalid application_id or application_token |
| `empty_message` | 400 | Message text is empty |
| `invalid_phone_number` | 400 | Invalid recipient number |
| `low_credit` | 402 | Insufficient funds |
| `blacklisted_number` | 400 | Number on blacklist |
| `invalid_numeric_sender` | 400 | Own sender not validated |
| `no_recipients` | 400 | No valid recipients (bulk) |
| `banned` | 403 | Account blocked |
| `method_not_allowed` | 405 | HTTP method not allowed |
| `unsupported_api_version` | 400 | Unknown/deprecated API version |

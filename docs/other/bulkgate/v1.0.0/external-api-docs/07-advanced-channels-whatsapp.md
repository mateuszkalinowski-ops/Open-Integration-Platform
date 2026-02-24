# BulkGate Advanced API v2.0 — WhatsApp Channel Object

Source: https://help.bulkgate.com/docs/en/http-advanced-whatsapp.html

## WhatsApp object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| sender | Text sender. Needs to be registered first. Contact support for registration. | Yes | - |
| expiration | Time limit after which alternative channel will be used (seconds) | No | `3600` |
| template | Template object. Cannot be used with Message, File, Otp, Location. | No | `null` |
| message | Message object. Cannot be used with Template, File, Otp, Location. | No | `null` |
| file | File object. Cannot be used with Template, Message, Otp, Location. | No | `null` |
| otp | OTP object. Cannot be used with Template, Message, File, Location. | No | `null` |
| location | Location object. Cannot be used with Template, Message, File, Otp. | No | `null` |

## Template object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| template | Template text | No | `null` |
| language | Language in ISO format | No | `en` |
| header | Template header object | No | `null` |
| body | Template body object | No | `null` |
| buttons | Array of template button objects | No | `null` |

### Template header object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| type | Type of header (`image`, `video`, `text`, `location`) | Yes | - |
| url | Path to video or image (used with `image`, `video` type) | Conditional | - |
| text | Text (used with `text` type) | Conditional | - |
| location | Location object (used with `location` type) | Conditional | - |

### Template body object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| type | Type of body (`text`, `price`, `currency`) | No | `text` |
| text | Text (used with `text` type) | Conditional | - |
| amount | Amount of set currency | Conditional | - |
| currency | Currency | Conditional | - |

### Template buttons object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| type | Type of button (`payload`, `url`) | No | `url` |
| index | Index of defined button | Yes | - |
| payload | Metadata sent after clicking (only with `payload` type) | Conditional | - |
| text | URL for redirect (only with `url` type) | Conditional | - |

## Message object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| text | Text of a message | Yes | - |
| preview_url | Preview sent URL as a thumbnail | No | `true` |

## File object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| type | Type of file (`image`, `video`, `audio`, `document`, `sticker`) | No | `image` |
| url | Path to the file | Yes | - |
| caption | Caption of sent file | No | `""` |

## OTP object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| template | Template of text message with the code | Yes | - |
| code | One time code | Yes | - |
| language | Language (if `null`, detected from phone number) | Yes | - |

## Location object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| latitude | Latitude (float) | No | - |
| longitude | Longitude (float) | No | - |
| name | Name of sent location | No | - |
| address | Address of sent location | No | - |

## Example — Template request

```json
{
    "application_id": "APPLICATION_ID",
    "application_token": "APPLICATION_TOKEN",
    "number": ["+420777777777"],
    "text": "Test text",
    "channel": {
        "whatsapp": {
            "sender": "420777777777",
            "expiration": 300,
            "template": {
                "template": "test_template",
                "language": "cz",
                "header": {
                    "type": "image",
                    "url": "test_url",
                    "caption": "test_caption"
                },
                "body": [
                    {"type": "currency", "amount": 20.5, "currency": "euro"}
                ],
                "buttons": [
                    {"type": "payload", "index": 1, "payload": "test_payload"}
                ]
            }
        }
    }
}
```

## Example — Message request

```json
{
    "application_id": "APPLICATION_ID",
    "application_token": "APPLICATION_TOKEN",
    "number": ["+420777777777"],
    "text": "Test text",
    "channel": {
        "whatsapp": {
            "sender": "420777777777",
            "expiration": 300,
            "message": {
                "text": "title",
                "preview_url": true
            }
        }
    }
}
```

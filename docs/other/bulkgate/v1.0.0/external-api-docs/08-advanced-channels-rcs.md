# BulkGate Advanced API v2.0 — RCS Channel Object

Source: https://help.bulkgate.com/docs/en/http-advanced-rcs.html

## RCS object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| sender | Text sender. Needs to be registered first. Contact support for registration. | Yes | - |
| expiration | Time limit after which alternative channel will be used (seconds) | No | `3600` |
| message | Message object. Cannot be used with File, Card, Carousel. | No | `null` |
| file | File object. Cannot be used with Message, Card, Carousel. | No | `null` |
| card | Card object. Cannot be used with Message, File, Carousel. | No | `null` |
| carousel | Carousel object. Cannot be used with Message, File, Card. | No | `null` |

## Message object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| text | Text of RCS message | Yes | - |
| suggestions | Suggestions array | No | `[]` |

## File object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| url | Path to the file | Yes | - |
| force_refresh | Force RBM to fetch new content | No | `false` |
| suggestions | Suggestions array | No | `[]` |

## Card object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| title | Title of the card | No | `null` |
| description | Description of the card | No | `null` |
| alignment | Align card (left/right) | No | `null` |
| orientation | Orientation (horizontal/vertical) | No | `null` |
| media | Card media object | No | `null` |
| suggestions | Suggestions array | No | `[]` |

### Card Media object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| url | Path to the media object | Yes | - |
| force_refresh | Force refresh from URL | No | `false` |
| height | Height (Short, Medium, Tall) | No | `null` |

## Carousel object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| width | Width (small, medium) | No | `null` |
| cards | List of carousel cards | No | `[]` |

## Suggestion types

| VALUE | DESCRIPTION |
| --- | --- |
| `reply` | Quick reply |
| `dial_number` | Pre-dial number |
| `view_location` | Display received location |
| `share_location` | Share recipient's location |
| `open_url` | Open received URL |
| `create_calendar_event` | Create calendar event |

## Suggestions object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| type | Suggestion type (see table above) | No | `reply` |
| text | Text of suggestion button | Yes | - |
| postback | Content sent in reply when button is pressed | No | `"Ok"` |
| location | Location object (for `view_location` type) | Conditional | - |
| calendar | Calendar object (for `create_calendar_event` type) | Conditional | - |
| phone_number | Phone number (for `dial_number` type) | Conditional | - |
| url | URL (for `open_url` type) | Conditional | - |

### Location object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| latitude | Float value of latitude | Conditional | `null` |
| longitude | Float value of longitude | Conditional | `null` |
| query | String name of location | Conditional | `null` |
| label | Label for the location | No | `null` |

### Calendar object

| PARAMETER NAME | VALUE | MANDATORY | DEFAULT VALUE |
| --- | --- | --- | --- |
| start | DateTime of event start | No | `null` |
| end | DateTime of event end | No | `null` |
| title | Title of calendar event | No | `null` |
| description | Description of the event | No | `null` |
| timezone | Timezone string | No | `null` |

## Example — Message with suggestions

```json
{
    "application_id": "APPLICATION_ID",
    "application_token": "APPLICATION_TOKEN",
    "number": ["+420777777777"],
    "text": "Test text",
    "channel": {
        "rcs": {
            "sender": "BulkGate",
            "message": {
                "text": "text",
                "suggestions": [
                    {
                        "type": "view_location",
                        "text": "View",
                        "location": {
                            "query": "Karluv most",
                            "latitude": 50.086584,
                            "longitude": 14.410763,
                            "label": "Karluv most"
                        }
                    }
                ]
            }
        }
    }
}
```

## Example — Card with media

```json
{
    "application_id": "APPLICATION_ID",
    "application_token": "APPLICATION_TOKEN",
    "number": ["+420777777777"],
    "text": "Test text",
    "channel": {
        "rcs": {
            "sender": "BulkGate",
            "card": {
                "title": "Card title",
                "description": "Card description",
                "media": {
                    "url": "PATH_TO_AN_IMAGE"
                },
                "suggestions": []
            }
        }
    }
}
```

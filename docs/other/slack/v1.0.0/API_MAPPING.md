# API Mapping — Slack v1.0.0

Maps Pinquark platform actions/events to the Slack Web API methods.

## Actions → Slack Web API

| Platform Action | Slack Web API Method | Description |
|---|---|---|
| `message.send` | `chat.postMessage` | Send a message to a channel or thread |
| `message.fetch` | `conversations.history` | Retrieve message history from a channel |
| `channel.list` | `conversations.list` | List all channels the bot has access to |
| `file.upload` | `files.upload` | Upload a file to one or more channels |
| `reaction.add` | `reactions.add` | Add an emoji reaction to a message |

## Events → Slack Events

| Platform Event | Trigger | Description |
|---|---|---|
| `message.received` | Poller detects new message | A new message appeared in a monitored channel |
| `message.sent` | After `chat.postMessage` | Confirmation that message was sent |
| `reaction.added` | After `reactions.add` | Confirmation that reaction was added |

## Field Mapping — message.send

| Platform Field | Slack API Field | Type | Required |
|---|---|---|---|
| `channel` | `channel` | string | Yes |
| `text` | `text` | string | Yes |
| `thread_ts` | `thread_ts` | string | No |
| `blocks` | `blocks` | object[] | No |
| `unfurl_links` | `unfurl_links` | boolean | No |

## Field Mapping — message.fetch (conversations.history)

| Platform Field | Slack API Field | Type | Required |
|---|---|---|---|
| `channel` | `channel` | string | Yes |
| `limit` | `limit` | integer | No |
| `oldest` | `oldest` | string (ts) | No |
| `latest` | `latest` | string (ts) | No |

## Field Mapping — channel.list (conversations.list)

| Platform Field | Slack API Field | Type | Required |
|---|---|---|---|
| `types` | `types` | string (csv) | No |
| `limit` | `limit` | integer | No |

## Field Mapping — file.upload

| Platform Field | Slack API Field | Type | Required |
|---|---|---|---|
| `channels` | `channels` | string (csv) | Yes |
| `filename` | `filename` | string | Yes |
| `content_base64` | `file` (decoded) | bytes | Yes |
| `title` | `title` | string | No |
| `initial_comment` | `initial_comment` | string | No |

## Field Mapping — reaction.add

| Platform Field | Slack API Field | Type | Required |
|---|---|---|---|
| `channel` | `channel` | string | Yes |
| `timestamp` | `timestamp` | string | Yes |
| `name` | `name` | string | Yes |

## Message Object Fields

| Platform Field | Slack API Field | Description |
|---|---|---|
| `channel_id` | `channel` | Channel ID |
| `channel_name` | resolved from `conversations.info` | Human-readable channel name |
| `user_id` | `user` | Slack user ID |
| `user_name` | resolved from `users.info` | Real name of the user |
| `text` | `text` | Message text content |
| `ts` | `ts` | Slack timestamp (unique message ID) |
| `thread_ts` | `thread_ts` | Thread parent timestamp |
| `reply_count` | `reply_count` | Number of replies in thread |
| `bot_id` | `bot_id` | Bot ID (if sent by bot) |
| `attachments` | `attachments` | Legacy attachments |
| `blocks` | `blocks` | Block Kit blocks |
| `files` | `files` | Uploaded files |

## Authentication

Slack uses **Bot User OAuth Token** (`xoxb-...`) for all Web API calls. The token is sent as a Bearer token in the `Authorization` header.

| Auth Method | Header | Token Format |
|---|---|---|
| Bot Token | `Authorization: Bearer xoxb-...` | `xoxb-{team_id}-{bot_id}-{random}` |

Required bot token scopes:
- `channels:history`, `channels:read`
- `groups:history`, `groups:read`
- `chat:write`
- `files:write`
- `reactions:write`
- `users:read`

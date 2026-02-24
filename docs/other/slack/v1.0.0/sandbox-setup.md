# Sandbox Setup — Slack v1.0.0

## Creating a Test Slack App

1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. Name it (e.g., `Pinquark Integration Test`) and select a development workspace
4. Navigate to **OAuth & Permissions**

## Required Bot Token Scopes

Add these scopes under **Bot Token Scopes**:

| Scope | Reason |
|---|---|
| `channels:history` | Read message history in public channels |
| `channels:read` | List public channels |
| `groups:history` | Read message history in private channels |
| `groups:read` | List private channels |
| `chat:write` | Send messages |
| `files:write` | Upload files |
| `reactions:write` | Add emoji reactions |
| `users:read` | Look up user names |

## Installing the App

1. Click **Install to Workspace** at the top of the OAuth & Permissions page
2. Review and allow the requested permissions
3. Copy the **Bot User OAuth Token** (`xoxb-...`)

## Configuring the Integrator

Add the token to `config/accounts.yaml`:

```yaml
accounts:
  - name: test-workspace
    bot_token: "xoxb-your-copied-token"
    default_channel: "test-channel"
    environment: sandbox
```

Or set environment variables:

```bash
SLACK_ACCOUNT_0_NAME=test-workspace
SLACK_ACCOUNT_0_BOT_TOKEN=xoxb-your-copied-token
SLACK_ACCOUNT_0_DEFAULT_CHANNEL=test-channel
```

## Testing

1. Create a `#test-channel` channel in your workspace
2. Invite the bot to the channel: `/invite @YourBotName`
3. Start the integrator and send a test message:

```bash
curl -X POST http://localhost:8000/messages/send?account_name=test-workspace \
  -H "Content-Type: application/json" \
  -d '{"channel": "test-channel", "text": "Hello from Pinquark!"}'
```

## Rate Limits

Slack enforces rate limits per method per workspace. The integrator handles `429 Too Many Requests` responses with automatic retry using the `Retry-After` header.

Typical limits:
- `chat.postMessage`: ~1 message per second per channel
- `conversations.history`: Tier 3 (~50 requests per minute)
- `conversations.list`: Tier 2 (~20 requests per minute)

See: https://api.slack.com/docs/rate-limits

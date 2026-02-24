# Slack Integrator v1.0.0

Connector for the **Slack** messaging platform. Enables sending messages to channels, polling for new messages, uploading files, managing reactions, and listing channels across multiple Slack workspaces.

## Features

- **Multi-workspace support** — manage multiple Slack Bot tokens simultaneously
- **Send messages** — post to channels, reply in threads, use Block Kit
- **Channel history** — fetch message history with time range filtering
- **File uploads** — upload files to channels with comments
- **Reactions** — add emoji reactions to messages
- **Background polling** — detect new messages on a configurable interval
- **Kafka integration** — publish `message.received` events to Kafka topics
- **Prometheus metrics** — track API call latency, error rates, and throughput

## Prerequisites

1. A Slack workspace with a Slack App created at https://api.slack.com/apps
2. **Bot Token Scopes** required:
   - `channels:history` — read public channel messages
   - `channels:read` — list public channels
   - `chat:write` — send messages
   - `files:write` — upload files
   - `groups:history` — read private channel messages
   - `groups:read` — list private channels
   - `reactions:write` — add reactions
   - `users:read` — resolve user names
3. Install the app to your workspace and copy the **Bot User OAuth Token** (`xoxb-...`)

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Configure your Slack bot token in config/accounts.yaml
# or via environment variables

# 3. Start the integrator
docker compose up -d slack-integrator

# 4. Verify health
curl http://localhost:8000/health

# 5. Open API docs
open http://localhost:8000/docs
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SLACK_LOG_LEVEL` | `INFO` | Logging level |
| `SLACK_POLLING_ENABLED` | `true` | Enable background message polling |
| `SLACK_POLLING_INTERVAL_SECONDS` | `30` | Polling interval |
| `KAFKA_ENABLED` | `false` | Publish events to Kafka |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka brokers |
| `DATABASE_URL` | `sqlite+aiosqlite:///...` | Poller state persistence |

### Account Configuration

Via `config/accounts.yaml`:

```yaml
accounts:
  - name: my-workspace
    bot_token: "xoxb-your-bot-token"
    app_token: "xapp-your-app-token"  # optional
    default_channel: "general"
    environment: production
```

Or via environment variables:

```bash
SLACK_ACCOUNT_0_NAME=my-workspace
SLACK_ACCOUNT_0_BOT_TOKEN=xoxb-your-bot-token
SLACK_ACCOUNT_0_DEFAULT_CHANNEL=general
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/readiness` | Readiness check |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/accounts` | List configured accounts |
| `POST` | `/accounts` | Add account at runtime |
| `DELETE` | `/accounts/{name}` | Remove account |
| `GET` | `/auth/{account}/status` | Auth status for account |
| `POST` | `/auth/{account}/test` | Test connection |
| `GET` | `/channels` | List channels |
| `GET` | `/messages` | Get channel message history |
| `POST` | `/messages/send` | Send a message |
| `POST` | `/reactions/add` | Add emoji reaction |
| `POST` | `/files/upload` | Upload a file |

## Running Tests

```bash
# Unit tests
docker compose --profile test up --abort-on-container-exit

# Or locally
pip install -r requirements-dev.txt
pytest tests/ -v --tb=short
```

## Development

```bash
# Start in dev mode with hot-reload
docker compose --profile dev up slack-integrator-dev
```

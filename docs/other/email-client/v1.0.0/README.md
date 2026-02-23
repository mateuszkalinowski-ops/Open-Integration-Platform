# Email Client Integrator v1.0.0

Universal IMAP/SMTP email client connector for Open Integration Platform by Pinquark.com.
Enables receiving and sending email messages at configurable time intervals.

## Features

- **Receiving emails** — IMAP polling at a configurable interval (default every 60s)
- **Sending emails** — SMTP with HTML, attachments, and priority support
- **Multiple accounts** — support for multiple email accounts simultaneously
- **IMAP folders** — listing, browsing different folders
- **Message operations** — marking as read, deleting
- **Kafka** — publishing `email.received` / `email.sent` events to Kafka
- **Prometheus** — IMAP/SMTP connection time metrics, operation counts

## Requirements

- Python 3.12+
- Email account with IMAP/SMTP access (e.g. Gmail with App Password, Outlook, any server)
- Docker (optional)

## Quick Start

### 1. Account Configuration

Create a `config/accounts.yaml` file:

```yaml
accounts:
  - name: moje-konto
    email_address: "user@example.com"
    username: ""  # optional — if IMAP/SMTP login differs from email_address
    password: "app-password"
    imap_host: "imap.gmail.com"
    imap_port: 993
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    use_ssl: true
    polling_folder: "INBOX"
    environment: production
```

Or use environment variables:

```bash
EMAIL_ACCOUNT_0_NAME=moje-konto
EMAIL_ACCOUNT_0_EMAIL_ADDRESS=user@example.com
EMAIL_ACCOUNT_0_USERNAME=        # optional, if login != email
EMAIL_ACCOUNT_0_PASSWORD=app-password
EMAIL_ACCOUNT_0_IMAP_HOST=imap.gmail.com
EMAIL_ACCOUNT_0_SMTP_HOST=smtp.gmail.com
```

### 2. Local Launch

```bash
cp .env.example .env
# Fill in account details in .env or config/accounts.yaml
docker compose up -d
```

### 3. Running in Development Mode

```bash
docker compose --profile dev up email-client-integrator-dev
```

### 4. Running Tests

```bash
docker compose --profile test up tests
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/readiness` | Readiness check with dependency verification |
| `GET` | `/docs` | Swagger UI — interactive API documentation |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/accounts` | List of configured accounts |
| `POST` | `/accounts` | Add a new email account |
| `DELETE` | `/accounts/{name}` | Remove an account |
| `GET` | `/emails?account_name=...` | List emails from a folder |
| `GET` | `/emails/{uid}?account_name=...` | Retrieve a single email |
| `POST` | `/emails/send?account_name=...` | Send an email |
| `PUT` | `/emails/{uid}/read?account_name=...` | Mark as read |
| `DELETE` | `/emails/{uid}?account_name=...` | Delete an email |
| `GET` | `/folders?account_name=...` | List IMAP folders |
| `GET` | `/connection/{account}/status` | IMAP/SMTP connection status |
| `GET` | `/auth/{account}/status` | Authentication status |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_LOG_LEVEL` | `INFO` | Log level |
| `EMAIL_POLLING_ENABLED` | `true` | Enable IMAP polling |
| `EMAIL_POLLING_INTERVAL_SECONDS` | `60` | Polling interval (seconds) |
| `EMAIL_POLLING_FOLDER` | `INBOX` | Default IMAP folder |
| `EMAIL_POLLING_MAX_EMAILS` | `50` | Max emails per polling cycle |
| `DATABASE_URL` | `sqlite+aiosqlite:///...` | State database URL |
| `KAFKA_ENABLED` | `false` | Publish to Kafka |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker addresses |

## Protocols

### IMAP (receiving)

- Protocol: IMAP4rev1 (RFC 3501)
- Ports: 993 (SSL/TLS), 143 (STARTTLS)
- Authentication: LOGIN (username + password / App Password)
- Polling: SEARCH UNSEEN at a configurable interval

### SMTP (sending)

- Protocol: SMTP (RFC 5321) + MIME (RFC 2045)
- Ports: 587 (STARTTLS), 465 (SSL/TLS), 25 (unencrypted)
- Authentication: PLAIN / LOGIN
- Support: HTML body, attachments, CC/BCC, priorities, Reply-To

## Kafka Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `email.output.other.emails.received` | Output | New received emails |
| `email.output.other.emails.sent` | Output | Sent emails |

## Common Server Configurations

| Provider | IMAP Host | IMAP Port | SMTP Host | SMTP Port |
|----------|-----------|-----------|-----------|-----------|
| Gmail | `imap.gmail.com` | 993 | `smtp.gmail.com` | 587 |
| Outlook/Hotmail | `outlook.office365.com` | 993 | `smtp.office365.com` | 587 |
| Yahoo | `imap.mail.yahoo.com` | 993 | `smtp.mail.yahoo.com` | 587 |
| Zoho | `imap.zoho.com` | 993 | `smtp.zoho.com` | 587 |
| Custom | varies | 993 | varies | 587 |

> **Gmail**: requires App Password (2FA enabled) or OAuth2 (future version).

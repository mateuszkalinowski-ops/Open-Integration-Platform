# FTP/SFTP Integrator v1.0.0

FTP and SFTP file transfer connector for the Open Integration Platform by Pinquark.com.

## Overview

This connector provides a unified REST API for interacting with remote FTP and SFTP servers. It supports file upload, download, listing, deletion, moving/renaming, directory creation, and automatic polling for new files.

## Features

- **Dual protocol**: FTP (aioftp) and SFTP (asyncssh) via a single unified API
- **File operations**: upload, download, list, delete, move/rename
- **Directory operations**: create, list (filtered to directories only)
- **New file polling**: background task detects new files on configured paths
- **Multi-account**: manage multiple FTP/SFTP servers from a single instance
- **Kafka integration**: publish `file.new`, `file.uploaded`, `file.deleted` events
- **Platform events**: notify the Flow Engine when new files are detected
- **Glob filtering**: list files matching a pattern (e.g., `*.csv`, `report_*.xlsx`)
- **Base path support**: configure a root directory per account
- **Connection testing**: validate credentials before use
- **Prometheus metrics**: standard integrator metrics at `/metrics`
- **Health checks**: `/health` and `/readiness` endpoints

## Quick Start

### 1. Configure accounts

Edit `config/accounts.yaml`:

```yaml
accounts:
  - name: my-sftp
    host: sftp.example.com
    protocol: sftp
    port: 22
    username: myuser
    password: mypassword
    base_path: /data/exchange
    environment: production

  - name: legacy-ftp
    host: ftp.legacy.example.com
    protocol: ftp
    port: 21
    username: ftpuser
    password: ftppass
    passive_mode: true
    base_path: /
    environment: production
```

### 2. Environment variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|---|---|---|
| `FTP_LOG_LEVEL` | `INFO` | Log level |
| `FTP_POLLING_ENABLED` | `false` | Enable background polling |
| `FTP_POLLING_INTERVAL_SECONDS` | `300` | Polling interval |
| `FTP_POLLING_PATH` | `/` | Directory to poll |
| `FTP_CONNECT_TIMEOUT` | `15.0` | Connection timeout (s) |
| `FTP_OPERATION_TIMEOUT` | `60.0` | Operation timeout (s) |
| `KAFKA_ENABLED` | `false` | Enable Kafka publishing |

### 3. Run locally

```bash
# Development mode (with hot reload)
docker compose --profile dev up -d

# Production mode
docker compose up -d

# With test SFTP server
docker compose --profile dev up -d sftp-server ftp-sftp-integrator-dev
```

### 4. Run tests

```bash
docker compose --profile test run --rm tests
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/readiness` | Readiness check (includes DB) |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/auth/{account_name}/test` | Test connection |
| `GET` | `/auth/status` | All accounts status |
| `GET` | `/accounts` | List accounts |
| `POST` | `/accounts` | Add account |
| `DELETE` | `/accounts/{account_name}` | Remove account |
| `GET` | `/files` | List files |
| `POST` | `/files/upload` | Upload file |
| `GET` | `/files/download` | Download file |
| `DELETE` | `/files` | Delete file |
| `POST` | `/files/move` | Move/rename file |
| `POST` | `/directories` | Create directory |
| `GET` | `/directories` | List directories |

All file/directory endpoints require `account_name` query parameter.

## Architecture

```
src/
├── main.py                    # FastAPI app with lifespan
├── config.py                  # Pydantic settings
├── api/
│   ├── routes.py              # REST endpoints
│   └── dependencies.py        # Shared AppState
├── ftp_client/
│   ├── client.py              # Unified FTP/SFTP client (aioftp + asyncssh)
│   ├── integration.py         # Orchestration facade
│   ├── poller.py              # Background new-file poller
│   └── schemas.py             # Pydantic request/response models
├── services/
│   └── account_manager.py     # Multi-account configuration
└── models/
    └── database.py            # SQLite state for poller
```

## Protocol Details

### FTP (RFC 959)

- Uses `aioftp` async FTP client
- Supports passive mode (default) and active mode
- Authentication: username/password
- Timeout: configurable per operation

### SFTP (SSH File Transfer Protocol)

- Uses `asyncssh` for SSH connections
- Authentication: password or SSH private key (PEM format)
- Host key verification disabled by default (configurable)
- Supports `makedirs` for recursive directory creation

## Kafka Topics

| Topic | Event | Description |
|---|---|---|
| `ftp-sftp.output.other.files.new` | `file.new` | New file detected by poller |
| `ftp-sftp.output.other.files.uploaded` | `file.uploaded` | File uploaded via API |
| `ftp-sftp.output.other.files.deleted` | `file.deleted` | File deleted via API |

## Flow Engine Integration

The connector emits `file.new` events when the poller detects new files. These can be used in flows:

```yaml
source:
  connector: ftp-sftp
  event: file.new
  filter:
    filename: "*.csv"
destination:
  connector: pinquark-wms
  action: document.create
mapping:
  - from: filename -> to: documentName
  - from: path -> to: sourcePath
```

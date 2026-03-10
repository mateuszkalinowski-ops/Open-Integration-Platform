# Amazon S3 Connector — v1.0.0

## Overview

Amazon S3 (and S3-compatible) object storage integration for the Open Integration Platform by Pinquark.com.

Supports:
- Amazon S3
- MinIO
- Wasabi
- DigitalOcean Spaces
- Backblaze B2
- Any S3-compatible storage

## Features

- **Object operations**: upload, download, list, delete, copy
- **Bucket management**: list, create, delete
- **Pre-signed URLs**: generate temporary access URLs for GET/PUT
- **Polling**: background detection of new objects with Kafka/platform events
- **Multi-account**: manage multiple S3 accounts (AWS, MinIO, Wasabi, etc.)
- **S3-compatible**: works with any S3-compatible endpoint via `endpoint_url` + `use_path_style`

## Quick Start

### 1. Configure accounts

Edit `config/accounts.yaml`:

```yaml
accounts:
  - name: production-aws
    aws_access_key_id: ${AWS_ACCESS_KEY_ID}
    aws_secret_access_key: ${AWS_SECRET_ACCESS_KEY}
    region: eu-central-1
    default_bucket: my-data-bucket
    environment: production
```

### 2. Run with Docker Compose

```bash
# Production
docker compose up -d s3-integrator

# Development (with MinIO)
docker compose --profile dev up -d
```

### 3. Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/readiness` | Readiness check |
| `GET` | `/accounts` | List configured accounts |
| `POST` | `/accounts` | Add account |
| `DELETE` | `/accounts/{name}` | Remove account |
| `POST` | `/auth/{name}/test` | Test S3 connection |
| `GET` | `/auth/status` | All account statuses |
| `GET` | `/objects` | List objects |
| `POST` | `/objects/upload` | Upload object (base64) |
| `GET` | `/objects/download` | Download object (base64) |
| `DELETE` | `/objects` | Delete object |
| `POST` | `/objects/copy` | Copy object |
| `POST` | `/objects/presign` | Generate pre-signed URL |
| `GET` | `/buckets` | List buckets |
| `POST` | `/buckets` | Create bucket |
| `DELETE` | `/buckets/{name}` | Delete bucket |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_LOG_LEVEL` | `INFO` | Log level |
| `S3_POLLING_ENABLED` | `false` | Enable object polling |
| `S3_POLLING_INTERVAL_SECONDS` | `300` | Polling interval |
| `S3_POLLING_BUCKET` | | Bucket to poll |
| `S3_POLLING_PREFIX` | | Key prefix to poll |
| `S3_CONNECT_TIMEOUT` | `15.0` | Connection timeout (s) |
| `S3_OPERATION_TIMEOUT` | `60.0` | Operation timeout (s) |
| `KAFKA_ENABLED` | `false` | Publish events to Kafka |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka brokers |
| `PLATFORM_API_URL` | `http://platform:8080` | Platform API URL |

### Account Configuration

Each account supports:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique account name |
| `aws_access_key_id` | Yes | AWS access key |
| `aws_secret_access_key` | Yes | AWS secret key |
| `region` | No | AWS region (default: `us-east-1`) |
| `endpoint_url` | No | Custom S3 endpoint (for MinIO, Wasabi, etc.) |
| `default_bucket` | No | Default bucket for operations |
| `use_path_style` | No | Path-style addressing (default: `false`, required for MinIO) |
| `environment` | No | Environment tag (default: `production`) |

## S3-compatible Storage

### MinIO

```yaml
accounts:
  - name: minio
    aws_access_key_id: minioadmin
    aws_secret_access_key: minioadmin
    region: us-east-1
    endpoint_url: http://minio:9000
    use_path_style: true
    default_bucket: my-bucket
```

### Wasabi

```yaml
accounts:
  - name: wasabi
    aws_access_key_id: ${WASABI_ACCESS_KEY}
    aws_secret_access_key: ${WASABI_SECRET_KEY}
    region: eu-central-1
    endpoint_url: https://s3.eu-central-1.wasabisys.com
    default_bucket: archive
```

### DigitalOcean Spaces

```yaml
accounts:
  - name: do-spaces
    aws_access_key_id: ${DO_SPACES_KEY}
    aws_secret_access_key: ${DO_SPACES_SECRET}
    region: fra1
    endpoint_url: https://fra1.digitaloceanspaces.com
    default_bucket: my-space
```

## Kafka Topics

| Topic | Event |
|-------|-------|
| `s3.output.other.objects.new` | New object detected (polling) |
| `s3.output.other.objects.uploaded` | Object uploaded |
| `s3.output.other.objects.deleted` | Object deleted |

## Development

```bash
# Start dev environment with MinIO
docker compose --profile dev up -d

# Access MinIO Console
open http://localhost:9001  # login: minioadmin / minioadmin

# Run tests
docker compose --profile test up tests
```

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov --cov-report=html
```

# SkanujFakture Integrator v1.0.0

Integration with the invoice OCR system [SkanujFakture.pl](https://skanujfakture.pl) — automatic scanning, recognition, and management of accounting documents.

## Features

- Upload documents (PDF, JPG, PNG) with automatic OCR recognition
- Retrieve scanned documents with all details (contractor, amounts, VAT, line items)
- Update and delete documents
- Manage document attributes
- Posting dictionaries (cost types, cost centers)
- Integration with KSeF (National e-Invoice System) — XML retrieval, QR codes, sending FA3 invoices
- Company and entity management
- Automatic polling for new documents with Kafka publishing
- Multi-account SkanujFakture support

## Requirements

- Python 3.12+
- Docker (optional)
- Account on skanujfakture.pl

## Quick Start

### 1. Account Configuration

Copy the configuration file:

```bash
cp config/accounts.yaml.example config/accounts.yaml
```

Fill in your login credentials:

```yaml
accounts:
  - name: moja-firma
    login: "user@example.com"
    password: "twoje-haslo"
    api_url: "https://skanujfakture.pl:8443/SFApi"
    company_id: 147
    environment: production
```

### 2. Docker (recommended)

```bash
cp .env.example .env
# Fill in .env
docker compose up -d
```

Available profiles:
- **Production**: `docker compose up -d`
- **Development**: `docker compose --profile dev up -d`
- **Tests**: `docker compose --profile test up`

### 3. Local Launch

```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

After launch, Swagger documentation is available at: `http://localhost:8000/docs`

### Health & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness check |
| `/readiness` | GET | Readiness check |
| `/metrics` | GET | Prometheus metrics |

### Accounts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/accounts` | GET | List accounts |
| `/accounts` | POST | Add an account |
| `/accounts/{name}` | DELETE | Remove an account |
| `/auth/{name}/status` | GET | Authentication status |
| `/connection/{name}/status` | GET | Connection status |

### Companies

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/companies` | GET | List companies |
| `/companies/{id}/entities` | GET | List entities |

### Documents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/companies/{id}/documents` | POST | Upload document (form-data) |
| `/companies/{id}/documents/v2` | POST | Upload with document type |
| `/companies/{id}/documents` | GET | List documents |
| `/companies/{id}/documents/simple` | GET | Simplified list |
| `/companies/{id}/documents/{docId}` | PUT | Update document |
| `/companies/{id}/documents` | DELETE | Delete documents |
| `/companies/{id}/documents/{docId}/file` | GET | Original file |
| `/companies/{id}/documents/{docId}/image` | GET | Document image |

### Attributes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/companies/{id}/documents/{docId}/attributes` | PUT | Edit attributes |
| `/companies/{id}/documents/{docId}/attributes` | DELETE | Remove attributes |

### Dictionaries (posting)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/companies/{id}/dictionaries` | GET | Retrieve dictionary |
| `/companies/{id}/dictionaries` | POST | Add entry |

### KSeF

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/companies/{id}/documents/{docId}/ksef-xml` | GET | KSeF invoice XML |
| `/companies/{id}/documents/{docId}/ksef-qr` | GET | KSeF QR code |
| `/companies/{id}/ksef/invoice` | PUT | Send invoice to KSeF |

## SkanujFakture API Authentication

The SkanujFakture API uses **Basic Authentication**. Login and password are base64-encoded and sent in the `Authorization` header.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SF_LOG_LEVEL` | `INFO` | Log level |
| `SF_POLLING_ENABLED` | `true` | Automatic polling |
| `SF_POLLING_INTERVAL_SECONDS` | `300` | Polling interval (s) |
| `SF_POLLING_STATUS_FILTER` | `zeskanowany` | Status filter |
| `DATABASE_URL` | `sqlite+aiosqlite:///...` | State database |
| `KAFKA_ENABLED` | `false` | Publish to Kafka |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka addresses |

## Kafka Topics

| Topic | Description |
|-------|-------------|
| `skanujfakture.output.other.documents.scanned` | Newly scanned documents |
| `skanujfakture.output.other.documents.uploaded` | Uploaded documents |

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov --cov-report=html
```

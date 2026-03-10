# Sandbox Setup — S3 Connector

## Option 1: MinIO (Recommended for Local Development)

MinIO is an S3-compatible object storage server ideal for local development and testing.

### Start MinIO via Docker Compose

```bash
cd integrators/other/s3/v1.0.0
docker compose --profile dev up -d minio
```

### Access MinIO Console

- URL: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

### Create Test Bucket

Via MinIO Console or CLI:

```bash
# Install mc (MinIO Client)
brew install minio/stable/mc  # macOS

# Configure alias
mc alias set local http://localhost:9000 minioadmin minioadmin

# Create bucket
mc mb local/test-bucket
```

### Configure Connector Account

```yaml
# config/accounts.yaml
accounts:
  - name: local-minio
    aws_access_key_id: minioadmin
    aws_secret_access_key: minioadmin
    region: us-east-1
    endpoint_url: http://minio:9000
    use_path_style: true
    default_bucket: test-bucket
    environment: development
```

## Option 2: AWS S3 (Sandbox Account)

### Create IAM User

1. Go to AWS IAM Console
2. Create a new IAM user for testing
3. Attach policy `AmazonS3FullAccess` (or a scoped policy)
4. Generate access key + secret key

### Create Test Bucket

```bash
aws s3 mb s3://pinquark-integration-test --region eu-central-1
```

### Configure Connector Account

```yaml
accounts:
  - name: aws-sandbox
    aws_access_key_id: ${AWS_ACCESS_KEY_ID}
    aws_secret_access_key: ${AWS_SECRET_ACCESS_KEY}
    region: eu-central-1
    default_bucket: pinquark-integration-test
    environment: sandbox
```

## Option 3: LocalStack

LocalStack provides a local AWS emulator.

```bash
docker run -d \
  --name localstack \
  -p 4566:4566 \
  -e SERVICES=s3 \
  localstack/localstack

# Create bucket
aws --endpoint-url http://localhost:4566 s3 mb s3://test-bucket
```

Configure:

```yaml
accounts:
  - name: localstack
    aws_access_key_id: test
    aws_secret_access_key: test
    region: us-east-1
    endpoint_url: http://localhost:4566
    use_path_style: true
    default_bucket: test-bucket
    environment: development
```

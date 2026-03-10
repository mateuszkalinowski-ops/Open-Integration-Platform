# API Mapping — S3 Connector v1.0.0

## S3 API → Connector Endpoint Mapping


| S3 API Operation       | Connector Endpoint  | Method |
| ---------------------- | ------------------- | ------ |
| `ListBuckets`          | `/buckets`          | GET    |
| `CreateBucket`         | `/buckets`          | POST   |
| `DeleteBucket`         | `/buckets/{bucket}` | DELETE |
| `ListObjectsV2`        | `/objects`          | GET    |
| `PutObject`            | `/objects/upload`   | POST   |
| `GetObject`            | `/objects/download` | GET    |
| `DeleteObject`         | `/objects`          | DELETE |
| `CopyObject`           | `/objects/copy`     | POST   |
| `GeneratePresignedUrl` | `/objects/presign`  | POST   |


## Field Mapping

### Object Upload


| Connector Field  | S3 API Parameter | Notes                        |
| ---------------- | ---------------- | ---------------------------- |
| `bucket`         | `Bucket`         | Target bucket name           |
| `key`            | `Key`            | Object key / path            |
| `content_base64` | `Body`           | Base64-decoded before upload |
| `content_type`   | `ContentType`    | MIME type                    |


### Object List


| Connector Field | S3 API Parameter | Notes             |
| --------------- | ---------------- | ----------------- |
| `bucket`        | `Bucket`         | Bucket to list    |
| `prefix`        | `Prefix`         | Key prefix filter |
| `max_keys`      | `MaxKeys`        | Default: 1000     |


### Object Response


| Connector Field | S3 API Field   | Notes                   |
| --------------- | -------------- | ----------------------- |
| `key`           | `Key`          | Object key              |
| `bucket`        | —              | Set by connector        |
| `size`          | `Size`         | Bytes                   |
| `last_modified` | `LastModified` | ISO 8601 datetime       |
| `etag`          | `ETag`         | Stripped of quotes      |
| `storage_class` | `StorageClass` | e.g., STANDARD, GLACIER |


### Pre-signed URL


| Connector Field | S3 API Parameter | Notes                                  |
| --------------- | ---------------- | -------------------------------------- |
| `bucket`        | `Bucket`         |                                        |
| `key`           | `Key`            |                                        |
| `expires_in`    | `ExpiresIn`      | Seconds (default: 3600)                |
| `method`        | Client method    | GET → `get_object`, PUT → `put_object` |


## Status Code Mapping


| S3 Error Code         | HTTP Status | Connector Behavior    |
| --------------------- | ----------- | --------------------- |
| `NoSuchBucket`        | 404         | Forward as error      |
| `NoSuchKey`           | 404         | Forward as error      |
| `AccessDenied`        | 403         | Forward as error      |
| `BucketAlreadyExists` | 409         | Forward as error      |
| `InvalidBucketName`   | 400         | Validated client-side |
| `RequestTimeout`      | 408         | Retry with backoff    |
| `SlowDown`            | 503         | Retry with backoff    |



# Changelog

## [1.0.0] - 2026-03-10
### Added
- Initial release of Amazon S3 connector
- Object operations: upload, download, list, delete, copy
- Bucket management: list, create, delete
- Pre-signed URL generation (GET/PUT)
- Background polling for new objects (Kafka + platform events)
- Multi-account support (AWS, MinIO, Wasabi, DigitalOcean Spaces, etc.)
- S3-compatible storage support via custom endpoint_url and path-style addressing
- Input validation for bucket names and object keys
- Connection testing endpoint
- SQLite state store for polling state persistence
- Prometheus metrics
- Account management via REST API and YAML configuration

# Changelog

## [1.0.0] - 2026-02-22

### Added
- Initial release of SkanujFakture integrator
- Document upload with OCR (PDF, JPG, PNG) — endpoints v1, v2, v3
- Document listing with filters (status, sale/purchase, contractor, IDs)
- Simplified document listing endpoint
- Document update and bulk edit
- Document deletion with filters
- Original file and image download
- Document attribute management (edit, delete, with status change)
- Dictionary management (COST_TYPE, COST_CENTER, ATTRIBUTE)
- KSeF integration — XML retrieval, QR code, FA3 invoice submission
- Company and entity listing
- Multi-account support via YAML or environment variables
- Background polling for new scanned documents
- Kafka event publishing for new documents
- Health check and Prometheus metrics
- Basic Authentication support
- Comprehensive unit tests for API, client, and account manager

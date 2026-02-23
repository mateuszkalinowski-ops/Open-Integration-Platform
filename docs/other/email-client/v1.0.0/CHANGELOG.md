# Changelog

## [1.0.0] - 2026-02-22
### Added
- IMAP email receiving with configurable polling interval
- SMTP email sending with HTML, attachments, and priority support
- Multi-account management via YAML config or environment variables
- IMAP folder listing
- Mark as read and delete email operations
- Background poller for automatic email retrieval
- Kafka event publishing (email.received, email.sent)
- Prometheus metrics for IMAP/SMTP operations
- Health and readiness endpoints
- SQLite state persistence for poller timestamps
- FastAPI auto-generated Swagger UI documentation

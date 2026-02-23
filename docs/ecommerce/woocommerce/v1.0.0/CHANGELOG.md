# Changelog

## [1.0.0] - 2026-02-23
### Added
- Initial WooCommerce REST API v3 integration
- Order fetching with pagination and date filtering (`modified_after`)
- Single order retrieval by ID
- Order status updates (bidirectional status mapping)
- Stock level synchronization by product ID or SKU lookup
- Product retrieval and sync (create/update)
- Multi-account support (multiple WooCommerce stores per instance)
- API key authentication (Basic Auth for HTTPS, OAuth 1.0a HMAC-SHA256 for HTTP)
- Background order scraper with configurable interval
- Kafka integration for event publishing (optional)
- SQLite state persistence for scraper checkpoints
- Prometheus metrics for API call monitoring
- Health and readiness endpoints
- Swagger UI documentation at `/docs`
- Docker multi-stage build with non-root user
- Docker Compose for development, testing, and production

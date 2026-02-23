# Changelog

## [1.0.0] - 2026-02-22

### Added
- Initial implementation of the Shoper connector for the Pinquark platform
- Basic Auth → Bearer token authentication with automatic refresh
- Order scraping with status_date filters and bulk order product fetching
- Product scraping with add_date filters
- User scraping (active users only) with date_add filters
- REST API: fetching orders, products, updating statuses
- Parcel management (creation, update)
- Stock level synchronization
- Pagination and filtering via Shoper API
- Bulk API for efficient data retrieval
- Multi-account Shoper support (configuration via YAML or env vars)
- Kafka publishing (orders, products, users)
- Scraper state persistence in SQLite
- Health/readiness endpoints
- Prometheus metrics
- Dockerfile with multi-stage build, non-root user, healthcheck
- Unit tests: auth, mapper, API routes

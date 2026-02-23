# Changelog

## [1.0.0] - 2026-02-22

### Added
- Initial IdoSell integrator for Open Integration Platform by Pinquark.com
- Order management: fetch, search, get, update status
- Product retrieval and sync
- Stock quantity synchronization via `PUT /products/stockQuantity`
- Parcel creation with tracking numbers
- Multi-account support (YAML config or environment variables)
- Background order scraper with configurable polling interval
- Kafka integration for publishing orders and products
- X-API-KEY authentication for IdoSell Admin API v6/v7
- Comprehensive status mapping (24 IdoSell statuses → 7 unified statuses)
- Rate limit handling with retry logic
- Health and readiness endpoints
- Prometheus metrics

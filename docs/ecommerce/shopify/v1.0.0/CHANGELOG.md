# Changelog

## [1.0.0] - 2026-02-22

### Added
- Initial Shopify integration (Admin REST API 2024-07)
- Order synchronization: fetch, get, status updates, fulfillment creation
- Product management: get, create, update, sync
- Inventory level sync via Inventory API
- Background order scraper with configurable polling interval
- Multi-account support (multiple Shopify stores)
- Kafka publishing for scraped orders
- Prometheus metrics and structured JSON logging
- Rate limit handling with automatic retry (X-Shopify-Shop-Api-Call-Limit)
- Health and readiness endpoints
- Access token validation
- Encrypted token persistence (AES-256-GCM)
- Docker container with multi-stage build
- Comprehensive test suite (mapper, API, client)

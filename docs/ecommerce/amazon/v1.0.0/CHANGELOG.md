# Changelog

## [1.0.0] - 2026-02-24

### Added
- Initial Amazon SP-API integration
- LWA OAuth2 authentication with automatic token refresh
- Orders API: fetch orders, get order details, get order items
- Order status management via Feeds API (acknowledge, ship, cancel)
- Catalog Items API: search products, get product by ASIN
- Stock synchronization via POST_INVENTORY_AVAILABILITY_DATA feed
- Reports API: create and retrieve reports
- Feed status tracking
- Background scraper for automatic order polling
- Multi-account support with YAML/env configuration
- Kafka publishing for scraped orders
- SQLite state persistence for scraper
- Prometheus metrics for all external API calls
- Health and readiness endpoints
- Docker and Docker Compose configuration
- Unit tests for mapper, auth, and API routes

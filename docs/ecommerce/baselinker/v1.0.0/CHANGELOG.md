# Changelog

## [1.0.0] - 2026-02-22

### Added
- Initial BaseLinker integrator release
- Order management: fetch, get, update status
- Product catalog: read product data from inventories
- Stock synchronization: bulk update via updateInventoryProductsStock
- Parcel registration via createPackageManual
- Background scraper using getJournalList for change detection
- Multi-account support via YAML or environment variables
- Kafka integration for order and product events
- Keyword-based order status mapping for custom BaseLinker statuses
- Rate limit handling (100 req/min)
- Retry with exponential backoff for transient failures

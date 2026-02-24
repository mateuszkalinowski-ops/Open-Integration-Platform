# Changelog

## [1.0.0] - 2026-02-24

### Added
- Initial release of Apilo e-commerce connector
- OAuth2 authentication with automatic token refresh (access tokens valid 21 days)
- Order management: list, get, create, update status, add payments, notes, tags, shipments
- Product catalog: list, get, create, update (full and patch), delete
- Shipment management: create via Shipping API, track, confirm pickup
- Finance document listing
- Background order scraper with configurable polling interval
- Multi-account support via YAML or environment variables
- Prometheus metrics and structured logging
- Rate limiting compliance (150 req/min)
- Full field mapping between Apilo and Pinquark unified schemas
- Reference map endpoints (statuses, payment types, carriers, platforms, tags)

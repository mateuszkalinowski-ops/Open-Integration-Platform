# Changelog

## [1.0.0] - 2026-02-20

### Added
- Initial Allegro integrator release
- Multi-account support via `accounts.yaml` or environment variables
- OAuth2 device flow authentication with encrypted token storage (AES-256-GCM)
- Order event scraping with configurable interval and event deduplication
- Order fetching (list and single order) via Allegro Checkout Forms API
- Bidirectional order status synchronization (WMS ↔ Allegro fulfillment)
- Stock level synchronization to Allegro offers
- Product/offer detail fetching with EAN extraction
- Optional Kafka message publishing for WMS integration
- Prometheus metrics endpoint (`/metrics`)
- Health and readiness endpoints
- Runtime account management via REST API (add/remove accounts)
- Structured JSON logging with PII redaction
- Docker support with multi-stage build, non-root user
- Unit tests for mapper, auth, and API routes

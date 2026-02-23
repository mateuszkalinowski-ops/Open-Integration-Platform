# Changelog

## [1.0.0] - 2026-02-22

### Added
- Initial Raben Group courier integrator
- Transport order creation via myOrder (LTL/FTL freight)
- Shipment tracking with full event history (Track & Trace)
- ETA (Estimated Time of Arrival) support with +/- 2h window
- Photo Confirming Delivery (PCD) retrieval
- Shipping label generation (PDF/ZPL)
- Complaint/claim submission via myClaim (damage, loss, delay, other)
- Service types: Cargo Classic, Cargo Premium, Premium 08/10/12/16
- JWT-based authentication with automatic token refresh
- Status mapping for 17 Raben statuses to 9 unified statuses
- Additional services: tail lift, email notifications, COD
- Docker support with multi-stage build
- Health and readiness endpoints
- Unit tests for all endpoints, schemas, and business logic

# Changelog

## [1.0.0] - 2026-02-24

### Added
- Initial FX Couriers (KurierSystem) connector implementation
- Transport order creation (POST /order)
- Order listing with pagination and date filtering (GET /orders)
- Single order retrieval (GET /order/{order_id})
- Order deletion (DELETE /order/{order_id})
- Order tracking (GET /order-tracking/{order_id})
- Shipping label PDF generation (GET /label/{order_id})
- Pickup scheduling (POST /shipments)
- Pickup cancellation (DELETE /shipment/{order_id})
- Available services listing (GET /services)
- Company info retrieval (GET /company/{company_id})
- Bearer token authentication
- Status mapping to platform-standard statuses
- Full test suite with mocked API calls

# Changelog

## [1.0.0] - 2026-02-25
### Added
- On-premise agent with pythonnet bridge to InsERT Nexo SDK (Sfera API)
- Full CRUD for contractors (Podmioty) with NIP search
- Full CRUD for products (Asortyment) with EAN search
- Sales document creation (Invoice, Receipt, Proforma)
- Warehouse document creation (WZ — issue, PZ — receipt)
- Order management (from customers and to suppliers)
- Stock level queries (by warehouse, by product)
- Heartbeat service with periodic status reporting to cloud
- Bidirectional sync engine with offline queue (SQLite)
- Cloud connector (proxy) for platform integration
- Docker Windows container deployment
- Swagger UI documentation at `/docs`
- Health and readiness endpoints

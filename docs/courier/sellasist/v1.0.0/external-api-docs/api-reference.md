# SellAsist — API Reference

Source: https://api.sellasist.pl/

## Base URL
```
https://{account}.sellasist.pl/api/v1
```
Replace `{account}` with the SellAsist account subdomain.

## API Version
1.90.7

## Authentication
Every request requires:
- `apiKey` (header) — API key for the account

## Endpoints

### GET /ordersshipments
Lists shipments with optional filtering.
- **Headers**: apiKey
- **Query Parameters**:
  - `page` (int, optional) — Page number for pagination
  - `limit` (int, optional) — Results per page
  - `order_id` (int, optional) — Filter by order ID
  - `status` (string, optional) — Filter by shipment status
- **Response**: Array of shipment summary objects
- **Shipment Object**:
  - `id` (int) — Shipment ID
  - `order_id` (int) — Associated order ID
  - `carrier` (string) — Carrier name
  - `tracking_number` (string) — Waybill/tracking number
  - `status` (string) — Current shipment status
  - `created_at` (string) — Creation timestamp
- **Status Codes**: 200 OK, 401 Unauthorized

### GET /ordersshipments/{id}
Retrieves a single shipment with its label file.
- **Headers**: apiKey
- **Path Parameters**:
  - `id` (int) — Shipment ID
- **Response**: Shipment details including label file data
- **Shipment Detail Object**:
  - `id` (int) — Shipment ID
  - `order_id` (int) — Associated order ID
  - `carrier` (string) — Carrier name
  - `tracking_number` (string) — Waybill/tracking number
  - `status` (string) — Current shipment status
  - `label_file` (string) — Base64-encoded PDF label
  - `label_format` (string) — Label format (typically PDF)
  - `created_at` (string) — Creation timestamp
- **Status Codes**: 200 OK, 404 Not Found, 401 Unauthorized

## PDF Label Merging
When retrieving labels for multiple shipments (batch printing), the integrator should:
1. Fetch individual labels via `GET /ordersshipments/{id}` for each shipment
2. Decode base64 label data to PDF
3. Merge multiple PDFs into a single document for batch printing

No native batch label endpoint exists — merging is handled client-side.

## Important Notes
- This API is **read-only** for shipment data — no endpoints for creating or modifying shipments
- Shipments are created through the SellAsist platform UI or via other connected integrations
- The integrator's primary purpose is label retrieval for WMS printing workflows

## Error Handling
Errors returned as JSON:
- `401` — Invalid or missing API key
- `404` — Shipment not found
- `429` — Rate limit exceeded (if applicable)
- `500` — Internal server error

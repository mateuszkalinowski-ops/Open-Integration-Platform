# Known Issues — Shopify Integrator v1.0.0

## Limitations

### 1. Single variant product mapping
When mapping products between pinquark and Shopify, only the first variant is used for SKU, EAN (barcode), and price. Multi-variant products are partially supported — all variants are preserved in raw data but the unified Product schema maps only the primary variant.

**Workaround**: Use the raw Shopify API response in `Product.attributes` for variant details.

### 2. Inventory sync requires inventory_item_id
The `StockItem.product_id` field must contain the Shopify `inventory_item_id` (not the product ID or variant ID). The inventory_item_id can be found in the product variant data: `variant.inventory_item_id`.

### 3. Fulfillment Orders API
The connector uses the Fulfillment Orders API (2023-01+) for creating fulfillments. Older Shopify API versions with the legacy Fulfillment API are not supported.

### 4. Order scraper pagination
The order scraper uses `since_id` for incremental fetching (max 250 per request). If more than 250 orders are created between polling intervals, some may be delayed to the next poll cycle.

### 5. No webhook support (yet)
This version uses polling for order synchronization. Webhook support (for real-time order notifications) is planned for v1.1.0.

### 6. GraphQL API not used
The Java reference implementation used both REST and GraphQL APIs. This Python implementation uses only the REST API. GraphQL support (for bulk operations and advanced product management) is planned for v1.1.0.

## Known Shopify API Quirks

- **Rate limits**: 40 requests/second with a bucket of 80. The connector handles 429 responses automatically.
- **Access token rotation**: Shopify custom app access tokens do not expire and cannot be rotated without reinstalling the app.
- **Decimal precision**: Shopify prices are strings (e.g., "49.99"). The connector converts to float, which may introduce precision issues for currencies with more than 2 decimal places.

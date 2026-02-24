# Known Issues & Limitations — Amazon Integrator v1.0.0

## 1. No Direct Status Update API

Amazon does not provide a direct "set order status" API endpoint. Status changes are performed via Feeds API submissions, which are asynchronous:

- **Acknowledge order**: Submit `POST_ORDER_ACKNOWLEDGEMENT_DATA` feed
- **Confirm shipment**: Submit `POST_ORDER_FULFILLMENT_DATA` feed
- **Cancel order**: Submit acknowledgement with `Failure` status code

Feed processing takes 5-30 minutes. Use `GET /feeds/{feed_id}` to track progress.

## 2. Restricted Data (PII)

Buyer PII (email, name, address) requires:
- Approved **restricted data** role in Seller Central
- Submitted **Data Protection Plan** (DPP)
- Restricted Data Token (RDT) for each request

Without restricted access, `BuyerInfo` and `ShippingAddress` fields may be empty or masked.

## 3. Rate Limiting

SP-API has strict rate limits, especially for `getOrders` (0.0167 req/s = ~1 request per minute sustained). The integrator handles 429 responses with automatic retry, but high-volume polling may require longer intervals.

## 4. Feed Processing Delay

Feeds submitted via the Feeds API are queued and processed asynchronously. Typical processing time: 5-30 minutes. The same feed type cannot be submitted more frequently than every 20 minutes.

## 5. Catalog API Limitations

- `searchCatalogItems` by keywords is limited to 50 req/s application-wide
- Maximum 20 results per page, 1000 results total
- Product data completeness varies by marketplace

## 6. Sandbox Limitations

- Only predefined test scenarios work in sandbox
- Not all API operations have sandbox support
- Feed processing in sandbox may behave differently than production

## 7. Multi-Marketplace Orders

Orders from different marketplaces within the same region share the same API endpoint but require the correct `MarketplaceId` parameter. The integrator uses the configured `marketplace_id` per account.

## 8. FBA vs MFN Orders

- **MFN** (Merchant Fulfilled Network): Full control over shipment confirmation
- **AFN/FBA** (Fulfilled by Amazon): Shipments are managed by Amazon; status updates are read-only

The integrator handles both fulfillment channels but shipment confirmation only applies to MFN orders.

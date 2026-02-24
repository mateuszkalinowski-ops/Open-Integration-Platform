# Amazon Selling Partner API (SP-API) — Reference

## Authentication

**Login with Amazon (LWA) OAuth2**

Token endpoint: `POST https://api.amazon.com/auth/o2/token`

### Refresh Token Grant
```
grant_type=refresh_token
refresh_token=Atzr|XXXX
client_id=amzn1.application-oa2-client.xxxx
client_secret=your-secret
```

### Client Credentials Grant (Grantless)
```
grant_type=client_credentials
client_id=amzn1.application-oa2-client.xxxx
client_secret=your-secret
scope=sellingpartnerapi::notifications
```

Access tokens expire after 1 hour. Pass in `x-amz-access-token` header.

## Regional Endpoints

| Region | Base URL |
|---|---|
| North America | https://sellingpartnerapi-na.amazon.com |
| Europe | https://sellingpartnerapi-eu.amazon.com |
| Far East | https://sellingpartnerapi-fe.amazon.com |

## Orders API (v0)

| Operation | Method | Path | Rate/Burst |
|---|---|---|---|
| getOrders | GET | /orders/v0/orders | 0.0167/s / 20 |
| getOrder | GET | /orders/v0/orders/{orderId} | 0.5/s / 30 |
| getOrderItems | GET | /orders/v0/orders/{orderId}/orderItems | 0.5/s / 30 |
| getOrderAddress | GET | /orders/v0/orders/{orderId}/address | 0.5/s / 30 (restricted) |
| getOrderBuyerInfo | GET | /orders/v0/orders/{orderId}/buyerInfo | 0.5/s / 30 (restricted) |

### getOrders Parameters
- `MarketplaceIds` (required)
- `CreatedAfter` / `CreatedBefore`
- `LastUpdatedAfter` / `LastUpdatedBefore`
- `OrderStatuses`: Pending, Unshipped, PartiallyShipped, Shipped, Canceled, Unfulfillable
- `FulfillmentChannels`: MFN, AFN
- `MaxResultsPerPage` (max 100)
- `NextToken` (pagination)

## Catalog Items API (2022-04-01)

| Operation | Method | Path | Rate |
|---|---|---|---|
| searchCatalogItems | GET | /catalog/2022-04-01/items | 2/s |
| getCatalogItem | GET | /catalog/2022-04-01/items/{asin} | 2/s |

### searchCatalogItems Parameters
- `marketplaceIds` (required)
- `keywords` / `identifiers` + `identifiersType`
- `includedData`: summaries, attributes, dimensions, identifiers, images, productTypes, salesRanks
- `pageSize` (max 20)

## Feeds API (2021-06-30)

| Operation | Method | Path | Rate/Burst |
|---|---|---|---|
| createFeedDocument | POST | /feeds/2021-06-30/documents | 0.5/s / 15 |
| createFeed | POST | /feeds/2021-06-30/feeds | 0.0083/s / 15 |
| getFeed | GET | /feeds/2021-06-30/feeds/{feedId} | 2/s / 15 |
| getFeedDocument | GET | /feeds/2021-06-30/documents/{feedDocumentId} | 0.0083/s / 15 |

### Feed Workflow
1. createFeedDocument → get feedDocumentId + pre-signed URL
2. PUT feed content to pre-signed URL
3. createFeed with feedType + inputFeedDocumentId
4. Poll getFeed until processingStatus = DONE

### Key Feed Types
- POST_ORDER_ACKNOWLEDGEMENT_DATA
- POST_ORDER_FULFILLMENT_DATA
- POST_INVENTORY_AVAILABILITY_DATA
- POST_PAYMENT_ADJUSTMENT_DATA

## Reports API (2021-06-30)

| Operation | Method | Path |
|---|---|---|
| createReport | POST | /reports/2021-06-30/reports |
| getReport | GET | /reports/2021-06-30/reports/{reportId} |
| getReportDocument | GET | /reports/2021-06-30/documents/{reportDocumentId} |

### Report Workflow
1. createReport → get reportId
2. Poll getReport until processingStatus = DONE
3. getReportDocument → get pre-signed download URL

## Error Response Format
```json
{
  "errors": [
    {
      "code": "InvalidInput",
      "message": "Description of the error",
      "details": ""
    }
  ]
}
```

HTTP status codes: 400 (validation), 401 (auth), 403 (forbidden), 404 (not found), 429 (throttled), 500 (server error).

# IdoSell Admin REST API — Reference Summary

> Source: https://idosell.readme.io/reference, https://www.idosell.com/en/developers/

## Base URL

```
https://{shop_domain}/api/admin/{version}/
```

Where `{shop_domain}` is the panel address (e.g. `client12345.idosell.com`) and `{version}` is `v6` or `v7`.

OpenAPI spec: `https://{shop_domain}/api/doc/admin/{version}/json`

---

## Orders (OMS Module)

### Search Orders
```
POST /orders/orders/search
```

Request body:
```json
{
  "params": {
    "resultsPage": 0,
    "resultsLimit": 100,
    "ordersRange": {
      "ordersDateRange": {
        "ordersDateType": "modified",
        "ordersDateBegin": "2026-01-01 00:00:00",
        "ordersDateEnd": "2026-02-22 23:59:59"
      }
    }
  }
}
```

Response:
```json
{
  "resultsNumberAll": 250,
  "resultsNumberPage": 3,
  "resultsPage": 0,
  "resultsLimit": 100,
  "errors": { "faultCode": 0, "faultString": "" },
  "results": [
    {
      "orderId": "ORD-001",
      "orderSerialNumber": 12345,
      "orderType": "retail",
      "order": {
        "stockId": 1,
        "orderNote": "...",
        "orderStatus": { "orderStatus": "new" },
        "dispatch": { "courierId": 1, "courierName": "InPost" },
        "payments": {
          "orderPaymentType": "prepaid",
          "orderBaseCurrency": {
            "billingCurrency": "PLN",
            "orderProductsCost": 99.99,
            "orderDeliveryCost": 12.50
          }
        },
        "productsResults": [
          {
            "productId": 100,
            "productName": "Koszulka Polo",
            "productCode": "POLO-001",
            "productQuantity": 2.0,
            "productOrderPrice": 49.99
          }
        ],
        "orderAddDate": "2026-02-20 10:00:00",
        "orderChangeDate": "2026-02-21 14:30:00"
      },
      "client": {
        "clientAccount": { "clientId": 500, "clientEmail": "jan@example.com" },
        "clientBillingAddress": { "clientFirstName": "Jan", "clientLastName": "Kowalski", "..." },
        "clientDeliveryAddress": { "..." }
      }
    }
  ]
}
```

### Get Orders by ID
```
GET /orders/orders?ordersSerialNumbers=12345,12346
GET /orders/orders?ordersIds=ORD-001,ORD-002
```

Max 100 IDs per request.

### Update Order
```
PUT /orders/orders
```

```json
{
  "params": {
    "orders": [
      {
        "orderSerialNumber": 12345,
        "orderStatus": "packed"
      }
    ]
  }
}
```

### Create Packages
```
POST /orders/packages
```

```json
{
  "params": {
    "orderPackages": [
      {
        "eventType": "order",
        "eventId": "12345",
        "packages": [
          {
            "deliveryPackageNumber": "TRACK001",
            "courierId": 1
          }
        ]
      }
    ]
  }
}
```

---

## Products (PIM Module)

### Search Products
```
POST /products/products/search
```

```json
{
  "params": {
    "resultsPage": 0,
    "resultsLimit": 100,
    "productDate": {
      "productDateType": "modification",
      "productDateBegin": "2026-01-01 00:00:00"
    }
  }
}
```

### Get Products
```
GET /products/products?productsIds=100,101,102
```

### Edit Products
```
PUT /products/products
```

```json
{
  "settings": { "settingModificationType": "edit" },
  "products": [
    { "productId": 100, "productDisplayedCode": "NEW-CODE" }
  ]
}
```

---

## Stock / Inventory

### Get Stock Levels
```
GET /products/stocks?identType=product_id&products=100,101
```

### Update Stock Quantity
```
PUT /products/stockQuantity
```

```json
{
  "params": {
    "products": [
      {
        "productIndex": "POLO-001",
        "productSizeCodeExternal": "",
        "stockId": 1,
        "productSizeQuantity": 150.0
      }
    ]
  }
}
```

---

## Order Statuses

| Status | Description |
|---|---|
| `new` | New order |
| `payment_waiting` | Waiting for payment |
| `delivery_waiting` | Waiting for delivery |
| `on_order` | On order (back-order) |
| `packed` | Packed |
| `packed_fulfillment` | Packed (fulfillment) |
| `packed_ready` | Packed and ready |
| `ready` | Ready for dispatch |
| `wait_for_dispatch` | Waiting for dispatch |
| `wait_for_packaging` | Waiting for packaging |
| `handled` | Handled / shipped |
| `wait_for_receive` | Waiting for customer receipt |
| `finished` | Completed |
| `finished_ext` | Completed (external) |
| `returned` | Returned |
| `complainted` | Complained |
| `canceled` | Cancelled |
| `all_canceled` | All items cancelled |
| `false` | False order |
| `lost` | Lost |
| `missing` | Missing |
| `suspended` | Suspended |
| `blocked` | Blocked |
| `joined` | Merged with another order |

---

## Date Format

All dates use the format: `YYYY-MM-DD HH:MM:SS` (space-separated, not ISO 8601).

## Batch Limits

Max 100 items per batch request (order serial numbers, product IDs, etc.).

## Pagination

- `resultsPage` — 0-based page index
- `resultsLimit` — items per page (max 100)
- `resultsNumberAll` — total number of results
- `resultsNumberPage` — total number of pages

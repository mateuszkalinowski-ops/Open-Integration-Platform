# Shopify Admin REST API 2024-07 — Reference

Source: https://shopify.dev/docs/api/admin-rest/2024-07

> **Note**: The REST Admin API is a legacy API as of October 1, 2024. Starting April 1, 2025,
> all new public apps must use the GraphQL Admin API. Custom apps (used by this connector) can
> still use REST API.

## Authentication

All requests require the `X-Shopify-Access-Token` header with a valid Admin API access token.

```
X-Shopify-Access-Token: shpat_xxxxx
Content-Type: application/json
```

Access tokens are created by installing a Custom App in the Shopify Admin.

Required scopes for this connector:
- `read_orders`, `write_orders`
- `read_products`, `write_products`
- `read_inventory`, `write_inventory`
- `read_fulfillments`, `write_fulfillments`
- `read_customers`
- `read_locations`

Source: https://shopify.dev/docs/api/usage/authentication

---

## Base URL

```
https://{shop}.myshopify.com/admin/api/{api_version}/
```

Example: `https://my-store.myshopify.com/admin/api/2024-07/`

---

## Orders API

### List Orders
```
GET /admin/api/2024-07/orders.json
```

Query parameters:
| Parameter | Type | Description |
|---|---|---|
| `status` | string | `open`, `closed`, `cancelled`, `any` (default: `open`) |
| `limit` | integer | Max results per page (1-250, default: 50) |
| `since_id` | string | Results after this ID |
| `updated_at_min` | string | ISO 8601 datetime filter |
| `updated_at_max` | string | ISO 8601 datetime filter |
| `created_at_min` | string | ISO 8601 datetime filter |
| `created_at_max` | string | ISO 8601 datetime filter |
| `fields` | string | Comma-separated list of fields to return |
| `financial_status` | string | `authorized`, `pending`, `paid`, `partially_paid`, `refunded`, `voided`, `partially_refunded`, `any`, `unpaid` |
| `fulfillment_status` | string | `shipped`, `partial`, `unshipped`, `any`, `unfulfilled` |

**Note**: Only the last 60 days of orders are accessible by default. Requires `read_all_orders` scope for older orders.

Response:
```json
{
  "orders": [
    {
      "id": 450789469,
      "name": "#1001",
      "order_number": 1001,
      "email": "bob@example.com",
      "financial_status": "paid",
      "fulfillment_status": null,
      "currency": "USD",
      "total_price": "199.99",
      "subtotal_price": "179.99",
      "total_tax": "20.00",
      "total_discounts": "0.00",
      "customer": { ... },
      "billing_address": { ... },
      "shipping_address": { ... },
      "line_items": [ ... ],
      "fulfillments": [ ... ],
      "shipping_lines": [ ... ],
      "note": "...",
      "tags": "...",
      "created_at": "2024-01-01T00:00:00-05:00",
      "updated_at": "2024-01-02T00:00:00-05:00"
    }
  ]
}
```

### Get Order
```
GET /admin/api/2024-07/orders/{order_id}.json
```

### Close Order
```
POST /admin/api/2024-07/orders/{order_id}/close.json
```

### Open Order (re-open)
```
POST /admin/api/2024-07/orders/{order_id}/open.json
```

### Cancel Order
```
POST /admin/api/2024-07/orders/{order_id}/cancel.json
```

Body (optional):
```json
{
  "reason": "customer",
  "email": true,
  "restock": true
}
```

Cancel reasons: `customer`, `fraud`, `inventory`, `declined`, `other`

### Order Properties

| Property | Type | Description |
|---|---|---|
| `id` | integer | Unique ID |
| `name` | string | Order name (e.g. "#1001") |
| `order_number` | integer | Sequential order number |
| `email` | string | Customer email |
| `phone` | string | Customer phone |
| `financial_status` | string | `pending`, `authorized`, `partially_paid`, `paid`, `partially_refunded`, `refunded`, `voided` |
| `fulfillment_status` | string | `fulfilled`, `partial`, `unfulfilled`, `restocked`, `null` |
| `cancel_reason` | string | `customer`, `fraud`, `inventory`, `declined`, `other` |
| `cancelled_at` | string | ISO 8601, null if not cancelled |
| `closed_at` | string | ISO 8601, null if not closed |
| `currency` | string | Three-letter ISO 4217 code |
| `total_price` | string | Total price including tax and shipping |
| `subtotal_price` | string | Price before shipping and tax |
| `total_tax` | string | Total tax |
| `total_discounts` | string | Total discounts |
| `customer` | object | Customer who placed the order |
| `billing_address` | object | Billing address |
| `shipping_address` | object | Shipping address |
| `line_items` | array | List of line items |
| `fulfillments` | array | List of fulfillments |
| `shipping_lines` | array | Shipping methods |
| `note` | string | Order notes |
| `note_attributes` | array | Additional attributes |
| `tags` | string | Comma-separated tags |
| `created_at` | string | ISO 8601 creation date |
| `updated_at` | string | ISO 8601 last update date |

---

## Products API

### List Products
```
GET /admin/api/2024-07/products.json
```

Query parameters:
| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Max results (1-250, default: 50) |
| `since_id` | string | Results after this ID |
| `title` | string | Filter by title |
| `vendor` | string | Filter by vendor |
| `product_type` | string | Filter by type |
| `status` | string | `active`, `archived`, `draft` |
| `fields` | string | Fields to return |

### Get Product
```
GET /admin/api/2024-07/products/{product_id}.json
```

### Create Product
```
POST /admin/api/2024-07/products.json
```

Body:
```json
{
  "product": {
    "title": "Burton Custom Freestyle",
    "body_html": "<strong>Good snowboard!</strong>",
    "vendor": "Burton",
    "product_type": "Snowboard",
    "tags": "Barnes & Noble, Big Icons",
    "variants": [
      {
        "sku": "BOARD-001",
        "barcode": "1234567890123",
        "price": "10.00",
        "weight": 1.5,
        "weight_unit": "kg",
        "inventory_management": "shopify"
      }
    ]
  }
}
```

### Update Product
```
PUT /admin/api/2024-07/products/{product_id}.json
```

### Product Properties

| Property | Type | Description |
|---|---|---|
| `id` | integer | Unique ID |
| `title` | string | Product name |
| `body_html` | string | HTML description |
| `vendor` | string | Vendor name |
| `product_type` | string | Product type/category |
| `handle` | string | URL-friendly name |
| `status` | string | `active`, `archived`, `draft` |
| `tags` | string | Comma-separated tags |
| `variants` | array | Product variants |
| `images` | array | Product images |
| `created_at` | string | ISO 8601 |
| `updated_at` | string | ISO 8601 |

### Variant Properties

| Property | Type | Description |
|---|---|---|
| `id` | integer | Variant ID |
| `product_id` | integer | Parent product ID |
| `title` | string | Variant title |
| `sku` | string | Stock Keeping Unit |
| `barcode` | string | Barcode (EAN/UPC/GTIN) |
| `price` | string | Price |
| `compare_at_price` | string | Original price (for sales) |
| `weight` | float | Weight |
| `weight_unit` | string | `g`, `kg`, `oz`, `lb` |
| `inventory_item_id` | integer | Inventory item ID |
| `inventory_quantity` | integer | Current stock |
| `inventory_management` | string | `shopify` or null |
| `option1..3` | string | Variant options |

---

## Fulfillments API

### Create Fulfillment (Fulfillment Orders API, 2023-01+)
```
POST /admin/api/2024-07/fulfillments.json
```

Body:
```json
{
  "fulfillment": {
    "line_items_by_fulfillment_order": [
      {
        "fulfillment_order_id": 1046000778
      }
    ],
    "tracking_info": {
      "number": "1Z1234512345123456",
      "company": "UPS",
      "url": "https://www.ups.com/track?tracknum=1Z1234512345123456"
    },
    "notify_customer": true
  }
}
```

### Get Fulfillment Orders
```
GET /admin/api/2024-07/orders/{order_id}/fulfillment_orders.json
```

Response:
```json
{
  "fulfillment_orders": [
    {
      "id": 1046000778,
      "order_id": 450789469,
      "status": "open",
      "line_items": [
        {
          "id": 1058737482,
          "fulfillment_order_id": 1046000778,
          "quantity": 1
        }
      ]
    }
  ]
}
```

Fulfillment order statuses: `open`, `in_progress`, `cancelled`, `incomplete`, `closed`, `scheduled`, `on_hold`

### Update Tracking
```
POST /admin/api/2024-07/fulfillments/{fulfillment_id}/update_tracking.json
```

Body:
```json
{
  "fulfillment": {
    "tracking_info": {
      "number": "1Z1234512345123456",
      "company": "UPS"
    },
    "notify_customer": false
  }
}
```

### List Fulfillments for Order
```
GET /admin/api/2024-07/orders/{order_id}/fulfillments.json
```

### Fulfillment Properties

| Property | Type | Description |
|---|---|---|
| `id` | integer | Fulfillment ID |
| `order_id` | integer | Order ID |
| `status` | string | `pending`, `open`, `success`, `cancelled`, `error`, `failure` |
| `tracking_company` | string | Shipping carrier |
| `tracking_number` | string | Tracking number |
| `tracking_numbers` | array | Multiple tracking numbers |
| `tracking_url` | string | Tracking URL |
| `created_at` | string | ISO 8601 |
| `updated_at` | string | ISO 8601 |

---

## Inventory Levels API

### Set Inventory Level
```
POST /admin/api/2024-07/inventory_levels/set.json
```

Body:
```json
{
  "inventory_item_id": 808950810,
  "location_id": 905684977,
  "available": 42
}
```

**Note**: Requires `inventory_management` to be set to `"shopify"` on the variant.

---

## Customers API

### List Customers
```
GET /admin/api/2024-07/customers.json
```

Query parameters:
| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Max results (1-250) |
| `since_id` | string | Results after this ID |
| `fields` | string | Fields to return |

### Customer Properties

| Property | Type | Description |
|---|---|---|
| `id` | integer | Customer ID |
| `email` | string | Email address |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `phone` | string | Phone number |
| `orders_count` | integer | Total orders |
| `total_spent` | string | Total lifetime spend |
| `verified_email` | boolean | Email verified |
| `default_address` | object | Default address |
| `tags` | string | Tags |
| `note` | string | Notes |

---

## Locations API

### List Locations
```
GET /admin/api/2024-07/locations.json
```

Returns all locations for the shop. The location ID is needed for inventory management.

---

## Address Object

Used in `shipping_address`, `billing_address`, `default_address`:

| Property | Type | Description |
|---|---|---|
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `company` | string | Company name |
| `address1` | string | Street address |
| `address2` | string | Apartment, suite, etc. |
| `city` | string | City |
| `province` | string | Province/state name |
| `province_code` | string | Province/state code |
| `country` | string | Country name |
| `country_code` | string | ISO 3166-1 alpha-2 country code |
| `zip` | string | Postal/zip code |
| `phone` | string | Phone number |
| `name` | string | Full name |
| `latitude` | float | Latitude |
| `longitude` | float | Longitude |

---

## Line Item Object

| Property | Type | Description |
|---|---|---|
| `id` | integer | Line item ID |
| `variant_id` | integer | Product variant ID |
| `product_id` | integer | Product ID |
| `title` | string | Product title |
| `variant_title` | string | Variant title |
| `sku` | string | SKU |
| `quantity` | integer | Quantity |
| `price` | string | Unit price |
| `total_discount` | string | Total discount |
| `fulfillable_quantity` | integer | Quantity that can be fulfilled |
| `fulfillment_status` | string | `fulfilled`, `partial`, `null` |
| `grams` | integer | Weight in grams |
| `name` | string | Full name (title + variant) |
| `vendor` | string | Vendor |
| `taxable` | boolean | Whether taxable |
| `tax_lines` | array | Tax details |
| `properties` | array | Custom properties [{name, value}] |

---

## Common HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized (invalid access token) |
| 403 | Forbidden (insufficient scopes) |
| 404 | Not Found |
| 422 | Unprocessable Entity (validation error) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

Error response format:
```json
{
  "errors": {
    "base": ["Order cannot be canceled"]
  }
}
```

Or:
```json
{
  "errors": "Not Found"
}
```

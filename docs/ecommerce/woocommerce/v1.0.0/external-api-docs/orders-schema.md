# WooCommerce REST API — Orders Schema

> Source: https://woocommerce.github.io/woocommerce-rest-api-docs/v3.html
> Fetched: 2026-02-24

## Order Properties

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Order ID (read-only) |
| `order_number` | integer | Order number (read-only) |
| `created_at` | string | UTC DateTime of creation (read-only) |
| `updated_at` | string | UTC DateTime of last update (read-only) |
| `completed_at` | string | UTC DateTime of completion (read-only) |
| `status` | string | Status: `pending`, `processing`, `on-hold`, `completed`, `cancelled`, `refunded`, `failed` |
| `currency` | string | Currency ISO code (e.g. `USD`, `PLN`) |
| `total` | string | Order total (read-only) |
| `subtotal` | string | Order subtotal (read-only) |
| `total_line_items_quantity` | integer | Total item count (read-only) |
| `total_tax` | string | Tax total (read-only) |
| `total_shipping` | string | Shipping total (read-only) |
| `cart_tax` | string | Cart tax (read-only) |
| `shipping_tax` | string | Shipping tax (read-only) |
| `total_discount` | string | Discount total (read-only) |
| `shipping_methods` | string | Shipping methods text (read-only) |
| `payment_details` | array | Payment details |
| `billing_address` | array | Billing address |
| `shipping_address` | array | Shipping address |
| `note` | string | Customer order notes |
| `customer_ip` | string | Customer IP (read-only) |
| `customer_user_agent` | string | Customer User-Agent (read-only) |
| `customer_id` | integer | Customer user ID (required) |
| `view_order_url` | string | Frontend order URL (read-only) |
| `line_items` | array | Order line items |
| `shipping_lines` | array | Shipping line items |
| `tax_lines` | array | Tax line items (read-only) |
| `fee_lines` | array | Fee line items |
| `coupon_lines` | array | Coupon line items |
| `customer` | array | Customer data |

### Payment Details

| Attribute | Type | Description |
|-----------|------|-------------|
| `method_id` | string | Payment method ID (required) |
| `method_title` | string | Payment method title (required) |
| `paid` | boolean | Whether order is paid |
| `transaction_id` | string | Transaction ID |

### Line Items

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Line item ID (read-only) |
| `subtotal` | string | Item subtotal |
| `subtotal_tax` | string | Item subtotal tax |
| `total` | string | Item total |
| `total_tax` | string | Item total tax |
| `price` | string | Product price (read-only) |
| `quantity` | integer | Quantity |
| `tax_class` | string | Tax class (read-only) |
| `name` | string | Product name (read-only) |
| `product_id` | integer | Product ID (required) |
| `sku` | string | Product SKU (read-only) |
| `meta` | array | Product meta items |
| `variations` | array | Variation attributes (write-only) |

### Shipping Lines

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | ID (read-only) |
| `method_id` | string | Shipping method ID (required) |
| `method_title` | string | Shipping method title (required) |
| `total` | string | Total amount |

### Tax Lines

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Tax rate line ID (read-only) |
| `rate_id` | integer | Tax rate ID (read-only) |
| `code` | string | Tax rate code (read-only) |
| `title` | string | Tax rate title (read-only) |
| `total` | string | Tax total (read-only) |
| `compound` | boolean | Is compound rate (read-only) |

### Fee Lines

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Fee line ID (read-only) |
| `title` | string | Fee title (required) |
| `taxable` | boolean | Is fee taxable (write-only) |
| `tax_class` | string | Tax class (required if taxable) |
| `total` | string | Total amount |
| `total_tax` | string | Tax total |

### Coupon Lines

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | ID (read-only) |
| `code` | string | Coupon code (required) |
| `amount` | string | Coupon amount (required) |

### Billing Address

| Attribute | Type | Description |
|-----------|------|-------------|
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `company` | string | Company name |
| `address_1` | string | Address line 1 |
| `address_2` | string | Address line 2 |
| `city` | string | City |
| `state` | string | State/Province ISO code or name |
| `postcode` | string | Postal code |
| `country` | string | Country ISO code |
| `email` | string | Email |
| `phone` | string | Phone |

### Shipping Address

| Attribute | Type | Description |
|-----------|------|-------------|
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `company` | string | Company name |
| `address_1` | string | Address line 1 |
| `address_2` | string | Address line 2 |
| `city` | string | City |
| `state` | string | State/Province ISO code or name |
| `postcode` | string | Postal code |
| `country` | string | Country ISO code |

## Order Statuses

| Status | Description |
|--------|-------------|
| `pending` | Payment pending |
| `processing` | Payment received, order being processed |
| `on-hold` | Awaiting payment (bank transfer, cheque) |
| `completed` | Order fulfilled and completed |
| `cancelled` | Cancelled by admin or customer |
| `refunded` | Refunded by admin |
| `failed` | Payment failed or declined |
| `trash` | Trashed |

## CRUD Operations

### List Orders

```
GET /wp-json/wc/v3/orders
GET /wp-json/wc/v3/orders?status=processing&per_page=50&page=1
GET /wp-json/wc/v3/orders?modified_after=2026-01-01T00:00:00Z
```

### Get Order

```
GET /wp-json/wc/v3/orders/{id}
```

### Update Order

```
PUT /wp-json/wc/v3/orders/{id}
Content-Type: application/json

{ "status": "completed" }
```

### Sample Order Response

```json
{
  "order": {
    "id": 645,
    "order_number": 645,
    "created_at": "2015-01-26T20:00:21Z",
    "status": "processing",
    "currency": "USD",
    "total": "79.87",
    "subtotal": "63.97",
    "total_tax": "5.90",
    "total_shipping": "10.00",
    "payment_details": {
      "method_id": "bacs",
      "method_title": "Direct Bank Transfer",
      "paid": true
    },
    "billing_address": {
      "first_name": "John",
      "last_name": "Doe",
      "address_1": "969 Market",
      "city": "San Francisco",
      "state": "CA",
      "postcode": "94103",
      "country": "US",
      "email": "john.doe@example.com",
      "phone": "(555) 555-5555"
    },
    "shipping_address": {
      "first_name": "John",
      "last_name": "Doe",
      "address_1": "969 Market",
      "city": "San Francisco",
      "state": "CA",
      "postcode": "94103",
      "country": "US"
    },
    "customer_id": 2,
    "line_items": [
      {
        "id": 504,
        "price": "21.99",
        "quantity": 2,
        "name": "Premium Quality",
        "product_id": 546,
        "sku": "",
        "tax_class": "reduced-rate"
      }
    ],
    "shipping_lines": [
      {
        "id": 506,
        "method_id": "flat_rate",
        "method_title": "Flat Rate",
        "total": "10.00"
      }
    ]
  }
}
```

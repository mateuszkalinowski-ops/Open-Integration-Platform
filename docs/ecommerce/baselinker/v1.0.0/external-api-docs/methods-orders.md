# BaseLinker API — Orders Methods (Detailed)

> Source: https://api.baselinker.com/
> Fetched: 2026-02-24

---

## getOrders

Download orders from the BaseLinker order manager. Max 100 orders per call.

**Best practice:** Use `getJournalList` to collect new order IDs, or paginate via
`date_confirmed_from` (increase by 1s from last downloaded order's `date_confirmed`).

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `order_id` | int | No | Specific order ID to download |
| `date_confirmed_from` | int | No | Unix timestamp — confirmed orders from this date |
| `date_from` | int | No | Unix timestamp — orders created from this date |
| `id_from` | int | No | Order ID from which to collect subsequent orders |
| `get_unconfirmed_orders` | bool | No | Include unconfirmed orders (default: false) |
| `status_id` | int | No | Filter by status ID |
| `filter_email` | varchar(50) | No | Filter by email |
| `filter_order_source` | varchar(20) | No | Filter by source (e.g. "ebay", "amazon") |
| `filter_order_source_id` | int | No | Filter by source ID (requires `filter_order_source`) |
| `filter_shop_order_id` | int | No | Filter by shop order ID |
| `include_custom_extra_fields` | bool | No | Include custom extra field values (default: false) |
| `include_commission_data` | bool | No | Include commission info (default: false) |
| `include_connect_data` | bool | No | Include Base Connect data (default: false) |

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `orders` | array | Array of order objects |

**Order object fields:**

| Field | Type | Description |
|-------|------|-------------|
| `order_id` | int | BaseLinker order ID |
| `shop_order_id` | int | Shop order ID |
| `external_order_id` | varchar(50) | External order ID |
| `order_source` | varchar(20) | Source: "shop", "personal", "order_return", marketplace code |
| `order_source_id` | int | Source account ID |
| `order_source_info` | varchar(200) | Source description |
| `order_status_id` | int | Status ID |
| `date_add` | int | Creation date (unix) |
| `date_confirmed` | int | Confirmation date (unix) |
| `date_in_status` | int | Date entered current status (unix) |
| `confirmed` | bool | Is confirmed |
| `user_login` | varchar(100) | Allegro/eBay login |
| `currency` | char(3) | 3-letter currency code |
| `payment_method` | varchar(100) | Payment method name |
| `payment_method_cod` | varchar(1) | "1" = COD, "0" = not COD |
| `payment_done` | float | Amount paid |
| `user_comments` | varchar(1000) | Buyer comments |
| `admin_comments` | varchar(200) | Seller comments |
| `email` | varchar(150) | Buyer email |
| `phone` | varchar(100) | Buyer phone |
| `delivery_method_id` | int | Delivery method ID |
| `delivery_method` | varchar(100) | Delivery method name |
| `delivery_price` | float | Gross delivery price |
| `delivery_package_module` | varchar(20) | Courier name |
| `delivery_package_nr` | varchar(40) | Shipping number |
| `delivery_fullname` | varchar(100) | Delivery name/surname |
| `delivery_company` | varchar(100) | Delivery company |
| `delivery_address` | varchar(156) | Delivery street + number |
| `delivery_postcode` | varchar(100) | Delivery postcode |
| `delivery_city` | varchar(100) | Delivery city |
| `delivery_state` | varchar(35) | Delivery state/province |
| `delivery_country` | varchar(50) | Delivery country |
| `delivery_country_code` | char(2) | Delivery country code |
| `delivery_point_id` | varchar(40) | Pickup point ID |
| `delivery_point_name` | varchar(100) | Pickup point name |
| `delivery_point_address` | varchar(100) | Pickup point address |
| `delivery_point_postcode` | varchar(100) | Pickup point postcode |
| `delivery_point_city` | varchar(100) | Pickup point city |
| `invoice_fullname` | varchar(200) | Billing name/surname |
| `invoice_company` | varchar(200) | Billing company |
| `invoice_nip` | varchar(100) | VAT/tax number |
| `invoice_address` | varchar(250) | Billing street + number |
| `invoice_postcode` | varchar(20) | Billing postcode |
| `invoice_city` | varchar(100) | Billing city |
| `invoice_state` | varchar(35) | Billing state/province |
| `invoice_country` | varchar(50) | Billing country |
| `invoice_country_code` | char(2) | Billing country code |
| `want_invoice` | varchar(1) | "1" = wants invoice |
| `extra_field_1` | varchar(50) | Extra field 1 |
| `extra_field_2` | varchar(50) | Extra field 2 |
| `custom_extra_fields` | array | Custom extra fields (when `include_custom_extra_fields=true`) |
| `order_page` | varchar(150) | Order page URL |
| `pick_state` | int | 1 = all picked, 0 = not all |
| `pack_state` | int | 1 = all packed, 0 = not all |
| `star` | int | Star type (0-5) |
| `commission` | array | Marketplace commission (`net`, `gross`, `currency`) |
| `connect_data` | array | Base Connect data (`connect_integration_id`, `connect_contractor_id`) |

**Product fields (in `products` array):**

| Field | Type | Description |
|-------|------|-------------|
| `storage` | varchar(9) | Source type: "db", "shop", "warehouse" |
| `storage_id` | int | Storage ID |
| `order_product_id` | int | Order item ID |
| `product_id` | varchar(50) | Product ID in storage |
| `variant_id` | varchar(30) | Variant ID |
| `name` | varchar(130) | Product name |
| `sku` | varchar(50) | SKU |
| `ean` | varchar(32) | EAN |
| `location` | varchar(50) | Product location |
| `warehouse_id` | int | Source warehouse ID |
| `auction_id` | varchar(50) | Listing ID (eBay/Allegro) |
| `attributes` | varchar(350) | Product attributes/variant name |
| `price_brutto` | float | Single item gross price |
| `tax_rate` | float | VAT rate (0-100, -1=exempt, -0.02=NP, -0.03=reverse charge) |
| `quantity` | int | Quantity |
| `weight` | float | Single item weight |
| `bundle_id` | int | Bundle ID (0 if not from bundle) |

### Sample

```json
// Input
{
  "date_confirmed_from": 1407341754,
  "get_unconfirmed_orders": false
}

// Output
{
  "status": "SUCCESS",
  "orders": [
    {
      "order_id": 1630473,
      "shop_order_id": 2824,
      "external_order_id": "534534234",
      "order_source": "amazon",
      "order_source_id": 2598,
      "order_status_id": 6624,
      "date_add": 1407841161,
      "date_confirmed": 1407841256,
      "user_login": "nick123",
      "currency": "GBP",
      "payment_method": "PayPal",
      "delivery_method": "Expedited shipping",
      "delivery_price": 10,
      "delivery_fullname": "John Doe",
      "delivery_company": "Company",
      "delivery_address": "Long Str 12",
      "delivery_city": "London",
      "delivery_postcode": "E2 8HQ",
      "delivery_country_code": "GB",
      "products": [
        {
          "storage": "shop",
          "storage_id": 1,
          "order_product_id": 154904741,
          "product_id": "5434",
          "variant_id": 52124,
          "name": "Harry Potter and the Chamber of Secrets",
          "sku": "LU4235",
          "ean": "1597368451236",
          "price_brutto": 20.00,
          "tax_rate": 23,
          "quantity": 2,
          "weight": 1
        }
      ]
    }
  ]
}
```

---

## getJournalList

Download order events from the last 3 days. Must be enabled in account API settings.

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `last_log_id` | int | Yes | Log ID to start from |
| `logs_types` | array | No | Filter by event type IDs |
| `order_id` | int | No | Filter by order ID |

### Event Types

| Type ID | Description |
|---------|-------------|
| 1 | Order creation |
| 2 | DOF download (order confirmation) |
| 3 | Payment of the order |
| 4 | Removal of order/invoice/receipt |
| 5 | Merging the orders |
| 6 | Splitting the order |
| 7 | Issuing an invoice |
| 8 | Issuing a receipt |
| 9 | Package creation |
| 10 | Deleting a package |
| 11 | Editing delivery data |
| 12 | Adding a product to an order |
| 13 | Editing the product in the order |
| 14 | Removing the product from the order |
| 15 | Adding a buyer to a blacklist |
| 16 | Editing order data |
| 17 | Copying an order |
| 18 | Order status change |
| 19 | Invoice deletion |
| 20 | Receipt deletion |
| 21 | Editing invoice data |

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `logs` | array | Array of event objects |

**Event object:**

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | int | Event ID |
| `order_id` | int | Order ID |
| `log_type` | int | Event type (see table above) |
| `object_id` | int | Context-dependent ID (see event type) |
| `date` | int | Event date (unix) |

### Sample

```json
// Input
{ "last_log_id": 654258, "logs_types": [7, 13] }

// Output
{
  "status": "SUCCESS",
  "logs": [
    { "log_id": 456269, "log_type": 13, "order_id": 6911942, "object_id": 0, "date": 1516369287 },
    { "log_id": 456278, "log_type": 7, "order_id": 8911945, "object_id": 5107899, "date": 1516369390 }
  ]
}
```

---

## setOrderStatus

Change order status.

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `order_id` | int | Yes | Order ID |
| `status_id` | int | Yes | Status ID (from `getOrderStatusList`) |

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |

---

## setOrderFields

Edit selected fields of a specific order. Only include fields you want to modify.

### Input Parameters

Accepts any order fields that are editable (address data, notes, etc.).

---

## getOrderStatusList

Download order statuses created by the customer.

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `statuses` | array | Array of status objects |

**Status object:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Status ID |
| `name` | varchar | Status name (basic) |
| `name_for_customer` | varchar | Display name for customer |
| `color` | varchar | Hex color |

### Sample

```json
{
  "status": "SUCCESS",
  "statuses": [
    { "id": 1051, "name": "New orders", "name_for_customer": "Order accepted" },
    { "id": 1052, "name": "To be paid (courier)", "name_for_customer": "Awaiting payment" },
    { "id": 1471, "name": "Dispatched", "name_for_customer": "The parcel has been shipped" }
  ]
}
```

# WooCommerce ↔ pinquark WMS — Field Mapping

## Order Mapping

### WooCommerce Order → Unified Order

| WooCommerce Field | Unified Order Field | Notes |
|---|---|---|
| `id` | `external_id` | Cast to string |
| `status` | `status` | Mapped via status table |
| `currency` | `currency` | |
| `total` | `total_amount` | Cast to float |
| `customer_id` | `buyer.external_id` | Cast to string |
| `customer_note` | `notes` | |
| `payment_method_title` | `payment_type` | Falls back to `payment_method` |
| `date_created` | `created_at` | ISO 8601 |
| `date_modified` | `updated_at` | ISO 8601 |
| `billing.first_name` | `buyer.first_name` | |
| `billing.last_name` | `buyer.last_name` | |
| `billing.email` | `buyer.email` | |
| `billing.company` | `buyer.company_name` | |
| `billing.phone` | `delivery_address.phone` | Copied from billing |
| `billing.address_1` | `invoice_address.street` | |
| `billing.city` | `invoice_address.city` | |
| `billing.postcode` | `invoice_address.postal_code` | |
| `billing.country` | `invoice_address.country_code` | |
| `shipping.first_name` | `delivery_address.first_name` | |
| `shipping.last_name` | `delivery_address.last_name` | |
| `shipping.address_1` | `delivery_address.street` | |
| `shipping.address_2` | `delivery_address.apartment_number` | |
| `shipping.city` | `delivery_address.city` | |
| `shipping.postcode` | `delivery_address.postal_code` | |
| `shipping.country` | `delivery_address.country_code` | |
| `shipping_lines[0].method_title` | `delivery_method` | First shipping line |

### WooCommerce Order Line Item → Unified OrderLine

| WooCommerce Field | Unified OrderLine Field | Notes |
|---|---|---|
| `id` | `external_id` | Cast to string |
| `product_id` | `product_id`, `offer_id` | Cast to string |
| `sku` | `sku` | |
| `name` | `name` | |
| `quantity` | `quantity` | |
| `price` | `unit_price` | |
| (from order) | `currency` | Inherited from order |

## Product Mapping

### WooCommerce Product → Unified Product

| WooCommerce Field | Unified Product Field | Notes |
|---|---|---|
| `id` | `external_id` | Cast to string |
| `sku` | `sku` | |
| `name` | `name` | |
| `description` | `description` | |
| `regular_price` | `price` | Falls back to `price` field |
| `stock_quantity` | `stock_quantity` | 0.0 if null |
| `attributes[].name` | `attributes` key | |
| `attributes[].options` | `attributes` value | List of strings |

## Status Mapping

### WooCommerce → Unified (inbound)

| WooCommerce Status | Unified OrderStatus |
|---|---|
| `pending` | `NEW` |
| `processing` | `PROCESSING` |
| `on-hold` | `PROCESSING` |
| `completed` | `DELIVERED` |
| `cancelled` | `CANCELLED` |
| `refunded` | `RETURNED` |
| `failed` | `CANCELLED` |
| `trash` | `CANCELLED` |

### Unified → WooCommerce (outbound)

| Unified OrderStatus | WooCommerce Status |
|---|---|
| `NEW` | `pending` |
| `PROCESSING` | `processing` |
| `READY_FOR_SHIPMENT` | `processing` |
| `SHIPPED` | `completed` |
| `DELIVERED` | `completed` |
| `CANCELLED` | `cancelled` |
| `RETURNED` | `refunded` |

## WooCommerce REST API Endpoints Used

| Operation | Method | Endpoint |
|---|---|---|
| List orders | `GET` | `/wp-json/wc/v3/orders` |
| Get order | `GET` | `/wp-json/wc/v3/orders/{id}` |
| Update order | `PUT` | `/wp-json/wc/v3/orders/{id}` |
| List products | `GET` | `/wp-json/wc/v3/products` |
| Get product | `GET` | `/wp-json/wc/v3/products/{id}` |
| Create product | `POST` | `/wp-json/wc/v3/products` |
| Update product | `PUT` | `/wp-json/wc/v3/products/{id}` |
| List customers | `GET` | `/wp-json/wc/v3/customers` |
| Get customer | `GET` | `/wp-json/wc/v3/customers/{id}` |
| System status | `GET` | `/wp-json/wc/v3/system_status` |

## Query Parameters

| Parameter | Endpoint | Description |
|---|---|---|
| `per_page` | All list endpoints | Items per page (max 100) |
| `page` | All list endpoints | Page number |
| `modified_after` | Orders, Products | ISO 8601 — only items modified after this date |
| `modified_before` | Orders | ISO 8601 — only items modified before this date |
| `status` | Orders | Filter by order status |
| `sku` | Products | Filter by SKU |

## Authentication

| Protocol | Method | Details |
|---|---|---|
| HTTPS | Basic Auth | `consumer_key` as username, `consumer_secret` as password |
| HTTP | OAuth 1.0a | HMAC-SHA256 signature in query parameters |

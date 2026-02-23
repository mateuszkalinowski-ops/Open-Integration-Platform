# Shopify API Mapping — v1.0.0

Field mapping between pinquark unified schemas and Shopify Admin REST API 2024-07.

## Order Mapping

### Shopify Order → pinquark Order

| pinquark Field | Shopify Field | Notes |
|---|---|---|
| `external_id` | `order.id` | Shopify numeric ID (cast to string) |
| `account_name` | — | From connector configuration |
| `status` | Derived from `fulfillment_status`, `cancelled_at`, `closed_at` | See Status Mapping |
| `buyer.external_id` | `order.customer.id` | |
| `buyer.email` | `order.customer.email` or `order.email` | |
| `buyer.first_name` | `order.customer.first_name` | |
| `buyer.last_name` | `order.customer.last_name` | |
| `buyer.is_guest` | — | `true` if no `customer` object |
| `delivery_address.first_name` | `order.shipping_address.first_name` | |
| `delivery_address.last_name` | `order.shipping_address.last_name` | |
| `delivery_address.company_name` | `order.shipping_address.company` | |
| `delivery_address.street` | `order.shipping_address.address1` + `address2` | Concatenated with ", " |
| `delivery_address.city` | `order.shipping_address.city` | |
| `delivery_address.postal_code` | `order.shipping_address.zip` | |
| `delivery_address.country_code` | `order.shipping_address.country_code` | |
| `delivery_address.phone` | `order.shipping_address.phone` | |
| `invoice_address.*` | `order.billing_address.*` | Same mapping as delivery |
| `lines[].external_id` | `order.line_items[].id` | |
| `lines[].offer_id` | `order.line_items[].variant_id` | |
| `lines[].product_id` | `order.line_items[].product_id` | |
| `lines[].sku` | `order.line_items[].sku` | |
| `lines[].name` | `order.line_items[].name` or `.title` | |
| `lines[].quantity` | `order.line_items[].quantity` | |
| `lines[].unit_price` | `order.line_items[].price` | |
| `lines[].currency` | `order.currency` | |
| `total_amount` | `order.total_price` | |
| `currency` | `order.currency` | |
| `payment_type` | `order.financial_status` | |
| `delivery_method` | `order.shipping_lines[0].title` | First shipping line |
| `notes` | `order.note` | |
| `created_at` | `order.created_at` | |
| `updated_at` | `order.updated_at` | |
| `raw_data` | Full Shopify order JSON | Preserved for debugging |

### Status Mapping

| Shopify State | pinquark OrderStatus |
|---|---|
| `cancelled_at` is set | `CANCELLED` |
| `closed_at` set + `fulfillment_status=fulfilled` | `DELIVERED` |
| `closed_at` set (not fulfilled) | `SHIPPED` |
| `fulfillment_status=fulfilled` | `SHIPPED` |
| `fulfillment_status=partial` | `PROCESSING` |
| No fulfillment status | `NEW` |

### Reverse Status Mapping (pinquark → Shopify Action)

| pinquark OrderStatus | Shopify Action |
|---|---|
| `CANCELLED` | `POST /orders/{id}/cancel.json` |
| `SHIPPED` / `READY_FOR_SHIPMENT` | Create fulfillment via Fulfillment Orders API |
| `DELIVERED` | `POST /orders/{id}/close.json` |

## Product Mapping

### Shopify Product → pinquark Product

| pinquark Field | Shopify Field | Notes |
|---|---|---|
| `external_id` | `product.id` | |
| `name` | `product.title` | |
| `description` | `product.body_html` | |
| `sku` | `product.variants[0].sku` | First variant |
| `ean` | `product.variants[0].barcode` | First variant |
| `price` | `product.variants[0].price` | First variant |
| `stock_quantity` | `product.variants[0].inventory_quantity` | First variant |
| `attributes.vendor` | `product.vendor` | |
| `attributes.product_type` | `product.product_type` | |
| `attributes.tags` | `product.tags` | |
| `attributes.status` | `product.status` | |
| `attributes.handle` | `product.handle` | |
| `attributes.variants_count` | `len(product.variants)` | |

### pinquark Product → Shopify Product (create/update)

| Shopify Field | pinquark Field | Notes |
|---|---|---|
| `product.title` | `name` | Required |
| `product.body_html` | `description` | |
| `product.vendor` | `attributes.vendor` | |
| `product.product_type` | `attributes.product_type` | |
| `product.tags` | `attributes.tags` | |
| `product.variants[0].sku` | `sku` | |
| `product.variants[0].barcode` | `ean` | |
| `product.variants[0].price` | `price` | |

## Stock Mapping

### pinquark StockItem → Shopify Inventory Level

| Shopify Field | pinquark Field | Notes |
|---|---|---|
| `inventory_item_id` | `product_id` | Must be Shopify inventory_item_id |
| `location_id` | `warehouse_id` or account default | From config `default_location_id` |
| `available` | `quantity` | |

## Kafka Topics

| Topic | Direction | Content |
|---|---|---|
| `shopify.output.ecommerce.orders.save` | OUT | New/updated orders from scraper |
| `shopify.input.ecommerce.orders.status` | IN | Order status updates to apply |
| `shopify.input.ecommerce.stock.sync` | IN | Stock level updates to sync |

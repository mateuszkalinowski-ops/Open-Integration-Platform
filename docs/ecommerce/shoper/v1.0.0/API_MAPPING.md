# Shoper API Mapping — Open Integration Platform by Pinquark.com

## Orders

### Shoper → Pinquark Order

| Shoper Field | Pinquark Field | Notes |
|-------------|---------------|-------|
| `order_id` | `external_id` | Converted to string |
| `user_id` | `buyer.external_id` | |
| `status_id` | `status` | Mapped via status table |
| `sum` | `total_amount` | |
| `email` | `buyer.email` | |
| `shipping_id` | `delivery_method` | Delivery method ID |
| `payment_id` | `payment_type` | Payment method ID |
| `notes` | `notes` | |
| `delivery_address.firstname` | `delivery_address.first_name` | |
| `delivery_address.lastname` | `delivery_address.last_name` | |
| `delivery_address.company` | `delivery_address.company_name` | |
| `delivery_address.street1` | `delivery_address.street` | |
| `delivery_address.city` | `delivery_address.city` | |
| `delivery_address.postcode` | `delivery_address.postal_code` | |
| `delivery_address.country_code` | `delivery_address.country_code` | |
| `delivery_address.phone` | `delivery_address.phone` | |

### Order Products

| Shoper Field | Pinquark Field | Notes |
|-------------|---------------|-------|
| `id` | `external_id` | |
| `product_id` | `product_id`, `offer_id` | |
| `code` | `sku` | |
| `name` | `name` | |
| `quantity` | `quantity` | |
| `price` | `unit_price` | |
| `unit` | `unit` | Default: "szt." |

## Order Status Mapping

### Shoper → Pinquark

| Shoper `status_id` | Pinquark `OrderStatus` | Shoper Description |
|--------------------|------------------------|-------------|
| 1 | NEW | Temporary document |
| 2 | NEW | New |
| 3 | PROCESSING | In progress |
| 4 | PROCESSING | In progress |
| 5 | PROCESSING | In progress |
| 6 | READY_FOR_SHIPMENT | Ready for shipment |
| 7 | DELIVERED | Completed |
| 8 | CANCELLED | Cancelled |
| 9 | CANCELLED | Cancelled |
| 10 | CANCELLED | Cancelled |
| 12 | CANCELLED | Cancelled |

### Pinquark → Shoper

| Pinquark `OrderStatus` | Shoper `status_id` |
|------------------------|--------------------|
| NEW | 2 |
| PROCESSING | 4 |
| READY_FOR_SHIPMENT | 6 |
| SHIPPED | 7 |
| DELIVERED | 7 |
| CANCELLED | 8 |

## Products

### Shoper → Pinquark Product

| Shoper Field | Pinquark Field | Notes |
|-------------|---------------|-------|
| `product_id` | `external_id` | |
| `code` | `sku` | |
| `ean` | `ean` | Fallback: `stock.ean` |
| `translations.{lang}.name` | `name` | Based on account `language_id` |
| `stock.price` | `price` | |
| `stock.stock` | `stock_quantity` | |

## Users

### Shoper → Pinquark Buyer

| Shoper Field | Pinquark Field | Notes |
|-------------|---------------|-------|
| `user_id` | `external_id` | |
| `firstname` | `first_name` | |
| `lastname` | `last_name` | |
| `email` | `email` | |

## Shoper REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|------|
| `/webapi/rest/auth` | POST | Authentication (Basic Auth → Bearer) |
| `/webapi/rest/orders` | GET | List orders |
| `/webapi/rest/orders/{id}` | GET/PUT | Order details / update |
| `/webapi/rest/order-products` | GET | Order products |
| `/webapi/rest/products` | GET/POST | List / create products |
| `/webapi/rest/products/{id}` | GET/PUT | Product details / update |
| `/webapi/rest/users` | GET | List users |
| `/webapi/rest/parcels` | GET/POST | List / create parcels |
| `/webapi/rest/parcels/{id}` | PUT | Update parcel |
| `/webapi/rest/units` | GET | Units of measure |
| `/webapi/rest/categories` | GET | Product categories |
| `/webapi/rest/categories-tree` | GET | Category tree |
| `/webapi/rest/shippings` | GET | Shipping methods |
| `/webapi/rest/payments` | GET | Payment methods |
| `/webapi/rest/currencies` | GET | Currencies |
| `/webapi/rest/product-images` | GET | Product images |
| `/webapi/rest/bulk` | POST | Batch operations |

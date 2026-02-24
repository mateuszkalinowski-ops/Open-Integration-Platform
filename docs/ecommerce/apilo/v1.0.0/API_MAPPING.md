# Apilo API Mapping — v1.0.0

## Order Field Mapping

### Pinquark Order → Apilo Order

| Pinquark Field | Apilo Field | Notes |
|---|---|---|
| `external_id` | `id` | Apilo order ID (e.g. `AL231100017`) |
| `status` | `status` | Integer ID, resolved via `/orders/status/map/` |
| `buyer.email` | `addressCustomer.email` | |
| `buyer.first_name` | `addressCustomer.name` (split) | First word of name |
| `buyer.last_name` | `addressCustomer.name` (split) | Remaining words |
| `buyer.company_name` | `addressCustomer.companyName` | |
| `buyer.login` | `customerLogin` | |
| `delivery_address.street` | `addressDelivery.streetName` | |
| `delivery_address.building_number` | `addressDelivery.streetNumber` | |
| `delivery_address.city` | `addressDelivery.city` | |
| `delivery_address.postal_code` | `addressDelivery.zipCode` | |
| `delivery_address.country_code` | `addressDelivery.country` | ISO 3166 alpha-2 |
| `delivery_address.phone` | `addressDelivery.phone` | |
| `invoice_address.*` | `addressInvoice.*` | Same structure |
| `lines[].external_id` | `orderItems[].id` | |
| `lines[].offer_id` | `orderItems[].idExternal` | |
| `lines[].product_id` | `orderItems[].productId` | |
| `lines[].sku` | `orderItems[].sku` | |
| `lines[].ean` | `orderItems[].ean` | |
| `lines[].name` | `orderItems[].originalName` | |
| `lines[].quantity` | `orderItems[].quantity` | |
| `lines[].unit` | `orderItems[].unit` | |
| `lines[].unit_price` | `orderItems[].originalPriceWithTax` | Gross price |
| `lines[].tax_rate` | `orderItems[].tax` | Percentage |
| `total_amount` | `originalAmountTotalWithTax` | |
| `currency` | `originalCurrency` | ISO 4217 |
| `payment_type` | `paymentType` | Integer ID |
| `created_at` | `createdAt` | ISO 8601 |
| `updated_at` | `updatedAt` | ISO 8601 |
| `notes` | `orderNotes[].comment` | Concatenated |

### Order Status Mapping

Apilo uses configurable integer status IDs. Mapping is done by status name heuristics:

| Apilo Status Name | Pinquark OrderStatus |
|---|---|
| Nowy / New | `NEW` |
| Niepotwierdzone / Unconfirmed | `NEW` |
| W realizacji / In progress | `PROCESSING` |
| Do wysyłki / Ready to ship | `READY_FOR_SHIPMENT` |
| Wysłane / Shipped | `SHIPPED` |
| Dostarczone / Delivered | `DELIVERED` |
| Anulowane / Cancelled | `CANCELLED` |
| Zwrot / Returned | `RETURNED` |

## Product Field Mapping

### Pinquark Product → Apilo Product

| Pinquark Field | Apilo Field | Notes |
|---|---|---|
| `external_id` | `id` | Apilo internal integer ID |
| `sku` | `sku` | Unique SKU |
| `ean` | `ean` | EAN barcode |
| `name` | `name` / `groupName` | Falls back to `groupName` if `name` is empty |
| `description` | `description` | Long description |
| `unit` | `unit` | Unit of measure |
| `price` | `priceWithTax` | Gross price |
| `stock_quantity` | `quantity` | Inventory count |
| `attributes.original_code` | `originalCode` | External product code |
| `attributes.weight` | `weight` | Product weight |
| `attributes.tax` | `tax` | VAT rate string |

## Payment Type Mapping

Resolved via `GET /rest/api/orders/payment/map/`:

| ID | Key | Name |
|---|---|---|
| 1 | `PAYMENT_TYPE_BANK_TRANSFER` | Przelew bankowy |
| 2 | `PAYMENT_TYPE_COD` | Pobranie |
| 3 | `PAYMENT_TYPE_SERVICE_PAYU` | PayU |

## Carrier Mapping

Resolved via `GET /rest/api/orders/carrier/map/`.

## API Endpoints Used

| Pinquark Operation | Apilo Endpoint | Method |
|---|---|---|
| Fetch orders | `/rest/api/orders/` | GET |
| Get order | `/rest/api/orders/{id}/` | GET |
| Create order | `/rest/api/orders/` | POST |
| Update status | `/rest/api/orders/{id}/status/` | PUT |
| Add payment | `/rest/api/orders/{id}/payment/` | POST |
| Add note | `/rest/api/orders/{id}/note/` | POST |
| Add shipment | `/rest/api/orders/{id}/shipment/` | POST |
| Add tag | `/rest/api/orders/{orderId}/tag/` | POST |
| Remove tag | `/rest/api/orders/{orderId}/tag/{tagId}/` | DELETE |
| List products | `/rest/api/warehouse/product/` | GET |
| Get product | `/rest/api/warehouse/product/{id}/` | GET |
| Create products | `/rest/api/warehouse/product/` | POST |
| Update products | `/rest/api/warehouse/product/` | PUT |
| Patch products | `/rest/api/warehouse/product/` | PATCH |
| Delete product | `/rest/api/warehouse/product/{id}/` | DELETE |
| Create shipment | `/rest/api/shipping/shipment/` | POST |
| Get shipment | `/rest/api/shipping/shipment/{id}/` | GET |
| Auth token | `/rest/auth/token/` | POST |

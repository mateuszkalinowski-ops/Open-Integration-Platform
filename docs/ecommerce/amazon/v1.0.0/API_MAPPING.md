# API Mapping — Amazon SP-API ↔ Pinquark Unified Schemas

## Order Mapping

### Amazon Order → Pinquark Order

| Amazon Field | Pinquark Field | Notes |
|---|---|---|
| `AmazonOrderId` | `external_id` | |
| `OrderStatus` | `status` | Mapped via status table below |
| `PurchaseDate` | `created_at` | ISO 8601 |
| `LastUpdateDate` | `updated_at` | ISO 8601 |
| `OrderTotal.Amount` | `total_amount` | |
| `OrderTotal.CurrencyCode` | `currency` | |
| `PaymentMethod` | `payment_type` | |
| `ShipServiceLevel` | `delivery_method` | |
| `ShippingAddress.Name` | `delivery_address.first_name` / `last_name` | Split on first space |
| `ShippingAddress.AddressLine1/2/3` | `delivery_address.street` | Joined with comma |
| `ShippingAddress.City` | `delivery_address.city` | |
| `ShippingAddress.PostalCode` | `delivery_address.postal_code` | |
| `ShippingAddress.CountryCode` | `delivery_address.country_code` | |
| `ShippingAddress.Phone` | `delivery_address.phone` | |
| `BuyerInfo.BuyerEmail` | `buyer.email` | |
| `BuyerInfo.BuyerName` | `buyer.first_name` / `last_name` | Split on first space |

### Amazon Order Item → Pinquark OrderLine

| Amazon Field | Pinquark Field | Notes |
|---|---|---|
| `OrderItemId` | `external_id` | |
| `ASIN` | `offer_id`, `product_id` | |
| `SellerSKU` | `sku` | |
| `Title` | `name` | |
| `QuantityOrdered` | `quantity` | |
| `ItemPrice.Amount` / `QuantityOrdered` | `unit_price` | Total divided by qty |
| `ItemPrice.CurrencyCode` | `currency` | |

## Order Status Mapping

| Amazon Status | Pinquark OrderStatus | Description |
|---|---|---|
| `Pending` | `NEW` | Payment not yet completed |
| `PendingAvailability` | `NEW` | Pre-order, not yet available |
| `Unshipped` | `PROCESSING` | Payment completed, not shipped |
| `PartiallyShipped` | `PROCESSING` | Some items shipped |
| `Shipped` | `SHIPPED` | All items shipped |
| `Canceled` | `CANCELLED` | Order cancelled |
| `Unfulfillable` | `CANCELLED` | Cannot be fulfilled (FBA) |
| `InvoiceUnconfirmed` | `PROCESSING` | Awaiting invoice confirmation |

### Reverse Mapping (Pinquark → Amazon Action)

| Pinquark OrderStatus | Amazon Action |
|---|---|
| `PROCESSING` | Submit order acknowledgement (Success) |
| `SHIPPED` | Submit shipment confirmation feed |
| `CANCELLED` | Submit order acknowledgement (Failure) |

## Product Mapping

### Amazon Catalog Item → Pinquark Product

| Amazon Field | Pinquark Field | Notes |
|---|---|---|
| `asin` | `external_id` | |
| `summaries[0].itemName` | `name` | First marketplace summary |
| `summaries[0].brandName` | `attributes.brand` | |
| `summaries[0].manufacturer` | `attributes.manufacturer` | |
| `summaries[0].modelNumber` | `attributes.model_number` | |
| `identifiers[].identifier` (EAN/GTIN) | `ean` | First EAN/GTIN found |

## Feed Types Used

| Feed Type | Purpose | Trigger |
|---|---|---|
| `POST_ORDER_ACKNOWLEDGEMENT_DATA` | Acknowledge or cancel orders | `update_order_status(PROCESSING/CANCELLED)` |
| `POST_ORDER_FULFILLMENT_DATA` | Confirm shipment with tracking | `confirm_shipment()` |
| `POST_INVENTORY_AVAILABILITY_DATA` | Update stock levels | `sync_stock()` |

## Report Types Available

| Report Type | Description |
|---|---|
| `GET_FLAT_FILE_OPEN_LISTINGS_DATA` | Open listings summary |
| `GET_MERCHANT_LISTINGS_ALL_DATA` | All listings detail |
| `GET_MERCHANT_LISTINGS_DATA` | Active listings only |
| `GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA` | FBA inventory levels |
| `GET_FLAT_FILE_ORDERS_DATA` | Order tracking report |
| `GET_FLAT_FILE_ACTIONABLE_ORDER_DATA_SHIPPING` | Unshipped orders (restricted) |

## Authentication

| Credential | Purpose |
|---|---|
| `client_id` | LWA application identifier |
| `client_secret` | LWA application secret |
| `refresh_token` | Per-seller authorization (does not expire) |
| Access token (derived) | Bearer token for API calls (1 hour TTL) |

Token endpoint: `POST https://api.amazon.com/auth/o2/token`

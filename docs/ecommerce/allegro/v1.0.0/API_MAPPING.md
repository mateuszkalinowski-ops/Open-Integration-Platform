# Allegro API Mapping — v1.0.0

## Order Field Mapping

### pinquark Order ↔ Allegro Checkout Form

| pinquark Field | Allegro Field | Notes |
|----------------|---------------|-------|
| `order.external_id` | `checkoutForm.id` | UUID |
| `order.status` | `checkoutForm.status` | Mapped via status table below |
| `order.account_name` | _(derived)_ | From account config, not in Allegro data |
| `order.total_amount` | `checkoutForm.summary.totalToPay.amount` | String → float conversion |
| `order.currency` | `checkoutForm.summary.totalToPay.currency` | Default: PLN |
| `order.payment_type` | `checkoutForm.payment.type` | e.g., "ONLINE" |
| `order.delivery_method` | `checkoutForm.delivery.method.name` | |
| `order.updated_at` | `checkoutForm.updatedAt` | ISO 8601 |
| `order.created_at` | _(not available)_ | Use `lineItems[0].boughtAt` as approximation |

### Buyer

| pinquark Field | Allegro Field |
|----------------|---------------|
| `buyer.external_id` | `buyer.id` |
| `buyer.email` | `buyer.email` |
| `buyer.login` | `buyer.login` |
| `buyer.first_name` | `buyer.firstName` |
| `buyer.last_name` | `buyer.lastName` |
| `buyer.company_name` | `buyer.companyName` |
| `buyer.is_guest` | `buyer.guest` |

### Delivery Address

| pinquark Field | Allegro Field |
|----------------|---------------|
| `address.first_name` | `delivery.address.firstName` |
| `address.last_name` | `delivery.address.lastName` |
| `address.company_name` | `delivery.address.companyName` |
| `address.street` | `delivery.address.street` |
| `address.city` | `delivery.address.city` |
| `address.postal_code` | `delivery.address.zipCode` |
| `address.country_code` | `delivery.address.countryCode` |
| `address.phone` | `delivery.address.phoneNumber` |

### Order Lines

| pinquark Field | Allegro Field | Notes |
|----------------|---------------|-------|
| `line.external_id` | `lineItem.id` | |
| `line.offer_id` | `lineItem.offer.id` | |
| `line.product_id` | _(fetched from offer.product.id)_ | Requires extra API call |
| `line.sku` | `offer.external.id` or `offer.id` | Falls back to offer ID |
| `line.ean` | Offer/Product parameter `225693` | EAN/GTIN parameter |
| `line.name` | `lineItem.offer.name` | |
| `line.quantity` | `lineItem.quantity` | int → float |
| `line.unit_price` | `lineItem.price.amount` | String → float |
| `line.currency` | `lineItem.price.currency` | |

## Status Mapping

### Allegro → pinquark (order import)

| Allegro CheckoutFormStatus | pinquark OrderStatus |
|----------------------------|---------------------|
| `READY_FOR_PROCESSING` | `NEW` |
| `BOUGHT` | `NEW` |
| `FILLED_IN` | `NEW` |
| `CANCELLED` | `CANCELLED` |

### pinquark → Allegro (status update)

| pinquark OrderStatus | Allegro FulfillmentStatus |
|----------------------|--------------------------|
| `NEW` | `NEW` |
| `PROCESSING` | `PROCESSING` |
| `READY_FOR_SHIPMENT` | `READY_FOR_SHIPMENT` |
| `SHIPPED` | `SENT` |
| `DELIVERED` | `PICKED_UP` |
| `CANCELLED` | `CANCELLED` |
| `RETURNED` | _(not supported)_ |

## Event Types Processed by Scraper

| Allegro Event Type | Action |
|-------------------|--------|
| `READY_FOR_PROCESSING` | Import order as NEW |
| `BUYER_CANCELLED` | Import/update order as CANCELLED |
| `AUTO_CANCELLED` | Import/update order as CANCELLED |
| `BUYER_MODIFIED` | Re-import order with updated data |

## Allegro API Endpoints Used

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Get order events | GET | `/order/events` |
| Get checkout form | GET | `/order/checkout-forms/{id}` |
| List checkout forms | GET | `/order/checkout-forms` |
| Update fulfillment | PUT | `/order/checkout-forms/{id}/fulfillment` |
| Get offer details | GET | `/sale/offers/{id}` |
| Get product details | GET | `/sale/products/{id}` |
| Update stock | PUT | `/sale/offer-quantity-change-commands/{id}` |
| Device code auth | POST | `/auth/oauth/device` |
| Token exchange | POST | `/auth/oauth/token` |

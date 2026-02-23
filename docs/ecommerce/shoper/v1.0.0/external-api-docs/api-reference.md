# Shoper REST API — Reference

Source: https://developers.shoper.pl/developers/api/getting-started
Fetched: 2026-02-22

> **Note**: Shoper REST API is available at `/webapi/rest/` on every Shoper store.
> Access requires an administrator account with "WebApi" group permissions.
> Official docs are behind a login at developers.shoper.pl — this file consolidates
> publicly available information and details extracted from working integrations.

## Base URL

```
https://{shop-domain}/webapi/rest/
```

Example: `https://mystore.shoparena.pl/webapi/rest/`

All endpoints below are relative to this base URL.

---

## Pagination (ShoperPage)

All list endpoints return a paginated response:

```json
{
  "count": 254,
  "pages": 6,
  "page": 1,
  "list": [
    { ... },
    { ... }
  ]
}
```

| Field   | Type    | Description                          |
|---------|---------|--------------------------------------|
| `count` | integer | Total number of records              |
| `pages` | integer | Total number of pages                |
| `page`  | integer | Current page number (1-based)        |
| `list`  | array   | Array of entity objects on this page |

### Pagination Parameters

| Parameter | Type    | Description                              |
|-----------|---------|------------------------------------------|
| `page`    | integer | Page number to retrieve (default: 1)     |
| `limit`   | integer | Number of items per page (default: ~50)  |

### Filtering

Filters are passed as a JSON-encoded `filters` query parameter:

```
GET /webapi/rest/orders?filters={"status_date":{">":"2026-01-01 00:00:00"}}
```

Supported filter operators:
- `=` — exact match
- `!=` — not equal
- `>`, `>=`, `<`, `<=` — comparison
- `IN` — value in array
- `LIKE` — partial match

### Sorting

Sorting via `order` query parameter:

```
GET /webapi/rest/orders?order=date+desc
```

---

## Orders API

### List Orders

```
GET /webapi/rest/orders
```

Query parameters: standard pagination + filters.

Common filters:
| Filter field   | Description                           |
|----------------|---------------------------------------|
| `status_date`  | Filter by status change date          |
| `date`         | Filter by order creation date         |
| `status_id`    | Filter by status ID                   |
| `user_id`      | Filter by customer ID                 |
| `confirm`      | Filter by confirmation status         |

Response: `ShoperPage` with order objects.

### Get Order

```
GET /webapi/rest/orders/{order_id}
```

### Update Order

```
PUT /webapi/rest/orders/{order_id}
```

Body (partial update):
```json
{
  "status_id": "4",
  "notes_priv": "Internal note"
}
```

### Order Properties

| Property                     | Type    | Description                            |
|------------------------------|---------|----------------------------------------|
| `order_id`                   | integer | Unique order ID                        |
| `user_id`                    | integer | Customer ID (0 = guest)                |
| `date`                       | string  | Creation date (YYYY-MM-DD HH:MM:SS)   |
| `status_id`                  | string  | Status ID (see Order Statuses)         |
| `sum`                        | float   | Total amount                           |
| `payment_id`                 | integer | Payment method ID                      |
| `shipping_id`                | integer | Shipping method ID                     |
| `shipping_cost`              | float   | Shipping cost                          |
| `email`                      | string  | Customer email                         |
| `delivery_code`              | string  | Delivery tracking code                 |
| `code`                       | string  | Order code                             |
| `confirm`                    | boolean | Order confirmed                        |
| `notes`                      | string  | Customer notes                         |
| `notes_priv`                 | string  | Private (admin) notes                  |
| `notes_pub`                  | string  | Public notes                           |
| `currency_id`                | integer | Currency ID                            |
| `paid`                       | float   | Amount paid                            |
| `pickup_point`               | string  | Pickup point identifier                |
| `billing_address`            | object  | Billing address (OrderAddress)         |
| `delivery_address`           | object  | Delivery address (OrderAddress)        |
| `status`                     | object  | Status details (OrderStatus)           |
| `auction`                    | object  | Marketplace auction data               |
| `additional_fields`          | array   | Custom fields                          |
| `shipping_additional_fields` | object  | Shipping-specific custom fields        |

### OrderAddress Object

| Property                    | Type    | Description          |
|-----------------------------|---------|----------------------|
| `address_id`                | integer | Address ID           |
| `order_id`                  | integer | Related order ID     |
| `type`                      | integer | Address type         |
| `firstname`                 | string  | First name           |
| `lastname`                  | string  | Last name            |
| `company`                   | string  | Company name         |
| `tax_identification_number` | string  | Tax ID (NIP)         |
| `city`                      | string  | City                 |
| `postcode`                  | string  | Postal code          |
| `street1`                   | string  | Street line 1        |
| `street2`                   | string  | Street line 2        |
| `state`                     | string  | State/Province       |
| `country`                   | string  | Country name         |
| `phone`                     | string  | Phone number         |
| `country_code`              | string  | ISO country code     |

---

## Order Products API

### List Order Products

```
GET /webapi/rest/order-products
```

Returns products (line items) for orders. Filter by `order_id` to get products for specific orders.

```
GET /webapi/rest/order-products?filters={"order_id":{"IN":["101","102","103"]}}
```

### Order Product Properties

| Property        | Type    | Description                    |
|-----------------|---------|--------------------------------|
| `id`            | integer | Line item ID                   |
| `order_id`      | integer | Parent order ID                |
| `stock_id`      | integer | Stock variant ID               |
| `product_id`    | integer | Product ID                     |
| `price`         | float   | Unit price                     |
| `discount_perc` | float   | Discount percentage            |
| `quantity`       | float   | Quantity ordered               |
| `name`          | string  | Product name                   |
| `code`          | string  | Product code (SKU)             |
| `tax`           | string  | Tax rate label                 |
| `tax_value`     | float   | Tax value                      |
| `unit`          | string  | Unit of measure                |
| `weight`        | float   | Weight                         |

---

## Products API

### List Products

```
GET /webapi/rest/products
```

Common filters:
| Filter field  | Description                            |
|---------------|----------------------------------------|
| `edit_date`   | Filter by last modification date       |
| `add_date`    | Filter by creation date                |
| `category_id` | Filter by category                     |
| `code`        | Filter by product code (SKU)           |

### Get Product

```
GET /webapi/rest/products/{product_id}
```

### Update Product

```
PUT /webapi/rest/products/{product_id}
```

Body (partial update, e.g. update stock):
```json
{
  "stock": {
    "stock": 42
  }
}
```

### Product Properties

| Property       | Type    | Description                              |
|----------------|---------|------------------------------------------|
| `product_id`   | integer | Unique product ID                        |
| `type`         | integer | Product type                             |
| `producer_id`  | integer | Producer/manufacturer ID                 |
| `category_id`  | integer | Main category ID                         |
| `unit_id`      | integer | Unit of measure ID                       |
| `add_date`     | string  | Creation date                            |
| `edit_date`    | string  | Last modification date                   |
| `code`         | string  | Product code (SKU)                       |
| `ean`          | string  | EAN barcode                              |
| `pkwiu`        | string  | PKWiU classification                     |
| `dimension_w`  | float   | Width                                    |
| `dimension_h`  | float   | Height                                   |
| `dimension_l`  | float   | Length                                    |
| `vol_weight`   | float   | Volumetric weight                        |
| `stock`        | object  | Stock information (see Stock object)     |
| `translations` | object  | Name/description per language            |

### Stock Object (nested in Product)

| Property     | Type    | Description                  |
|--------------|---------|------------------------------|
| `stock_id`   | integer | Stock variant ID             |
| `product_id` | integer | Parent product ID            |
| `extended`   | boolean | Extended variant             |
| `price`      | float   | Price                        |
| `active`     | boolean | Active/visible               |
| `stock`      | float   | Available quantity           |
| `warn_level` | float   | Low stock warning threshold  |
| `sold`       | float   | Total sold                   |
| `code`       | string  | Variant code                 |
| `ean`        | string  | Variant EAN                  |
| `weight`     | float   | Weight                       |

### Translation Object (nested in Product)

| Property            | Type    | Description                |
|---------------------|---------|----------------------------|
| `translation_id`    | integer | Translation ID             |
| `product_id`        | integer | Parent product ID          |
| `name`              | string  | Product name               |
| `short_description` | string  | Short description          |
| `description`       | string  | Full HTML description      |
| `active`            | boolean | Translation active         |
| `isdefault`         | boolean | Default language           |
| `lang_id`           | integer | Language ID                |
| `seo_url`           | string  | SEO-friendly URL slug      |

---

## Users API

### List Users

```
GET /webapi/rest/users
```

### Get User

```
GET /webapi/rest/users/{user_id}
```

### User Properties

| Property    | Type    | Description              |
|-------------|---------|--------------------------|
| `user_id`   | integer | Unique user ID           |
| `login`     | string  | Login username           |
| `date_add`  | string  | Registration date        |
| `firstname` | string  | First name               |
| `lastname`  | string  | Last name                |
| `email`     | string  | Email address            |
| `discount`  | float   | User discount percentage |
| `active`    | boolean | Account active           |
| `comment`   | string  | Admin comment            |
| `group_id`  | integer | Customer group ID        |

---

## Parcels API

### List Parcels

```
GET /webapi/rest/parcels
```

Filter by order:
```
GET /webapi/rest/parcels?filters={"order_id":{"=":12345}}
```

### Create Parcel

```
POST /webapi/rest/parcels
```

Body:
```json
{
  "order_id": 12345,
  "shipping_id": 1,
  "shipping_code": "TRACK123456",
  "sent": 0
}
```

Returns: parcel ID (integer).

### Update Parcel

```
PUT /webapi/rest/parcels/{parcel_id}
```

Body:
```json
{
  "shipping_code": "TRACK123456",
  "sent": 1
}
```

### Parcel Properties

| Property        | Type    | Description                    |
|-----------------|---------|--------------------------------|
| `parcel_id`     | integer | Unique parcel ID               |
| `shipping_id`   | integer | Shipping method ID             |
| `shipping_code` | string  | Tracking number / waybill      |

---

## Bulk API

Allows batching multiple API requests in a single HTTP call.

```
POST /webapi/rest/bulk
```

Body:
```json
[
  {
    "id": "request1",
    "path": "/webapi/rest/orders",
    "method": "GET",
    "params": {
      "page": "1",
      "filters": "{\"status_id\":{\"=\":\"2\"}}"
    }
  },
  {
    "id": "request2",
    "path": "/webapi/rest/products/123",
    "method": "GET",
    "params": {}
  }
]
```

Response:
```json
{
  "errors": false,
  "items": [
    {
      "id": "request1",
      "code": 200,
      "body": {
        "count": 10,
        "pages": 1,
        "page": 1,
        "list": [...]
      }
    },
    {
      "id": "request2",
      "code": 200,
      "body": { ... }
    }
  ]
}
```

---

## Other Resources

The following resources are also available via the standard CRUD pattern
(`GET /resource`, `GET /resource/{id}`, `POST /resource`, `PUT /resource/{id}`, `DELETE /resource/{id}`):

| Resource            | Endpoint                        | Description               |
|---------------------|---------------------------------|---------------------------|
| Categories          | `/webapi/rest/categories`       | Product categories        |
| Shippings           | `/webapi/rest/shippings`        | Shipping methods          |
| Payments            | `/webapi/rest/payments`         | Payment methods           |
| Currencies          | `/webapi/rest/currencies`       | Available currencies      |
| Units               | `/webapi/rest/units`            | Units of measure          |
| Order Statuses      | `/webapi/rest/order-statuses`   | Available order statuses  |
| Product Images      | `/webapi/rest/product-images`   | Product images/gallery    |
| Producers           | `/webapi/rest/producers`        | Product manufacturers     |
| Tax Rules           | `/webapi/rest/tax-rules`        | Tax rules/rates           |
| Gauges              | `/webapi/rest/gauges`           | Product attributes/sizes  |
| Additional Fields   | `/webapi/rest/additional-fields`| Custom order fields       |
| Newsletters         | `/webapi/rest/newsletters`      | Newsletter subscribers    |

---

## Common HTTP Status Codes

| Code | Meaning                                        |
|------|------------------------------------------------|
| 200  | Success                                        |
| 201  | Created                                        |
| 400  | Bad Request (invalid parameters)               |
| 401  | Unauthorized (invalid/expired token)           |
| 403  | Forbidden (insufficient permissions)           |
| 404  | Not Found                                      |
| 429  | Too Many Requests (rate limited)               |
| 500  | Internal Server Error                          |

Error response format:
```json
{
  "error": "error_description"
}
```

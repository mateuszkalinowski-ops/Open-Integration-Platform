# WooCommerce REST API — Customers Schema

> Source: https://woocommerce.github.io/woocommerce-rest-api-docs/v3.html
> Fetched: 2026-02-24

## Customer Properties

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Customer ID / WordPress user ID (read-only) |
| `created_at` | string | UTC DateTime of creation (read-only) |
| `email` | string | Email address (mandatory) |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `username` | string | Username (cannot be changed, can be auto-generated) |
| `password` | string | Password (write-only, can be auto-generated) |
| `last_order_id` | integer | Last order ID (read-only) |
| `last_order_date` | string | Last order date (read-only) |
| `orders_count` | integer | Total orders count (read-only) |
| `total_spent` | integer | Total amount spent (read-only) |
| `avatar_url` | string | Gravatar URL |
| `billing_address` | array | Billing address |
| `shipping_address` | array | Shipping address |

### Billing Address

| Attribute | Type | Description |
|-----------|------|-------------|
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `company` | string | Company name |
| `address_1` | string | Address line 1 |
| `address_2` | string | Address line 2 |
| `city` | string | City |
| `state` | string | State/Province (ISO code or name) |
| `postcode` | string | Postal code |
| `country` | string | Country (ISO code) |
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
| `state` | string | State/Province (ISO code or name) |
| `postcode` | string | Postal code |
| `country` | string | Country (ISO code) |

## CRUD Operations

### List Customers

```
GET /wp-json/wc/v3/customers
GET /wp-json/wc/v3/customers?per_page=100&page=1
```

### Get Customer

```
GET /wp-json/wc/v3/customers/{id}
```

### Get by Email

```
GET /wp-json/wc/v3/customers/email/{email}
```

### Customer Orders

```
GET /wp-json/wc/v3/customers/{id}/orders
```

### Sample Response

```json
{
  "customer": {
    "id": 2,
    "created_at": "2015-01-05T18:34:19Z",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "username": "john.doe",
    "orders_count": 2,
    "total_spent": "79.87",
    "billing_address": {
      "first_name": "John",
      "last_name": "Doe",
      "company": "",
      "address_1": "969 Market",
      "address_2": "",
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
      "company": "",
      "address_1": "969 Market",
      "address_2": "",
      "city": "San Francisco",
      "state": "CA",
      "postcode": "94103",
      "country": "US"
    }
  }
}
```

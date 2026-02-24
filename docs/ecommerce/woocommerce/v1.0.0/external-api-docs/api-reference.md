# WooCommerce REST API v3 Reference

> Source: https://woocommerce.github.io/woocommerce-rest-api-docs/v3.html
> Developer docs: https://developer.woocommerce.com/docs/apis/rest-api
> Fetched: 2026-02-24

## Introduction

The WooCommerce REST API (v3) allows WooCommerce data to be created, read, updated,
and deleted using JSON format. Introduced in WooCommerce 2.1.

**Requirements:**
- WooCommerce 2.4+ (for API v3)
- Pretty permalinks enabled (Settings > Permalinks — not "Plain")
- REST API enabled under WooCommerce > Settings

## API Versions

| API Version | WooCommerce Version |
|-------------|-------------------|
| `v1` | 2.1.x – 2.4.x |
| `v2` | 2.2.x – 2.4.x |
| `v3` | 2.4.x – current |

**Our connector uses:** `wc/v3` (via `wp-json/wc/v3/` endpoint).

## Base URL

```
https://{store_url}/wp-json/wc/v3/
```

Legacy endpoint (also supported): `https://{store_url}/wc-api/v3/`

## Request / Response Format

- **Format:** JSON
- **Dates:** RFC 3339 in UTC: `YYYY-MM-DDTHH:MM:SSZ`
- **Resource IDs:** integers
- **Monetary amounts:** strings with two decimal places
- **Blank fields:** returned as `null`

## HTTP Methods

| Method | Description |
|--------|-------------|
| `HEAD` | Return HTTP headers only |
| `GET` | Retrieve resources |
| `POST` | Create resources |
| `PUT` | Update resources |
| `DELETE` | Delete resources |

## Pagination

- Default: 10 items per page (configurable)
- `per_page` parameter: items per page (max 100)
- `page` parameter: page number (1-based)
- Response headers: `X-WC-Total` (total items), `X-WC-TotalPages` (total pages)
- `Link` header with `next`, `prev`, `first`, `last` URLs

## Error Format

```json
{
  "errors": [
    {
      "code": "woocommerce_api_invalid_order",
      "message": "Invalid order"
    }
  ]
}
```

| HTTP Code | Description |
|-----------|-------------|
| 400 | Bad Request (invalid parameters, unsupported method) |
| 401 | Unauthorized (invalid API keys) |
| 404 | Not Found (resource doesn't exist, API disabled) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

---

## Available Endpoints

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/orders` | List all orders |
| `GET` | `/orders/{id}` | Get single order |
| `POST` | `/orders` | Create order |
| `PUT` | `/orders/{id}` | Update order |
| `DELETE` | `/orders/{id}` | Delete order |
| `GET` | `/orders/count` | Get orders count |
| `GET` | `/orders/statuses` | List valid order statuses |
| `POST/PUT` | `/orders/bulk` | Bulk create/update orders |

### Order Notes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/orders/{id}/notes` | List order notes |
| `GET` | `/orders/{id}/notes/{note_id}` | Get single note |
| `POST` | `/orders/{id}/notes` | Create note |
| `PUT` | `/orders/{id}/notes/{note_id}` | Update note |
| `DELETE` | `/orders/{id}/notes/{note_id}` | Delete note |

### Order Refunds

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/orders/{id}/refunds` | List refunds |
| `GET` | `/orders/{id}/refunds/{refund_id}` | Get single refund |
| `POST` | `/orders/{id}/refunds` | Create refund |
| `DELETE` | `/orders/{id}/refunds/{refund_id}` | Delete refund |

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/products` | List all products |
| `GET` | `/products/{id}` | Get single product |
| `POST` | `/products` | Create product |
| `PUT` | `/products/{id}` | Update product |
| `DELETE` | `/products/{id}` | Delete product |
| `GET` | `/products/count` | Get products count |
| `GET` | `/products/{id}/reviews` | Get product reviews |
| `GET` | `/products/{id}/orders` | Get product orders |
| `POST/PUT` | `/products/bulk` | Bulk create/update products |

### Product Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/products/categories` | List categories |
| `GET` | `/products/categories/{id}` | Get single category |
| `POST` | `/products/categories` | Create category |
| `PUT` | `/products/categories/{id}` | Update category |
| `DELETE` | `/products/categories/{id}` | Delete category |

### Product Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/products/tags` | List tags |
| `GET` | `/products/tags/{id}` | Get single tag |
| `POST` | `/products/tags` | Create tag |
| `PUT` | `/products/tags/{id}` | Update tag |
| `DELETE` | `/products/tags/{id}` | Delete tag |

### Product Attributes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/products/attributes` | List attributes |
| `GET` | `/products/attributes/{id}` | Get single attribute |
| `POST` | `/products/attributes` | Create attribute |
| `PUT` | `/products/attributes/{id}` | Update attribute |
| `DELETE` | `/products/attributes/{id}` | Delete attribute |
| `GET` | `/products/attributes/{id}/terms` | List terms |
| `POST` | `/products/attributes/{id}/terms` | Create term |

### Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/customers` | List all customers |
| `GET` | `/customers/{id}` | Get single customer |
| `POST` | `/customers` | Create customer |
| `PUT` | `/customers/{id}` | Update customer |
| `DELETE` | `/customers/{id}` | Delete customer |
| `GET` | `/customers/count` | Get customers count |
| `GET` | `/customers/email/{email}` | Get by email |
| `GET` | `/customers/{id}/orders` | Get customer orders |
| `GET` | `/customers/{id}/downloads` | Get customer downloads |
| `POST/PUT` | `/customers/bulk` | Bulk create/update customers |

### Coupons

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/coupons` | List coupons |
| `GET` | `/coupons/{id}` | Get single coupon |
| `POST` | `/coupons` | Create coupon |
| `PUT` | `/coupons/{id}` | Update coupon |
| `DELETE` | `/coupons/{id}` | Delete coupon |
| `GET` | `/coupons/count` | Get coupons count |
| `GET` | `/coupons/code/{code}` | Get by code |
| `POST/PUT` | `/coupons/bulk` | Bulk create/update coupons |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/webhooks` | List webhooks |
| `GET` | `/webhooks/{id}` | Get single webhook |
| `POST` | `/webhooks` | Create webhook |
| `PUT` | `/webhooks/{id}` | Update webhook |
| `DELETE` | `/webhooks/{id}` | Delete webhook |
| `GET` | `/webhooks/count` | Get webhooks count |
| `GET` | `/webhooks/{id}/deliveries` | Get deliveries |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/reports` | List available reports |
| `GET` | `/reports/sales` | Get sales report |
| `GET` | `/reports/sales/top_sellers` | Get top sellers |

### System Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/system_status` | Get system status |

## Query Parameters (Common Filters)

| Parameter | Description |
|-----------|-------------|
| `filter[created_at_min]` | Items created after date (RFC 3339) |
| `filter[created_at_max]` | Items created before date |
| `filter[updated_at_min]` | Items updated after date |
| `filter[updated_at_max]` | Items updated before date |
| `filter[q]` | Keyword search |
| `filter[order]` | Sort order: ASC (default) or DESC |
| `filter[orderby]` | Sort field (default: date) |
| `filter[limit]` | Items per page |
| `filter[offset]` | Offset from first resource |
| `fields` | Limit returned fields (comma-separated) |
| `page` | Page number |
| `per_page` | Items per page (max 100) |
| `modified_after` | ISO 8601 date filter |
| `status` | Filter by status |
| `sku` | Filter by SKU (products) |

## Official Libraries

- Python: `pip install woocommerce`
- PHP: `composer require automattic/woocommerce`
- Node.js: `npm install woocommerce-api`
- Ruby: `gem install woocommerce_api`

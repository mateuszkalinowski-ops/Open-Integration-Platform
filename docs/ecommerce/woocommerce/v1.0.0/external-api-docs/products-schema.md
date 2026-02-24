# WooCommerce REST API — Products Schema

> Source: https://woocommerce.github.io/woocommerce-rest-api-docs/v3.html
> Fetched: 2026-02-24

## Product Properties

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Product ID (read-only) |
| `title` | string | Product name |
| `name` | string | Product slug (edit-only) |
| `created_at` | string | UTC DateTime of creation (read-only) |
| `updated_at` | string | UTC DateTime of last update (read-only) |
| `type` | string | Type: `simple`, `grouped`, `external`, `variable` (default: `simple`) |
| `status` | string | Status (post status, default: `publish`) |
| `downloadable` | boolean | Is downloadable |
| `virtual` | boolean | Is virtual (not shipped) |
| `permalink` | string | Product URL (read-only) |
| `sku` | string | Stock Keeping Unit |
| `global_unique_id` | string | GTIN, UPC, EAN, or ISBN |
| `price` | string | Current price (read-only, derived from regular/sale) |
| `regular_price` | string | Regular price |
| `sale_price` | string | Sale price |
| `sale_price_dates_from` | string | Sale start date `YYYY-MM-DD` (write-only) |
| `sale_price_dates_to` | string | Sale end date `YYYY-MM-DD` (write-only) |
| `price_html` | string | Price formatted in HTML (read-only) |
| `taxable` | boolean | Is taxable (read-only) |
| `tax_status` | string | Tax status: `taxable`, `shipping`, `none` |
| `tax_class` | string | Tax class |
| `managing_stock` | boolean | Stock management enabled |
| `stock_quantity` | integer | Stock quantity |
| `in_stock` | boolean | Is in stock |
| `backorders_allowed` | boolean | Backorders allowed (read-only) |
| `backordered` | boolean | Is on backorder (read-only) |
| `backorders` | mixed | Backorder setting: `false`, `notify`, `true` (write-only) |
| `sold_individually` | boolean | Only one per order |
| `purchaseable` | boolean | Can be bought (read-only) |
| `featured` | boolean | Is featured |
| `visible` | boolean | Is visible in catalog (read-only) |
| `catalog_visibility` | string | Visibility: `visible`, `catalog`, `search`, `hidden` |
| `on_sale` | boolean | Is on sale (read-only) |
| `weight` | string | Weight (decimal format) |
| `dimensions` | array | Dimensions object |
| `shipping_required` | boolean | Needs shipping (read-only) |
| `shipping_taxable` | boolean | Shipping is taxable (read-only) |
| `shipping_class` | string | Shipping class slug |
| `shipping_class_id` | integer | Shipping class ID (read-only) |
| `description` | string | Full description |
| `short_description` | string | Short description |
| `reviews_allowed` | boolean | Reviews enabled |
| `average_rating` | string | Average rating (read-only) |
| `rating_count` | integer | Rating count (read-only) |
| `related_ids` | array | Related product IDs (read-only) |
| `upsell_ids` | array | Up-sell product IDs |
| `cross_sell_ids` | array | Cross-sell product IDs |
| `parent_id` | integer | Parent product ID |
| `categories` | array | Category names (read) / IDs (write) |
| `tags` | array | Tag names (read) / IDs (write) |
| `images` | array | Product images |
| `featured_src` | string | Featured image URL (read-only) |
| `attributes` | array | Product attributes |
| `default_attributes` | array | Default variation attributes (write-only) |
| `downloads` | array | Downloadable files |
| `download_limit` | integer | Download limit |
| `download_expiry` | integer | Download expiry (days) |
| `purchase_note` | string | Post-purchase note |
| `total_sales` | integer | Total sales count (read-only) |
| `variations` | array | Product variations |
| `menu_order` | integer | Menu order for sorting |

### Dimensions

| Attribute | Type | Description |
|-----------|------|-------------|
| `length` | string | Length (decimal) |
| `width` | string | Width (decimal) |
| `height` | string | Height (decimal) |
| `unit` | string | Unit (read-only) |

### Images

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Image/attachment ID |
| `created_at` | string | Creation date (read-only) |
| `updated_at` | string | Update date (read-only) |
| `src` | string | Image URL |
| `title` | string | Image title |
| `alt` | string | Alt text |
| `position` | integer | Position (0 = featured) |

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Attribute name (required) |
| `slug` | string | Attribute slug |
| `position` | integer | Position |
| `visible` | boolean | Visible on product page |
| `variation` | boolean | Used for variations |
| `options` | array | Available term names |

### Variations

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | integer | Variation ID (read-only) |
| `sku` | string | Variation SKU |
| `global_unique_id` | string | GTIN/UPC/EAN/ISBN |
| `price` | string | Current price (read-only) |
| `regular_price` | string | Regular price |
| `sale_price` | string | Sale price |
| `managing_stock` | boolean | Stock management |
| `stock_quantity` | integer | Stock quantity |
| `in_stock` | boolean | In stock |
| `weight` | string | Weight |
| `dimensions` | array | Dimensions |
| `image` | array | Featured image (position 0) |
| `attributes` | array | Variation attributes |

## CRUD Operations

### List Products

```
GET /wp-json/wc/v3/products
GET /wp-json/wc/v3/products?per_page=100&page=1
GET /wp-json/wc/v3/products?sku=ABC-123
GET /wp-json/wc/v3/products?modified_after=2026-01-01T00:00:00Z
```

### Get Product

```
GET /wp-json/wc/v3/products/{id}
```

### Create Product

```
POST /wp-json/wc/v3/products
Content-Type: application/json

{
  "product": {
    "title": "Premium Quality",
    "type": "simple",
    "regular_price": "21.99",
    "sku": "PQ-001",
    "managing_stock": true,
    "stock_quantity": 50,
    "description": "Product description",
    "categories": [9, 14]
  }
}
```

### Update Product (inc. stock)

```
PUT /wp-json/wc/v3/products/{id}
Content-Type: application/json

{
  "product": {
    "stock_quantity": 42,
    "manage_stock": true
  }
}
```

### Sample Product Response

```json
{
  "product": {
    "title": "Premium Quality",
    "id": 546,
    "created_at": "2015-01-22T19:46:16Z",
    "type": "simple",
    "status": "publish",
    "sku": "",
    "price": "21.99",
    "regular_price": "21.99",
    "sale_price": null,
    "managing_stock": false,
    "stock_quantity": 0,
    "in_stock": true,
    "weight": null,
    "dimensions": {
      "length": "",
      "width": "",
      "height": "",
      "unit": "cm"
    },
    "description": "...",
    "short_description": "...",
    "categories": ["Clothing", "T-shirts"],
    "images": [
      {
        "id": 547,
        "src": "http://example.com/wp-content/uploads/premium-quality-front.jpg",
        "position": 0
      }
    ],
    "attributes": [],
    "variations": []
  }
}
```

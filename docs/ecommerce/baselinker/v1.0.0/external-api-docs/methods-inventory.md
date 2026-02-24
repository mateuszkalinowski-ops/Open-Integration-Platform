# BaseLinker API — Inventory Methods (Detailed)

> Source: https://api.baselinker.com/
> Fetched: 2026-02-24

---

## getInventories

Retrieve list of catalogs available in BaseLinker storage.

### Input Parameters

None.

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `inventories` | array | Array of catalog objects |

**Catalog object:**

| Field | Type | Description |
|-------|------|-------------|
| `inventory_id` | int | Catalog ID |
| `name` | varchar(100) | Catalog name |
| `description` | text | Catalog description |
| `languages` | array | Available languages |
| `default_language` | char(2) | Default language |
| `price_groups` | array | Price group IDs |
| `default_price_group` | int | Default price group ID |
| `warehouses` | array | Warehouse IDs |
| `default_warehouse` | varchar(30) | Default warehouse ID |
| `reservations` | bool | Supports reservations |
| `is_default` | bool | Is default catalog |

### Sample

```json
{
  "status": "SUCCESS",
  "inventories": [
    {
      "inventory_id": 306,
      "name": "Default",
      "description": "Default catalog",
      "languages": ["en"],
      "default_language": "en",
      "price_groups": [105],
      "default_price_group": 105,
      "warehouses": ["bl_205", "shop_2334", "warehouse_4556"],
      "default_warehouse": "bl_205",
      "reservations": false,
      "is_default": true
    }
  ]
}
```

---

## getInventoryWarehouses

Retrieve list of warehouses available in BaseLinker inventories, including auto-created
warehouses for external stocks (shops, wholesalers).

### Input Parameters

None.

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `warehouses` | array | Array of warehouse objects |

**Warehouse object:**

| Field | Type | Description |
|-------|------|-------------|
| `warehouse_type` | varchar(30) | Type: "bl", "shop", or "warehouse" |
| `warehouse_id` | int | Warehouse ID |
| `name` | varchar(100) | Warehouse name |
| `description` | text | Warehouse description |
| `stock_edition` | bool | Manual stock editing permitted |
| `is_default` | bool | Is default warehouse |

### Sample

```json
{
  "status": "SUCCESS",
  "warehouses": [
    {
      "warehouse_type": "bl",
      "warehouse_id": 205,
      "name": "Default",
      "description": "Default warehouse located in London",
      "stock_edition": true,
      "is_default": true
    }
  ]
}
```

---

## getInventoryProductsList

Retrieve basic data of products from BaseLinker catalogs. Paginated (1000 products/page).

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inventory_id` | int | Yes | Catalog ID |
| `filter_id` | int | No | Filter by product ID |
| `filter_category_id` | int | No | Filter by category |
| `filter_ean` | varchar(32) | No | Filter by EAN |
| `filter_sku` | varchar(50) | No | Filter by SKU |
| `filter_name` | varchar(200) | No | Filter by name (partial match) |
| `filter_price_from` | float | No | Min price |
| `filter_price_to` | float | No | Max price |
| `filter_stock_from` | int | No | Min stock |
| `filter_stock_to` | int | No | Max stock |
| `page` | int | No | Page number |
| `filter_sort` | varchar(30) | No | Sort: "id [ASC\|DESC]" |
| `include_variants` | bool | No | Include variants |

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `products` | array | Dict of product ID → product data |

**Product data:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Product ID |
| `parent_id` | int | Parent product ID (0 for main products) |
| `ean` | varchar(32) | EAN |
| `sku` | varchar(32) | SKU |
| `name` | varchar(200) | Product name |
| `prices` | array | Dict of price group ID → gross price |
| `stock` | array | Dict of warehouse ID → stock quantity |

### Sample

```json
// Input
{ "inventory_id": 307, "filter_id": 2685 }

// Output
{
  "status": "SUCCESS",
  "products": {
    "2685": {
      "id": 2685,
      "parent_id": 0,
      "ean": "63576363463",
      "sku": "PL53F",
      "name": "Nike PL35 shoes",
      "prices": { "105": 20.99, "106": 23.99 },
      "stock": { "bl_206": 5, "bl_207": 7 }
    }
  }
}
```

---

## getInventoryProductsData

Retrieve detailed data for selected products from BaseLinker inventory.

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inventory_id` | int | Yes | Catalog ID |
| `products` | array | Yes | Array of product IDs |
| `include_erp_units` | bool | No | Include ERP units |
| `include_wms_units` | bool | No | Include WMS units |
| `include_additional_eans` | bool | No | Include additional EANs |
| `include_suppliers` | bool | No | Include suppliers data |

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `products` | array | Dict of product ID → detailed product data |

**Product data:**

| Field | Type | Description |
|-------|------|-------------|
| `is_bundle` | bool | Is a bundle product |
| `parent_id` | int | Parent product ID (0 for main) |
| `sku` | varchar(32) | SKU |
| `ean` | varchar(32) | Primary EAN |
| `ean_additional` | array | Additional EANs (list of `{quantity, ean}`) |
| `asin` | varchar(50) | Primary ASIN |
| `tags` | array | Product tags |
| `tax_rate` | float | VAT rate |
| `weight` | float | Weight (kg) |
| `height` | float | Height (cm) |
| `width` | float | Width (cm) |
| `length` | float | Length (cm) |
| `star` | float | Star type |
| `category_id` | int | Category ID |
| `manufacturer_id` | int | Manufacturer ID |
| `prices` | array | Dict of price group ID → gross price |
| `stock` | array | Dict of warehouse ID → stock |
| `locations` | array | Dict of warehouse ID → location string |
| `text_fields` | array | Dict of text field key → value |
| `average_cost` | float | Average cost |
| `average_landed_cost` | float | Average landed cost |
| `bundle_products` | array | Products in bundle (product ID → quantity) |
| `images` | array | Dict of position (1-16) → image URL |
| `links` | array | Links with external warehouses |
| `variants` | array | Dict of variant ID → variant data |
| `stock_erp_units` | array | ERP units per warehouse |
| `stock_wms_units` | array | WMS units per warehouse |
| `suppliers` | array | Supplier data |

**Text field key format:** `[field]|[lang]|[source_id]`

- `name` — default name
- `name|de` — name in German
- `name|de|amazon_123` — name for specific Amazon account
- `description`, `features`, `description_extra1`..`4`, `extra_field_[ID]`

### Sample

```json
// Input
{ "inventory_id": "307", "products": [2685] }

// Output
{
  "status": "SUCCESS",
  "products": {
    "2685": {
      "is_bundle": false,
      "sku": "EPL-432",
      "ean": "983628103943",
      "tax_rate": 23,
      "weight": 0.25,
      "category_id": "3",
      "prices": { "105": 20.99, "106": 23.99 },
      "stock": { "bl_206": 5, "bl_207": 7 },
      "locations": { "bl_206": "A-5-2" },
      "text_fields": {
        "name": "Harry Potter and the Chamber of Secrets",
        "description": "Basic book description",
        "features": { "Cover": "Hardcover", "Pages": "300" }
      },
      "images": {
        "1": "http://upload.cdn.baselinker.com/products/23/484608.jpg"
      },
      "variants": {
        "17": {
          "name": "Special edition",
          "sku": "AGH-41",
          "ean": "5697482359144",
          "prices": { "105": 22.99 },
          "stock": { "bl_206": 3 }
        }
      }
    }
  }
}
```

---

## getInventoryProductsStock

Retrieve stock data. Paginated (1000 products/page).

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inventory_id` | int | Yes | Catalog ID |
| `page` | int | No | Page number |

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `products` | array | Dict of product ID → stock data |

**Stock data:**

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | int | Product ID |
| `stock` | array | Dict of warehouse ID → stock quantity |
| `reservations` | array | Dict of warehouse ID → reserved quantity (if enabled) |
| `variants` | array | Dict of variant ID → warehouse stock |

### Sample

```json
{
  "status": "SUCCESS",
  "products": {
    "2685": {
      "product_id": 2685,
      "stock": { "bl_206": 5, "bl_207": 7 },
      "reservations": { "bl_206": 0, "bl_207": 2 }
    }
  }
}
```

---

## updateInventoryProductsStock

Update stocks for up to 1000 products at a time.

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inventory_id` | int | Yes | Catalog ID |
| `products` | array | Yes | Dict of product/variant ID → dict of warehouse ID → stock |

Warehouse ID format: `[type:bl|shop|warehouse]_[id:int]` (e.g. `bl_123`).
Cannot assign stock to auto-created external warehouses.

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `counter` | int | Number of updated products |
| `warnings` | array | Dict of product ID → error message (only for failures) |

### Sample

```json
// Input
{
  "inventory_id": "307",
  "products": {
    "2685": { "bl_206": 5, "bl_207": 7 },
    "2687": { "bl_206": 2, "bl_207": 4 }
  }
}

// Output
{ "status": "SUCCESS", "counter": 2, "warnings": "" }
```

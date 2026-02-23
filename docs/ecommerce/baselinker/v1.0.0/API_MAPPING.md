# BaseLinker API Mapping — Pinquark Unified Schema

## Order Mapping

| Pinquark (Order) | BaseLinker (getOrders) | Notes |
|---|---|---|
| external_id | order_id | Integer → string |
| status | order_status_id | Mapped via keyword matching on status name |
| buyer.external_id | user_login or order_id | Falls back to order_id for guests |
| buyer.login | user_login | Empty for guest orders |
| buyer.email | email | |
| buyer.first_name | delivery_fullname (split) | First word |
| buyer.last_name | delivery_fullname (split) | Remaining words |
| buyer.company_name | delivery_company | |
| buyer.is_guest | !user_login | True when user_login is empty |
| delivery_address.street | delivery_address | |
| delivery_address.city | delivery_city | |
| delivery_address.postal_code | delivery_postcode | |
| delivery_address.country_code | delivery_country_code | |
| delivery_address.phone | phone | |
| invoice_address.street | invoice_address | |
| invoice_address.city | invoice_city | |
| invoice_address.postal_code | invoice_postcode | |
| invoice_address.country_code | invoice_country_code | |
| invoice_address.company_name | invoice_company | |
| total_amount | sum(products) + delivery_price | Computed |
| currency | currency | Default PLN |
| payment_type | payment_method | |
| delivery_method | delivery_method | |
| notes | user_comments | |

## Order Line Mapping

| Pinquark (OrderLine) | BaseLinker (products[]) | Notes |
|---|---|---|
| external_id | order_product_id | |
| product_id | product_id | |
| sku | sku | |
| ean | ean | |
| name | name | |
| quantity | quantity | |
| unit_price | price_brutto | Gross price |
| tax_rate | tax_rate | Percentage (e.g. 23) |

## Product Mapping

| Pinquark (Product) | BaseLinker (getInventoryProductsData) | Notes |
|---|---|---|
| external_id | product ID (dict key) | |
| sku | sku | |
| ean | ean | |
| name | text_fields.name | |
| description | text_fields.description | |
| price | prices (first value) | First price group |
| stock_quantity | stock[warehouse_id] | Sum of all warehouses if no ID specified |

## Stock Update Mapping

| Pinquark (StockItem) | BaseLinker (updateInventoryProductsStock) | Notes |
|---|---|---|
| product_id / sku | product key | |
| quantity | stock value | |
| warehouse_id | warehouse key | From account config |

## BaseLinker API Methods Used

| Pinquark Operation | BaseLinker Method | HTTP |
|---|---|---|
| fetch_orders | getOrders | POST |
| get_order | getOrders (filtered) | POST |
| update_order_status | setOrderStatus | POST |
| sync_stock | updateInventoryProductsStock | POST |
| get_product | getInventoryProductsData | POST |
| create_parcel | createPackageManual | POST |
| scraper (journal) | getJournalList | POST |
| status mapping | getOrderStatusList | POST |

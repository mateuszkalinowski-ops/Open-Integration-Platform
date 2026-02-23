# Shopify Sandbox Setup

## Development Store

Shopify provides free **development stores** for testing.

### Creating a Development Store

1. Sign up for a [Shopify Partner](https://partners.shopify.com/) account (free)
2. Go to **Stores** → **Add store** → **Create development store**
3. Choose **Create a store to test and build**
4. Name your store (e.g., `pinquark-test`)
5. The store URL will be: `pinquark-test.myshopify.com`

### Creating a Custom App

1. In your dev store, go to **Settings** → **Apps and sales channels**
2. Click **Develop apps** → **Allow custom app development**
3. Click **Create an app** → name it "pinquark Integration Test"
4. Under **Configuration** → **Admin API integration**, select these scopes:
   - `read_orders`, `write_orders`
   - `read_products`, `write_products`
   - `read_inventory`, `write_inventory`
   - `read_fulfillments`, `write_fulfillments`
   - `read_customers`
   - `read_locations`
5. Click **Install app**
6. Copy the **Admin API access token** (starts with `shpat_`)

**Important**: The access token is only shown once. Store it securely.

### Populating Test Data

Add test products and orders via:
- Shopify Admin UI
- Shopify CLI: `shopify theme dev`
- Shopify API directly

### Finding Location ID

```bash
curl -X GET "https://pinquark-test.myshopify.com/admin/api/2024-07/locations.json" \
  -H "X-Shopify-Access-Token: shpat_xxxxx"
```

### Credential Storage

Store sandbox credentials in CI/CD secrets:
- `SHOPIFY_SANDBOX_SHOP_URL`
- `SHOPIFY_SANDBOX_ACCESS_TOKEN`
- `SHOPIFY_SANDBOX_LOCATION_ID`

**Never** commit access tokens to the repository.

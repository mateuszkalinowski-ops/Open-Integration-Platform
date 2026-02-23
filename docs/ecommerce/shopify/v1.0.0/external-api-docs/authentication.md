# Shopify Authentication

Source: https://shopify.dev/docs/api/usage/authentication

## Custom App Access (used by this connector)

Custom apps provide a permanent **Admin API access token** for accessing the store's data.

### Creating a Custom App

1. Go to Shopify Admin → **Settings** → **Apps and sales channels**
2. Click **Develop apps** → **Allow custom app development**
3. Click **Create an app** → Name it
4. Under **Configuration** → **Admin API integration**:
   - Select required scopes
   - Click **Save**
5. Click **Install app**
6. Copy the **Admin API access token** (shown only once)

### Token Properties

- **Format**: `shpat_` prefix + alphanumeric string
- **Lifetime**: Permanent (does not expire)
- **Rotation**: Cannot be rotated without reinstalling the app
- **Scope**: Defined at app creation time, can be modified

### Using the Token

Include in every API request as a header:

```http
X-Shopify-Access-Token: shpat_xxxxx
```

### Required Scopes for This Connector

| Scope | Purpose |
|---|---|
| `read_orders` | Fetch orders |
| `write_orders` | Update order status (cancel, close, open) |
| `read_products` | Fetch products |
| `write_products` | Create/update products |
| `read_inventory` | Read inventory levels |
| `write_inventory` | Set inventory levels |
| `read_fulfillments` | Read fulfillments |
| `write_fulfillments` | Create fulfillments, update tracking |
| `read_customers` | Read customer data (from orders) |
| `read_locations` | List locations (for inventory) |

### Optional Scopes

| Scope | Purpose |
|---|---|
| `read_all_orders` | Access orders older than 60 days |

## OAuth2 (for public/partner apps)

Public Shopify apps use the OAuth2 Authorization Code Grant flow:

1. Redirect merchant to: `https://{shop}.myshopify.com/admin/oauth/authorize?client_id={api_key}&scope={scopes}&redirect_uri={redirect_uri}`
2. Merchant approves permissions
3. Shopify redirects to `redirect_uri` with `code` parameter
4. Exchange code for permanent access token via POST to `https://{shop}.myshopify.com/admin/oauth/access_token`

**Note**: This connector uses the Custom App approach (access token from config),
not the OAuth2 flow. OAuth2 support may be added in a future version for multi-store
SaaS deployments.

## Security Considerations

- Access tokens should be treated as secrets — never commit to repositories
- Store tokens in encrypted form (AES-256-GCM) when persisted
- Use separate Custom Apps per environment (production, sandbox)
- Request only the minimum required scopes
- Monitor Shopify Partner Dashboard for token usage alerts

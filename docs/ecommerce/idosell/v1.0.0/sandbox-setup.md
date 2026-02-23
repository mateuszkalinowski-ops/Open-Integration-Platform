# Sandbox Setup — IdoSell

## Overview

IdoSell provides test/demo panels for development and testing. All merchants run the same system version, so the sandbox environment is functionally identical to production.

## Setting Up a Test Panel

### Option 1: Demo/Test Account

1. Go to https://www.idosell.com
2. Request a demo account or contact IdoSell sales
3. You will receive a panel URL like `https://clientXXXXX.idosell.com`

### Option 2: Development Partner Account

1. Register as a development partner at https://www.idosell.com/en/developers/
2. Request access to a development panel
3. Development panels have the same API access as production

## Generating API Key

1. Log in to the IdoSell administration panel
2. Navigate to: **Administration → API → Access Keys for Admin API**
3. Click "Generate new key"
4. Copy the API key and store it securely
5. The key has full access to all API endpoints

## Configuring the Integrator

Create `config/accounts.yaml`:

```yaml
accounts:
  - name: sandbox
    shop_url: "https://clientXXXXX.idosell.com"
    api_key: "your_generated_api_key"
    api_version: "v6"
    default_stock_id: 1
    environment: sandbox
```

Or use environment variables:

```bash
IDOSELL_ACCOUNT_0_NAME=sandbox
IDOSELL_ACCOUNT_0_SHOP_URL=https://clientXXXXX.idosell.com
IDOSELL_ACCOUNT_0_API_KEY=your_generated_api_key
```

## Verifying the Setup

```bash
# Start the integrator
docker compose --profile dev up -d

# Validate API key
curl -X POST http://localhost:8000/auth/sandbox/validate

# List orders
curl "http://localhost:8000/orders?account_name=sandbox"
```

## Test Data

Create test data in the IdoSell admin panel:
- Add test products with SKU codes
- Create test orders
- Set up warehouse stocks

## Important Notes

- IdoSell does not have a separate sandbox API URL — the same panel URL is used
- Monthly API quota applies even in test panels (100k calls for Smart CLOUD)
- Keep scraping intervals reasonable (120s+) to avoid quota exhaustion
- There is no separate "test mode" flag — all operations are real

# Sandbox Setup — Shoper

## Creating a Test Account

1. Go to https://www.shoper.pl and create a free test account (14-day trial)
2. After registration, you will receive your test shop URL, e.g. `https://yourshop-123456.shoparena.pl`
3. Log in to the admin panel

## API Access Credentials

Shoper WebAPI uses the same login credentials as the admin panel:

- **Shop URL**: Your shop URL (e.g. `https://yourshop-123456.shoparena.pl`)
- **Login**: administrator login
- **Password**: administrator password

## Integrator Configuration

1. Copy `.env.example` to `.env`
2. Create `config/accounts.yaml`:

```yaml
accounts:
  - name: sandbox
    shop_url: "https://yourshop-123456.shoparena.pl"
    login: "your-login"
    password: "your-password"
    language_id: "pl_PL"
    environment: sandbox
```

3. Start the integrator: `docker compose up -d`

## Verification

```bash
# Check health
curl http://localhost:8000/health

# Check authentication status
curl http://localhost:8000/auth/sandbox/status

# Fetch orders
curl "http://localhost:8000/orders?account_name=sandbox"
```

## Notes

- The trial account expires after 14 days
- API rate limit: no official documentation, recommended max 60 req/min
- Test data: after creating a shop, sample products and categories are automatically generated

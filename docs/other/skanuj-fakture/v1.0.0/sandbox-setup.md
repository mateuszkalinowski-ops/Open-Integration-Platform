# Sandbox Setup — SkanujFakture

## Test Account

SkanujFakture.pl offers a free starter plan ("Start") allowing you to test the system:
- 250 documents included in the plan
- 7 days of availability

### Registration

1. Go to: https://skanujfakture.pl:8443/skanujfakture/#/
2. Register a new account providing company details
3. Activate the account via the email link

### Integrator Configuration

After registration, set the login credentials in `config/accounts.yaml`:

```yaml
accounts:
  - name: sandbox
    login: "your-email@example.com"
    password: "your-password"
    api_url: "https://skanujfakture.pl:8443/SFApi"
    environment: sandbox
```

Or via environment variables:

```bash
SF_ACCOUNT_0_NAME=sandbox
SF_ACCOUNT_0_LOGIN=your-email@example.com
SF_ACCOUNT_0_PASSWORD=your-password
SF_ACCOUNT_0_ENVIRONMENT=sandbox
```

### Connection Verification

```bash
curl http://localhost:8000/connection/sandbox/status
```

Expected response:
```json
{
  "account_name": "sandbox",
  "connected": true,
  "companies_count": 1
}
```

## Notes

- SkanujFakture does not have a separate sandbox environment — testing is done on an account with the starter plan
- Test documents can be deleted after testing is complete
- The API is available on non-standard port 8443 (HTTPS)
- Support contact: tel. 451 087 052 or form at https://skanujfakture.pl/kontakt

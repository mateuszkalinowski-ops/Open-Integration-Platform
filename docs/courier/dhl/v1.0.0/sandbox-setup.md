# DHL Sandbox Setup — v1.0.0

## Sandbox Environment

- **WSDL URL**: `https://sandbox.dhl24.com.pl/webapi2`
- **ServicePoint WSDL URL**: `https://sandbox.dhl24.com.pl/servicepoint`
- **Portal**: `https://sandbox.dhl24.com.pl`

## Test Account

| Field | Value |
|-------|-------|
| Username (email) | `your-email@example.com` |
| Password | Stored in CI/CD secrets as `DHL_SANDBOX_PASSWORD` |
| Account created | 2026-02-21 |

> **Security note**: The password is stored in the `.env` file locally (gitignored) and in CI/CD secrets for automated testing. Never commit credentials to the repository.

## How to Set Up

1. Go to `https://sandbox.dhl24.com.pl` and log in with the test credentials
2. Note the SAP number and account number from the portal dashboard (needed for some operations)
3. Copy `.env.example` to `.env` and ensure WSDL URLs point to sandbox
4. Pass credentials in each API request via the `credentials` field

## API Authentication

DHL uses per-request credentials via the `AuthData` SOAP structure:

```json
{
  "credentials": {
    "username": "your-email@example.com",
    "password": "***",
    "account_number": "",
    "sap_number": ""
  }
}
```

## Testing Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get service points
curl "http://localhost:8000/points?username=your-email@example.com&password=***&city=Warszawa&postal_code=00-001"

# Create shipment (POST /shipments with JSON body)
# Get label (POST /labels with JSON body)
# Get status (GET /shipments/{waybill}/status?username=...&password=...)
```

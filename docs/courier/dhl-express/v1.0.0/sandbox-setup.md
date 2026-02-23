# DHL Express Sandbox Setup — v1.0.0

## Developer Portal Account

| Field | Value |
|-------|-------|
| Portal | https://developer.dhl.com |
| Email | `your-email@example.com` |
| Password | Stored in CI/CD secrets as `DHL_EXPRESS_PORTAL_PASSWORD` |

## Getting API Credentials

1. Log in at https://developer.dhl.com
2. Navigate to "My Apps" or visit https://developer.dhl.com/user/apps
3. Click "Create App" (or go to https://developer.dhl.com/user/200671/create-app)
4. Select "DHL Express - MyDHL API"
5. Fill in the app details and submit
6. Once approved, you'll receive an **API Key** and **API Secret**
7. Save them in the `.env` file:
   ```
   DHL_EXPRESS_API_KEY=your-api-key
   DHL_EXPRESS_API_SECRET=your-api-secret
   ```

## Test Environment

- **Base URL**: `https://express.api.dhl.com/mydhlapi/test`
- **Daily limit**: 500 API calls
- **Auth**: Basic Auth with `Authorization: Basic <Base64(KEY:SECRET)>`

## Testing

```bash
# Health check
curl http://localhost:8001/health

# Validate address capability
curl "http://localhost:8001/address-validate?countryCode=PL&postalCode=00-001&cityName=Warszawa"

# Get rates
curl -X POST http://localhost:8001/rates \
  -H "Content-Type: application/json" \
  -d '{
    "shipperCountryCode": "PL",
    "shipperPostalCode": "00-001",
    "shipperCity": "Warszawa",
    "receiverCountryCode": "DE",
    "receiverPostalCode": "10115",
    "receiverCity": "Berlin",
    "plannedShippingDate": "2026-02-25T10:00:00 GMT+01:00",
    "weight": 2.5,
    "length": 30,
    "width": 20,
    "height": 15,
    "unitOfMeasurement": "metric",
    "isCustomsDeclarable": false
  }'
```

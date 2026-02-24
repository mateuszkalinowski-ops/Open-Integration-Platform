# Apilo Sandbox Setup

## Creating a Test Account

1. Register at [https://apilo.com](https://apilo.com) for a trial/demo account
2. Navigate to **Administracja** > **API Apilo**
3. Create a new API application to obtain:
   - Client ID
   - Client Secret
   - Authorization Code

## API Documentation

- Official docs: [https://developer.apilo.com/api/](https://developer.apilo.com/api/)
- OpenAPI spec: [https://developer.apilo.com/uploads/apilo/swagger.json](https://developer.apilo.com/uploads/apilo/swagger.json)

## Authentication Flow

1. Use Basic Auth with `Client ID:Client Secret` (base64-encoded)
2. POST to `/rest/auth/token/` with `grantType: "authorization_code"` and the authorization code
3. Receive `accessToken` (valid 21 days) and `refreshToken` (valid 2 months)
4. Use `Authorization: Bearer {accessToken}` for all API calls
5. Before token expiry, refresh using `grantType: "refresh_token"`

## Rate Limits

- **150 requests per minute** across all endpoints
- HTTP 429 response on limit exceeded

## Testing Configuration

```yaml
accounts:
  - name: sandbox
    client_id: "your-sandbox-client-id"
    client_secret: "your-sandbox-client-secret"
    authorization_code: "your-sandbox-auth-code"
    base_url: "https://app.apilo.com"
    environment: sandbox
```

## Known Sandbox Limitations

- Demo accounts may have limited data and API access
- Some operations may be restricted in trial mode
- Rate limits apply equally to sandbox and production

# Allegro Sandbox Setup

## 1. Create Allegro Developer Account

1. Go to https://developer.allegro.pl.allegrosandbox.pl/
2. Register a new account (or use existing Allegro sandbox credentials)
3. Verify your email address

## 2. Create an Application

1. Log in to https://apps.developer.allegro.pl.allegrosandbox.pl/
2. Click "Register new application"
3. Fill in:
   - **Application name**: `pinquark WMS Integration (Sandbox)`
   - **Application description**: WMS integration for order management
   - **Application URL**: `http://localhost:8000`
   - **Redirect URI**: `http://localhost:8000/callback` (not used for device flow, but required)
4. Copy the **Client ID** and **Client Secret**

## 3. Configure the Integrator

Edit `config/accounts.yaml`:

```yaml
accounts:
  - name: sandbox
    client_id: "PASTE_CLIENT_ID_HERE"
    client_secret: "PASTE_CLIENT_SECRET_HERE"
    api_url: "https://api.allegro.pl.allegrosandbox.pl"
    auth_url: "https://allegro.pl.allegrosandbox.pl/auth/oauth"
    environment: sandbox
```

## 4. Authenticate

1. Start the integrator: `docker compose --profile dev up allegro-integrator-dev`
2. Start device flow:
   ```bash
   curl -X POST http://localhost:8000/auth/sandbox/device-code
   ```
3. Open the `verification_uri_complete` from the response in your browser
4. Log in to Allegro sandbox and confirm access
5. Poll for the token:
   ```bash
   curl -X POST http://localhost:8000/auth/sandbox/poll-token
   ```

## 5. Create Test Data

In the Allegro sandbox:
1. Create a few test offers at https://allegro.pl.allegrosandbox.pl/
2. Place test orders using a second sandbox account
3. The scraper will automatically pick up new orders

## Sandbox vs Production URLs

| Component | Sandbox | Production |
|-----------|---------|------------|
| API | `https://api.allegro.pl.allegrosandbox.pl` | `https://api.allegro.pl` |
| Auth | `https://allegro.pl.allegrosandbox.pl/auth/oauth` | `https://allegro.pl/auth/oauth` |
| Web | `https://allegro.pl.allegrosandbox.pl` | `https://allegro.pl` |
| Developer portal | `https://developer.allegro.pl.allegrosandbox.pl` | `https://developer.allegro.pl` |

## Rate Limits

| Environment | Requests per second | Requests per minute |
|-------------|--------------------|--------------------|
| Sandbox | 10 | 600 |
| Production | 9000/min per user | Varies by endpoint |

The integrator handles 429 responses automatically with `Retry-After` header backoff.

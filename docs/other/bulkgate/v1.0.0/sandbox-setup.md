# BulkGate SMS Gateway — Sandbox Setup

## Creating a Test Account

BulkGate provides a free trial with credits that can be used for testing.

### Steps

1. **Register** at [BulkGate Portal](https://portal.bulkgate.com/sign/up)
2. After registration, you receive a small amount of free credits for testing
3. Navigate to **Modules & APIs** in the left sidebar
4. Click **Create API**
5. Select **HTTP Simple API** or **HTTP Advanced API**
6. Note the displayed `Application ID` and `Application Token`
7. These credentials are used for all API calls

### API Token Management

- Each API instance has its own `application_id` and `application_token`
- Tokens can be regenerated in the portal under the specific API settings
- Multiple APIs can be created under one account
- See [API token documentation](https://help.bulkgate.com/docs/en/api-tokens.html)

### Testing Recommendations

- Use your own phone number as a recipient for transactional SMS testing
- For bulk SMS testing, use a small list of opted-in numbers
- BulkGate has no dedicated sandbox environment — all API calls use the production endpoint
- Be aware that test messages consume credits (even free credits)
- Use the `tag` field to label test messages for easy identification in the portal
- Enable `duplicates_check` during testing to avoid accidental duplicate sends

### Delivery Reports

To test delivery report webhooks:
1. In BulkGate Portal, go to your API settings
2. In **Delivery reports** section, click the **+** button
3. Enter your webhook URL (e.g., `https://your-domain/webhooks/delivery-report`)
4. Optionally enable "Report only when error occurs" or "Bulk DLRs"
5. Click **Save**

For local development, use a tunneling tool (ngrok, localtunnel) to expose your local webhook endpoint.

### Rate Limits

- BulkGate applies rate limits based on your account tier
- Free/trial accounts have lower throughput limits
- Contact BulkGate support for specific rate limit information
- The connector implements retry with exponential backoff for transient errors

### Credential Storage

Store sandbox credentials in CI/CD secrets:

```
BULKGATE_TEST_APPLICATION_ID=<your-test-app-id>
BULKGATE_TEST_APPLICATION_TOKEN=<your-test-token>
```

**Never** commit credentials to the repository.

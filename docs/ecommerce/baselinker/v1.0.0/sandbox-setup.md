# BaseLinker Sandbox Setup

## Account Registration

1. Sign up for a BaseLinker account at https://baselinker.com
2. BaseLinker offers a **14-day free trial** that can be used as a sandbox
3. After registration, go to **Account & other → My account → API**
4. Generate a new API token
5. Store the token in your environment variables or `config/accounts.yaml`

## API Testing

BaseLinker provides an API tester at https://api.baselinker.com/?tester where you can test individual methods with your token.

## Rate Limits

- API rate limit: **100 requests per minute**
- The integrator handles 429 responses with automatic backoff
- For testing, keep the scraping interval above 60 seconds

## Test Data

1. Create a few test orders manually in the BaseLinker panel
2. Set up at least one inventory (catalog) with test products
3. Create custom order statuses that match the expected keywords (see README.md)
4. Configure a warehouse for stock operations

## Credentials Storage

Store sandbox credentials in CI/CD secrets:

```
BASELINKER_API_TOKEN=your-sandbox-token
```

Never commit tokens to the repository.

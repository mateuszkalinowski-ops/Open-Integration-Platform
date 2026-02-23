# IdoSell API — Webhooks

## Support

IdoSell supports webhooks as a push notification mechanism. Configuration is done via the admin panel.

## Supported Events

- Order placed (new order created)
- Order status changed
- Cart/basket edited
- Customer registered
- Newsletter subscription

## Configuration

Webhooks are configured in the IdoSell admin panel under the API settings section. Detailed payload formats and retry policies are not publicly documented.

## Current Integration Approach

This integrator uses **polling** (scheduled scraping) instead of webhooks:
- Orders are polled every 120 seconds (configurable)
- The `modified` date type filter catches both new and updated orders
- Scraper state is persisted in SQLite to avoid duplicate processing

### Why polling over webhooks

1. Webhook payload format is not publicly documented
2. Polling provides more control over data flow
3. Webhook configuration requires manual setup in each IdoSell panel
4. Polling is resilient to temporary connectivity issues

## Future Consideration

When IdoSell publishes detailed webhook specifications, this integrator could be extended with a webhook receiver endpoint for real-time event processing.

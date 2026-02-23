# Known Issues & Limitations

## v1.0.0

### WooCommerce API Limitations

1. **Pagination limit**: WooCommerce REST API returns a maximum of 100 items per page (`per_page` max is 100). Large catalogs require paginated fetching.
2. **No webhook support yet**: This version uses polling (scraping) to detect new/modified orders. Webhook support for real-time event notifications is planned for v1.1.0.
3. **Variable products**: Stock sync updates the main product's stock quantity. Variation-level stock management requires fetching and updating individual variations, which is planned for v1.1.0.
4. **Rate limiting**: WooCommerce does not have standardized rate limits — they depend on the hosting provider. The connector respects `429` responses with `Retry-After` headers.
5. **OAuth 1.0a over HTTP**: OAuth 1.0a authentication is used for non-HTTPS connections. It is strongly recommended to use HTTPS in production for security.

### Known Workarounds

1. **Large order volumes**: If the store has very large order volumes, increase `WOOCOMMERCE_SCRAPING_INTERVAL_SECONDS` and `default_per_page` to balance between data freshness and API load.
2. **Custom order statuses**: WooCommerce plugins may add custom order statuses (e.g., `shipped`, `awaiting-pickup`). These are not mapped by default and will fall back to `NEW`. Custom mappings can be added to the mapper.
3. **Multi-site WordPress**: Each site in a WordPress multisite installation requires a separate account configuration with its own API keys.


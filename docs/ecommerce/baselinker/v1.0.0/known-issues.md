# Known Issues — BaseLinker v1.0.0

## 1. Single POST endpoint

BaseLinker's entire API uses a single POST endpoint (`connector.php`). Unlike RESTful APIs, there are no separate paths for different resources. This means all operations share the same rate limit bucket.

## 2. Custom order statuses

BaseLinker has no fixed order status IDs — they are custom per account. The integrator maps status names to unified statuses using keyword matching. If a customer uses non-standard status names (e.g., in English or with unusual wording), the mapping may default to PROCESSING.

**Workaround**: The customer should ensure their BaseLinker statuses contain recognizable keywords (see README.md for the keyword list).

## 3. getOrders returns max 100 orders

The `getOrders` method returns at most 100 orders per call. For accounts with high order volume, pagination is done by incrementing `date_confirmed_from`. The scraper uses `getJournalList` for efficient change detection instead.

## 4. getJournalList availability

The `getJournalList` method may not be enabled by default on all BaseLinker accounts. If the scraper receives empty responses, the user should enable it in their BaseLinker panel API settings.

## 5. Rate limit (100 req/min)

The 100 req/min limit is shared across all API consumers using the same token. If other integrations or BaseLinker apps use the same token, the effective rate for this integrator is lower.

**Workaround**: Use a dedicated API token for the Pinquark integration.

## 6. Stock sync requires inventory_id

Stock operations require a configured `inventory_id` (BaseLinker catalog ID). If not set, stock sync will fail with a descriptive error.

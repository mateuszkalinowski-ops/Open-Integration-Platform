# Known Issues — Slack v1.0.0

## Limitations

1. **No Socket Mode support** — the connector uses HTTP polling, not WebSocket-based Socket Mode. The `app_token` field is reserved for future Socket Mode integration.

2. **No Event Subscriptions API** — incoming events are detected via polling `conversations.history`, not via Slack's Events API (which requires a public URL with SSL). For real-time events, consider deploying behind a reverse proxy with a public endpoint.

3. **File upload size** — files uploaded via the API are sent as base64-encoded strings in the request body. Very large files (>50 MB) may cause timeouts. Use the Slack UI for large file uploads.

4. **User name cache** — user name resolution is cached in memory only. Cache is lost on container restart. No TTL is applied to cached entries.

5. **Channel membership** — the poller only monitors channels where the bot is a member. The bot must be invited to private channels manually.

6. **Thread replies** — the poller fetches top-level messages only. Thread replies are not polled separately. Use `conversations.replies` (not yet implemented) for thread monitoring.

## Workarounds

- For real-time events: reduce `SLACK_POLLING_INTERVAL_SECONDS` to `5` (but respect rate limits).
- For large file uploads: upload to an external storage and share the URL via `message.send`.

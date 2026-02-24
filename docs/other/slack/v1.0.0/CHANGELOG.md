# Changelog

## [1.0.0] - 2026-02-23

### Added
- Initial Slack connector implementation
- Send messages to channels and threads (`chat.postMessage`)
- Fetch channel message history (`conversations.history`)
- List channels (`conversations.list`)
- Upload files (`files.upload`)
- Add emoji reactions (`reactions.add`)
- Multi-workspace support via account configuration
- Background message polling with configurable interval
- User name resolution with in-memory caching
- Kafka event publishing for `message.received` events
- Prometheus metrics for API call tracking
- SQLite-backed poller state persistence
- Health and readiness endpoints
- Swagger UI documentation at `/docs`

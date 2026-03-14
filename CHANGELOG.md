# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 35 connectors: 18 courier, 8 e-commerce, 1 ERP, 1 WMS, 1 AI, 6 other
- Flow Engine with any-to-any event routing
- Workflow Engine with 18 node types (DAG-based visual builder)
- Visual field mapper with drag-and-drop
- Credential Vault with AES-256-GCM encryption
- 3-tier Verification Agent (health, auth, functional)
- On-premise agent for InsERT Nexo ERP
- Angular dashboard (standalone + embeddable `@pinquark/integrations` library)
- Python SDK (`pinquark-sdk`)
- OAuth2 lifecycle management with auto-refresh
- Per-connector rate limiting (token bucket)
- Connector version isolation (multiple versions coexist)
- Row-Level Security for multi-tenant isolation
- Workflow sync state tracking with deduplication
- AI-powered workflow generation and field mapping suggestions

### Security
- Removed ADMIN_SECRET from frontend JavaScript bundle
- Removed API key authentication via query string parameters
- Migrated courier connector credentials from query params to HTTP headers
- Removed default password fallbacks from production Docker Compose files
- Bound PostgreSQL and Redis to localhost in production compose
- Removed hardcoded CORS wildcard from VPS deployment
- Removed PII from error log messages
- Added SECURITY.md with vulnerability reporting policy

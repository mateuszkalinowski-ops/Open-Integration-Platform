# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| latest  | Yes                |
| < 1.0.0 | Best effort        |

## Reporting a Vulnerability

If you discover a security vulnerability in the Open Integration Platform, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email: **security@pinquark.com**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: within 48 hours
- **Initial assessment**: within 5 business days
- **Fix or mitigation**: depends on severity, typically within 30 days for critical issues

## Security Best Practices for Self-hosted Deployments

1. **Always run `setup.sh`** to generate unique, random secrets. Never use default or example values in production.
2. **Back up your `ENCRYPTION_KEY`** — if lost, all stored credentials become permanently unreadable.
3. **Do not expose PostgreSQL or Redis ports** to the public network. The default `docker-compose.prod.yml` binds them to `127.0.0.1`.
4. **Use a reverse proxy** (nginx, Traefik) with TLS for all external traffic.
5. **Set `CORS_ALLOWED_ORIGINS`** to your specific domain(s). Do not use `*` in production.
6. **Keep `ADMIN_SECRET` private** — it is not injected into the dashboard frontend. Enter it via the session prompt when admin features are needed.
7. **Rotate secrets periodically** — API keys, JWT secrets, and admin secrets can be rotated without data loss. `ENCRYPTION_KEY` must NOT be changed without re-encrypting all stored credentials.

## Credential Storage

All external system credentials are encrypted at rest using AES-256-GCM with per-tenant envelope encryption. The encryption key is derived from the `ENCRYPTION_KEY` environment variable and never logged or exposed via API responses.

## Network Architecture

- Connectors communicate with the platform via an internal Docker network
- Only the API Gateway and Dashboard are exposed externally
- `/internal/*` endpoints are protected by `INTERNAL_SECRET` header authentication
- Row-Level Security (RLS) enforces tenant isolation at the PostgreSQL level

# Known Issues — Apilo Integrator v1.0.0

## Status ID Mapping

Apilo order statuses use configurable integer IDs that vary per account. The integrator maps statuses by name heuristics rather than fixed IDs. If a customer uses non-standard status names, the mapping may default to `NEW`. The `/maps` endpoint provides the actual status map for the account.

## Date Format

Apilo uses ISO 8601 dates with timezone offsets (e.g., `2024-09-12T08:16:32+02:00`). When passing dates as URL parameters, the `+` sign must be URL-encoded as `%2B` to avoid being interpreted as a space. The client handles this encoding automatically.

## Product Update Constraints

- The `id` and `originalCode` fields cannot be changed via PUT update
- Product updates are limited to 128 items per request
- PATCH updates are limited to 512 items per request

## Encrypted Orders

Some orders may have `isEncrypted: true`, meaning customer data fields are encrypted by Apilo and not directly readable via the API.

## Media Upload

Media attachments support only: `application/pdf`, `image/jpeg`, `image/png`, `image/gif`, `image/webp`. Other file types will return HTTP 415.

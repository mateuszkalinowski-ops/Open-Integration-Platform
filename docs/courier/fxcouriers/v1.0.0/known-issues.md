# FX Couriers — Known Issues

## Limitations

1. **No sandbox environment** — All API calls go directly to production. Use mocked tests for CI/CD.

2. **Pagination limit** — The `/orders` endpoint returns a maximum of 100 orders per call. Use the `offset` parameter for pagination.

3. **Order deletion constraints** — Orders can only be deleted before a pickup (shipment) is scheduled for them.

4. **Label availability** — Label PDF generation may not be available for orders in `NEW` or `WAITING_APPROVAL` status.

5. **Static authentication** — Bearer tokens are static (no OAuth refresh flow). Token rotation requires manual coordination with FX Couriers support.

6. **No webhook support** — FX Couriers API does not provide webhooks for status change notifications. Status polling is required.

## Workarounds

- **Status polling**: Implement a periodic job (e.g., every 5 minutes) to poll `/orders` and detect status changes.
- **Service caching**: Call `GET /services` once daily and cache the response locally, as recommended by FX Couriers.

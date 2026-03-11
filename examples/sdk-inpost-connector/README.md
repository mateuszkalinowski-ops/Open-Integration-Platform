# InPost Connector (SDK Example)

A compact example showing how to build the InPost courier connector using the Pinquark Connector SDK. This serves as both a working reference and documentation for SDK usage.

## What This Demonstrates

- **Config class** — `required_credentials`, `rate_limits`, `port`
- **@action decorators** — `shipment.create`, `label.get`, `shipment.status`, `pickup_points.list`, `shipment.cancel`
- **@trigger decorator** — Polling `shipment.status_changed` every 300 seconds
- **test_connection()** — Overridden to validate API connectivity using stored account credentials
- **self.http** — `ConnectorHttpClient` for external API calls (retries, circuit breaker, metrics)
- **Credential handling** — Reading `organization_id`, `access_token`, `sandbox_mode` from payload or accounts

## Running the Example

Requires Python 3.12+.

```bash
cd examples/sdk-inpost-connector
pip install ../../sdk/python/pinquark_connector_sdk
python main.py
```

Alternatively, install SDK dependencies and run with `PYTHONPATH`:

```bash
pip install fastapi uvicorn httpx pydantic pydantic-settings prometheus-client structlog
PYTHONPATH=../../sdk/python python main.py
```

The connector starts on port 8000 with `/health`, `/readiness`, `/accounts`, `/docs`, and action routes at `/actions/{action}/{path}`.

## Mapping to Traditional Connector Structure

| Traditional (FastAPI)      | SDK (ConnectorApp)                    |
|----------------------------|--------------------------------------|
| Manual route registration  | `@action("shipment.create")`         |
| Separate integration class | Inline logic using `self.http`       |
| Custom health/readiness    | Auto-generated via `register_health_routes` |
| Credentials in request     | Injected into payload by platform    |
| Background polling logic   | `@trigger("event", interval_seconds=300)` |

## Action Endpoints

- `POST /actions/shipment/create` — Create shipment
- `POST /actions/label/get` — Get label (payload: `shipment_id`, optional `format`)
- `POST /actions/shipment/status` — Get shipment status (payload: `tracking_number` or `shipment_id`)
- `POST /actions/pickup_points/list` — List pickup points (payload: optional `city`, `zip_code`)
- `POST /actions/shipment/cancel` — Cancel shipment (payload: `shipment_id`)

## Testing Connection

Provisions an account and checks connectivity:

```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name":"default","credentials":{"organization_id":"org","access_token":"token","sandbox_mode":true}}'

curl http://localhost:8000/connection/default/status
```

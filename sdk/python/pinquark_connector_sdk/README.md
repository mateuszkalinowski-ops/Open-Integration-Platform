# Pinquark Connector SDK

A Python framework for building connectors for the **Open Integration Platform**.

## Installation

```bash
pip install pinquark-connector-sdk
```

## Quick Start

```python
from pinquark_connector_sdk import ConnectorApp, action

class MyConnector(ConnectorApp):
    name = "my-connector"
    category = "other"
    version = "1.0.0"
    display_name = "My Connector"
    description = "Example connector"

    class Config:
        required_credentials = ["api_key"]

    @action("data.fetch")
    async def fetch_data(self, payload: dict) -> dict:
        resp = await self.http.get("https://api.example.com/data")
        return resp.json()

connector = MyConnector()
```

Run:

```bash
python main.py
```

Or with uvicorn directly (the underlying FastAPI app is `connector._fastapi`):

```bash
uvicorn main:connector._fastapi --host 0.0.0.0 --port 8000
```

The recommended way is to use the built-in runner:

```python
if __name__ == "__main__":
    MyConnector().run()
```

## Features

- **Declarative** `@action`, `@trigger`, `@webhook` decorators
- **Auto-generated** health, readiness, metrics, and account endpoints
- **Built-in HTTP client** with circuit breakers, retries, and Prometheus metrics
- **OAuth2 manager** for token lifecycle
- **Test utilities** for writing connector tests

## Example

See `examples/sdk-inpost-connector/` for a full InPost courier connector built with the SDK.

## License

Apache 2.0

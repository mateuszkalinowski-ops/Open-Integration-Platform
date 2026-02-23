# Creating a Custom Connector

This guide walks through creating a new connector for the Open Integration Platform by Pinquark.com.

## 1. Copy the template

```bash
cp -r integrators/courier/_template integrators/ecommerce/my-shop/v1.0.0
cd integrators/ecommerce/my-shop/v1.0.0
```

## 2. Create connector.yaml

```yaml
name: my-shop
category: ecommerce
version: 1.0.0
display_name: "My Shop"
description: "Custom integration with My Shop API"
interface: ecommerce
capabilities:
  - fetch_orders
  - sync_stock
events:
  - order.created
  - order.status_changed
actions:
  - order.fetch
  - stock.sync
config_schema:
  required:
    - api_key
    - shop_url
  optional:
    - sandbox_mode
health_endpoint: /health
docs_url: /docs
```

## 3. Implement the integration

```python
# src/integration.py
from pinquark_common.interfaces import Connector, EventDescriptor, ActionDescriptor, ActionResult


class MyShopIntegration(Connector):
    def __init__(self, api_key: str, shop_url: str) -> None:
        self._api_key = api_key
        self._shop_url = shop_url

    def get_connector_name(self) -> str:
        return "my-shop"

    def get_connector_version(self) -> str:
        return "1.0.0"

    def get_supported_events(self) -> list[EventDescriptor]:
        return [
            EventDescriptor("order.created", "New order placed in My Shop"),
            EventDescriptor("order.status_changed", "Order status updated"),
        ]

    def get_supported_actions(self) -> list[ActionDescriptor]:
        return [
            ActionDescriptor("order.fetch", "Fetch orders from My Shop"),
            ActionDescriptor("stock.sync", "Sync stock levels to My Shop"),
        ]

    async def execute_action(self, action: str, payload: dict) -> ActionResult:
        if action == "order.fetch":
            orders = await self._fetch_orders(payload)
            return ActionResult(success=True, data={"orders": orders})
        elif action == "stock.sync":
            result = await self._sync_stock(payload)
            return ActionResult(success=True, data=result)
        return ActionResult(success=False, error=f"Unknown action: {action}")

    async def _fetch_orders(self, payload: dict) -> list:
        # Implement API call to My Shop
        ...

    async def _sync_stock(self, payload: dict) -> dict:
        # Implement stock sync to My Shop
        ...
```

## 4. Create the FastAPI app

```python
# src/app.py
from fastapi import FastAPI

app = FastAPI(title="My Shop Connector", version="1.0.0")
integration = MyShopIntegration(api_key="...", shop_url="...")

@app.get("/health")
async def health():
    return await integration.health_check()
```

## 5. Write tests

```python
# tests/test_integration.py
import pytest
from src.integration import MyShopIntegration

@pytest.fixture
def integration():
    return MyShopIntegration(api_key="test", shop_url="https://test.shop")

@pytest.mark.asyncio
async def test_get_connector_name(integration):
    assert integration.get_connector_name() == "my-shop"

@pytest.mark.asyncio
async def test_supported_events(integration):
    events = integration.get_supported_events()
    assert len(events) == 2
    assert events[0].name == "order.created"
```

## 6. Build and test

```bash
docker build -t connector-my-shop:dev .
docker run --rm -p 8000:8000 connector-my-shop:dev
curl http://localhost:8000/health
```

The platform will auto-discover your connector via `connector.yaml` on next restart.

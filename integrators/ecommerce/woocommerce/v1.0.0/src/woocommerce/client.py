"""Low-level WooCommerce REST API client with retry and rate-limit handling."""

import asyncio
import logging
import time
from typing import Any

import httpx

from src.config import settings
from src.woocommerce.auth import WooCommerceAuth
from pinquark_common.monitoring.metrics import setup_metrics

logger = logging.getLogger(__name__)

metrics = setup_metrics("woocommerce")


class WooCommerceApiError(Exception):
    def __init__(self, status_code: int, message: str, raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}
        super().__init__(f"WooCommerce API {status_code}: {message}")


class WooCommerceClient:
    """Async HTTP client for WooCommerce REST API v3 with per-account auth."""

    def __init__(self, auth: WooCommerceAuth):
        self._auth = auth
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _get_http_client(self, base_url: str, verify_ssl: bool = True) -> httpx.AsyncClient:
        if base_url not in self._clients:
            self._clients[base_url] = httpx.AsyncClient(
                base_url=base_url,
                verify=verify_ssl,
                timeout=httpx.Timeout(
                    connect=settings.http_connect_timeout,
                    read=settings.http_read_timeout,
                    write=settings.http_connect_timeout,
                    pool=settings.http_connect_timeout,
                ),
            )
        return self._clients[base_url]

    async def close(self) -> None:
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    async def request(
        self,
        method: str,
        path: str,
        account_name: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        verify_ssl: bool = True,
    ) -> httpx.Response:
        """Execute an authenticated request to WooCommerce REST API."""
        base_url = self._auth.get_base_url(account_name)
        http_client = self._get_http_client(base_url, verify_ssl)
        full_url = f"{base_url}/{path.lstrip('/')}"

        for attempt in range(settings.max_retries):
            request_params = dict(params or {})

            basic_auth = self._auth.get_basic_auth(account_name)
            oauth_params = self._auth.get_auth_params(account_name, method, full_url)
            if oauth_params:
                request_params.update(oauth_params)

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            start = time.monotonic()
            response = await http_client.request(
                method,
                path,
                headers=headers,
                params=request_params if request_params else None,
                json=json_data,
                auth=basic_auth,
            )
            duration = time.monotonic() - start

            operation = path.split("/")[0] if path else "unknown"
            metrics["external_api_calls_total"].labels(
                system="woocommerce", operation=operation, status=response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="woocommerce", operation=operation,
            ).observe(duration)

            if response.status_code == 401:
                logger.warning(
                    "WooCommerce 401 on attempt %d for account=%s path=%s — check consumer_key/consumer_secret",
                    attempt + 1, account_name, path,
                )
                if attempt == settings.max_retries - 1:
                    raise WooCommerceApiError(401, "Authentication failed — invalid consumer key or secret")
                backoff = settings.retry_backoff_factor * (2 ** attempt)
                await asyncio.sleep(backoff)
                continue

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning("WooCommerce rate limited, waiting %ds", retry_after)
                await asyncio.sleep(retry_after)
                continue

            return response

        raise WooCommerceApiError(0, f"Request failed after {settings.max_retries} retries")

    async def get(self, path: str, account_name: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, account_name, **kwargs)

    async def post(self, path: str, account_name: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, account_name, **kwargs)

    async def put(self, path: str, account_name: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", path, account_name, **kwargs)

    async def delete(self, path: str, account_name: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", path, account_name, **kwargs)

    # --- High-level WooCommerce API methods ---

    async def list_orders(
        self,
        account_name: str,
        per_page: int = 100,
        page: int = 1,
        status: str | None = None,
        modified_after: str | None = None,
        modified_before: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        if status:
            params["status"] = status
        if modified_after:
            params["modified_after"] = modified_after
        if modified_before:
            params["modified_before"] = modified_before

        resp = await self.get("orders", account_name, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_order(self, order_id: int, account_name: str) -> dict[str, Any]:
        resp = await self.get(f"orders/{order_id}", account_name)
        resp.raise_for_status()
        return resp.json()

    async def update_order(
        self, order_id: int, account_name: str, data: dict[str, Any],
    ) -> dict[str, Any]:
        resp = await self.put(f"orders/{order_id}", account_name, json_data=data)
        resp.raise_for_status()
        return resp.json()

    async def list_products(
        self,
        account_name: str,
        per_page: int = 100,
        page: int = 1,
        sku: str | None = None,
        search: str | None = None,
        modified_after: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        if sku:
            params["sku"] = sku
        if search:
            params["search"] = search
        if modified_after:
            params["modified_after"] = modified_after

        resp = await self.get("products", account_name, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_product(self, product_id: int, account_name: str) -> dict[str, Any]:
        resp = await self.get(f"products/{product_id}", account_name)
        resp.raise_for_status()
        return resp.json()

    async def create_product(self, account_name: str, data: dict[str, Any]) -> dict[str, Any]:
        resp = await self.post("products", account_name, json_data=data)
        resp.raise_for_status()
        return resp.json()

    async def update_product(
        self, product_id: int, account_name: str, data: dict[str, Any],
    ) -> dict[str, Any]:
        resp = await self.put(f"products/{product_id}", account_name, json_data=data)
        resp.raise_for_status()
        return resp.json()

    async def update_product_stock(
        self, product_id: int, quantity: int, account_name: str,
    ) -> dict[str, Any]:
        return await self.update_product(
            product_id, account_name,
            {"stock_quantity": quantity, "manage_stock": True},
        )

    async def list_customers(
        self,
        account_name: str,
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        resp = await self.get("customers", account_name, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_customer(self, customer_id: int, account_name: str) -> dict[str, Any]:
        resp = await self.get(f"customers/{customer_id}", account_name)
        resp.raise_for_status()
        return resp.json()

    async def test_connection(self, account_name: str) -> dict[str, Any]:
        """Test the connection by fetching system status."""
        resp = await self.get("system_status", account_name)
        resp.raise_for_status()
        return resp.json()

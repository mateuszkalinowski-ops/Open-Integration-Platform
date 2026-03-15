"""Low-level IdoSell Admin REST API client with retry and rate-limit handling.

Supports two authentication modes:
  - api_key: X-API-KEY header, modern /api/admin/{version}/ URLs
  - legacy:  SHA-1 daily key in request body, /admin/{version}/ URLs (Java compat)
"""

import asyncio
import logging
import time
from typing import Any

import httpx
from pinquark_common.monitoring.metrics import setup_metrics

from src.config import IdoSellAccountConfig, settings
from src.idosell.auth import IdoSellAuthManager

logger = logging.getLogger(__name__)

metrics = setup_metrics("idosell")

RETRY_AFTER_HEADER = "Retry-After"


class IdoSellApiError(Exception):
    def __init__(self, status_code: int, message: str, raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}
        super().__init__(f"IdoSell API {status_code}: {message}")


class IdoSellClient:
    """Async HTTP client for IdoSell Admin API (api_key + legacy modes)."""

    def __init__(self, auth_manager: IdoSellAuthManager):
        self._auth = auth_manager
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _get_http_client(self, account: IdoSellAccountConfig) -> httpx.AsyncClient:
        base_url = self._auth.build_base_url(account)
        key = f"{account.shop_url}_{account.api_version}_{account.auth_mode}"
        if key not in self._clients:
            self._clients[key] = httpx.AsyncClient(
                base_url=base_url,
                timeout=httpx.Timeout(
                    connect=settings.http_connect_timeout,
                    read=settings.http_read_timeout,
                    write=settings.http_connect_timeout,
                    pool=settings.http_connect_timeout,
                ),
            )
        return self._clients[key]

    async def close(self) -> None:
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    def _inject_legacy_auth(self, account: IdoSellAccountConfig, json_data: Any | None) -> Any:
        """For legacy mode, inject 'authenticate' block into the request body."""
        if account.auth_mode != "legacy":
            return json_data
        auth_block = self._auth.get_legacy_auth_body(account)
        if json_data is None:
            return {"authenticate": auth_block}
        if isinstance(json_data, dict):
            json_data["authenticate"] = auth_block
        return json_data

    async def request(
        self,
        method: str,
        path: str,
        account: IdoSellAccountConfig,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
    ) -> httpx.Response:
        http_client = self._get_http_client(account)
        headers = self._auth.get_headers(account)

        if method.upper() in ("POST", "PUT"):
            json_data = self._inject_legacy_auth(account, json_data)
        elif account.auth_mode == "legacy" and method.upper() == "GET":
            method = "POST"
            json_data = self._inject_legacy_auth(account, json_data or {})
            if params:
                json_data.update(params)
                params = None

        last_response: httpx.Response | None = None
        for attempt in range(settings.max_retries):
            start = time.monotonic()
            last_response = await http_client.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json_data,
            )
            duration = time.monotonic() - start

            operation = path.split("/")[0] if path else "unknown"
            metrics["external_api_calls_total"].labels(
                system="idosell",
                operation=operation,
                status=last_response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="idosell",
                operation=operation,
            ).observe(duration)

            if last_response.status_code == 401:
                logger.error(
                    "IdoSell 401 Unauthorized for account=%s path=%s (mode=%s)",
                    account.name,
                    path,
                    account.auth_mode,
                )
                raise IdoSellApiError(
                    401,
                    f"Authentication failed for account '{account.name}' (mode={account.auth_mode}). "
                    "Check api_key or login/password.",
                )

            if last_response.status_code == 429:
                retry_after = float(last_response.headers.get(RETRY_AFTER_HEADER, "5.0"))
                logger.warning(
                    "IdoSell rate limited for account=%s, waiting %.1fs (attempt %d/%d)",
                    account.name,
                    retry_after,
                    attempt + 1,
                    settings.max_retries,
                )
                await asyncio.sleep(retry_after)
                continue

            if last_response.status_code >= 500:
                backoff = settings.retry_backoff_factor * (2**attempt)
                logger.warning(
                    "IdoSell %d for account=%s path=%s, retrying in %.1fs (attempt %d/%d)",
                    last_response.status_code,
                    account.name,
                    path,
                    backoff,
                    attempt + 1,
                    settings.max_retries,
                )
                await asyncio.sleep(backoff)
                continue

            return last_response

        raise IdoSellApiError(
            last_response.status_code if last_response else 500,
            f"Request failed after {settings.max_retries} retries: {path}",
        )

    async def get(self, path: str, account: IdoSellAccountConfig, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, account, **kwargs)

    async def post(self, path: str, account: IdoSellAccountConfig, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, account, **kwargs)

    async def put(self, path: str, account: IdoSellAccountConfig, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", path, account, **kwargs)

    # -----------------------------------------------------------------------
    # High-level API methods
    # -----------------------------------------------------------------------

    async def search_orders(
        self,
        account: IdoSellAccountConfig,
        date_begin: str | None = None,
        date_end: str | None = None,
        date_type: str = "modified",
        statuses: list[str] | None = None,
        page: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """POST /orders/orders/search — search orders with filters."""
        params: dict[str, Any] = {"resultsPage": page, "resultsLimit": limit}
        if date_begin or date_end:
            date_range: dict[str, Any] = {"ordersDateType": date_type}
            if date_begin:
                date_range["ordersDateBegin"] = date_begin
            if date_end:
                date_range["ordersDateEnd"] = date_end
            params["ordersRange"] = {"ordersDateRange": date_range}
        if statuses:
            params["ordersStatuses"] = statuses

        body: dict[str, Any] = {"params": params}
        resp = await self.post("orders/orders/search", account, json_data=body)
        resp.raise_for_status()
        return resp.json()

    async def get_orders(
        self,
        account: IdoSellAccountConfig,
        serial_numbers: list[int] | None = None,
        order_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """GET /orders/orders — fetch orders by serial numbers or IDs.

        In legacy mode, GET is converted to POST automatically.
        """
        params: dict[str, Any] = {}
        if serial_numbers:
            params["ordersSerialNumbers"] = serial_numbers
        if order_ids:
            params["ordersIds"] = order_ids

        if account.auth_mode == "legacy":
            body: dict[str, Any] = {"params": params}
            resp = await self.post("orders/orders", account, json_data=body)
        else:
            query: dict[str, str] = {}
            if serial_numbers:
                query["ordersSerialNumbers"] = ",".join(str(sn) for sn in serial_numbers)
            if order_ids:
                query["ordersIds"] = ",".join(order_ids)
            resp = await self.get("orders/orders", account, params=query)

        resp.raise_for_status()
        return resp.json()

    async def update_order_status(
        self,
        account: IdoSellAccountConfig,
        order_serial_number: int,
        new_status: str,
    ) -> dict[str, Any]:
        """PUT /orders/orders — update order status."""
        body: dict[str, Any] = {
            "params": {
                "orders": [
                    {
                        "orderSerialNumber": order_serial_number,
                        "orderStatus": new_status,
                    }
                ]
            }
        }
        resp = await self.put("orders/orders", account, json_data=body)
        resp.raise_for_status()
        return resp.json()

    async def search_products(
        self,
        account: IdoSellAccountConfig,
        modified_after: str | None = None,
        page: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """POST /products/products/search — search products with filters."""
        params: dict[str, Any] = {"resultsPage": page, "resultsLimit": limit}
        if modified_after:
            params["productDate"] = {
                "productDateType": "modification",
                "productDateBegin": modified_after,
            }

        body: dict[str, Any] = {"params": params}
        resp = await self.post("products/products/search", account, json_data=body)
        resp.raise_for_status()
        return resp.json()

    async def get_products(
        self,
        account: IdoSellAccountConfig,
        product_ids: list[int],
    ) -> dict[str, Any]:
        """GET /products/products — fetch products by IDs."""
        if account.auth_mode == "legacy":
            body: dict[str, Any] = {"params": {"productsIds": product_ids}}
            resp = await self.post("products/products", account, json_data=body)
        else:
            params = {"productsIds": ",".join(str(pid) for pid in product_ids)}
            resp = await self.get("products/products", account, params=params)

        resp.raise_for_status()
        return resp.json()

    async def update_stock_quantity(
        self,
        account: IdoSellAccountConfig,
        products: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """PUT /products/stockQuantity — update product stock levels."""
        body: dict[str, Any] = {"params": {"products": products}}
        resp = await self.put("products/stockQuantity", account, json_data=body)
        resp.raise_for_status()
        return resp.json()

    async def create_package(
        self,
        account: IdoSellAccountConfig,
        order_serial_number: int,
        courier_id: int,
        tracking_numbers: list[str],
    ) -> dict[str, Any]:
        """POST /orders/packages — create shipping packages for an order."""
        packages = [{"deliveryPackageNumber": num, "courierId": courier_id} for num in tracking_numbers]
        body: dict[str, Any] = {
            "params": {
                "orderPackages": [
                    {
                        "eventType": "order",
                        "eventId": str(order_serial_number),
                        "packages": packages,
                    }
                ]
            }
        }
        resp = await self.post("orders/packages", account, json_data=body)
        resp.raise_for_status()
        return resp.json()

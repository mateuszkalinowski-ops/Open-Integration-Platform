"""Low-level BaseLinker API client.

BaseLinker uses a single POST endpoint (connector.php) with method-based dispatch.
Auth via X-BLToken header. Rate limit: 100 req/min.
"""

import asyncio
import json
import logging
import time
from typing import Any

import httpx
from pinquark_common.monitoring.metrics import setup_metrics

from src.config import BaseLinkerAccountConfig, settings

logger = logging.getLogger(__name__)

metrics = setup_metrics("baselinker")


class BaseLinkerApiError(Exception):
    def __init__(self, status_code: int, message: str, error_code: str = "", raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.raw = raw or {}
        super().__init__(f"BaseLinker API {status_code}: {error_code} — {message}")


class BaseLinkerClient:
    """Async HTTP client for BaseLinker API."""

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=settings.http_connect_timeout,
                    read=settings.http_read_timeout,
                    write=settings.http_connect_timeout,
                    pool=settings.http_connect_timeout,
                ),
            )
        return self._http

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    async def call(
        self,
        method: str,
        account: BaseLinkerAccountConfig,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call a BaseLinker API method. All calls go through connector.php via POST."""
        http = self._get_http_client()
        headers = {"X-BLToken": account.api_token}
        data = {
            "method": method,
            "parameters": json.dumps(parameters or {}),
        }

        last_response: httpx.Response | None = None
        for attempt in range(settings.max_retries):
            start = time.monotonic()
            last_response = await http.post(settings.baselinker_api_url, headers=headers, data=data)
            duration = time.monotonic() - start

            metrics["external_api_calls_total"].labels(
                system="baselinker",
                operation=method,
                status=last_response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="baselinker",
                operation=method,
            ).observe(duration)

            if last_response.status_code == 429:
                backoff = float(last_response.headers.get("Retry-After", "60"))
                logger.warning(
                    "BaseLinker rate limited, waiting %.0fs (attempt %d/%d)", backoff, attempt + 1, settings.max_retries
                )
                await asyncio.sleep(backoff)
                continue

            if last_response.status_code >= 500:
                backoff = settings.retry_backoff_factor * (2**attempt)
                logger.warning(
                    "BaseLinker %d, retrying in %.1fs (attempt %d/%d)",
                    last_response.status_code,
                    backoff,
                    attempt + 1,
                    settings.max_retries,
                )
                await asyncio.sleep(backoff)
                continue

            break

        if last_response is None:
            raise BaseLinkerApiError(500, "No response received")

        last_response.raise_for_status()
        result = last_response.json()

        if result.get("status") == "ERROR":
            raise BaseLinkerApiError(
                400,
                result.get("error_message", "Unknown error"),
                error_code=result.get("error_code", ""),
                raw=result,
            )

        return result

    # -----------------------------------------------------------------------
    # High-level API methods
    # -----------------------------------------------------------------------

    async def get_orders(
        self,
        account: BaseLinkerAccountConfig,
        date_confirmed_from: int = 0,
        date_from: int = 0,
        status_id: int | None = None,
        get_unconfirmed_orders: bool = False,
        include_custom_extra_fields: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"get_unconfirmed_orders": get_unconfirmed_orders}
        if date_confirmed_from:
            params["date_confirmed_from"] = date_confirmed_from
        if date_from:
            params["date_from"] = date_from
        if status_id is not None:
            params["status_id"] = status_id
        if include_custom_extra_fields:
            params["include_custom_extra_fields"] = True
        return await self.call("getOrders", account, params)

    async def set_order_status(
        self,
        account: BaseLinkerAccountConfig,
        order_id: int,
        status_id: int,
    ) -> dict[str, Any]:
        return await self.call(
            "setOrderStatus",
            account,
            {
                "order_id": order_id,
                "status_id": status_id,
            },
        )

    async def set_order_fields(
        self,
        account: BaseLinkerAccountConfig,
        order_id: int,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.call("setOrderFields", account, {"order_id": order_id, **fields})

    async def get_order_status_list(self, account: BaseLinkerAccountConfig) -> dict[str, Any]:
        return await self.call("getOrderStatusList", account)

    async def get_journal_list(
        self,
        account: BaseLinkerAccountConfig,
        last_log_id: int = 0,
        logs_types: list[int] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"last_log_id": last_log_id}
        if logs_types:
            params["logs_types"] = logs_types
        return await self.call("getJournalList", account, params)

    async def get_inventory_products_list(
        self,
        account: BaseLinkerAccountConfig,
        inventory_id: int,
        page: int = 1,
    ) -> dict[str, Any]:
        return await self.call(
            "getInventoryProductsList",
            account,
            {
                "inventory_id": inventory_id,
                "page": page,
            },
        )

    async def get_inventory_products_data(
        self,
        account: BaseLinkerAccountConfig,
        inventory_id: int,
        products: list[int],
    ) -> dict[str, Any]:
        return await self.call(
            "getInventoryProductsData",
            account,
            {
                "inventory_id": inventory_id,
                "products": products,
            },
        )

    async def get_inventory_products_stock(
        self,
        account: BaseLinkerAccountConfig,
        inventory_id: int,
        page: int = 1,
    ) -> dict[str, Any]:
        return await self.call(
            "getInventoryProductsStock",
            account,
            {
                "inventory_id": inventory_id,
                "page": page,
            },
        )

    async def update_inventory_products_stock(
        self,
        account: BaseLinkerAccountConfig,
        inventory_id: int,
        products: dict[str, dict[str, float]],
    ) -> dict[str, Any]:
        """Update stock. products = { product_id: { warehouse_id: quantity } }"""
        return await self.call(
            "updateInventoryProductsStock",
            account,
            {
                "inventory_id": inventory_id,
                "products": products,
            },
        )

    async def create_package(
        self,
        account: BaseLinkerAccountConfig,
        order_id: int,
        courier_code: str,
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.call(
            "createPackage",
            account,
            {
                "order_id": order_id,
                "courier_code": courier_code,
                **(fields or {}),
            },
        )

    async def create_package_manual(
        self,
        account: BaseLinkerAccountConfig,
        order_id: int,
        courier_code: str,
        package_number: str,
    ) -> dict[str, Any]:
        return await self.call(
            "createPackageManual",
            account,
            {
                "order_id": order_id,
                "courier_code": courier_code,
                "package_number": package_number,
            },
        )

    async def get_inventories(self, account: BaseLinkerAccountConfig) -> dict[str, Any]:
        return await self.call("getInventories", account)

    async def get_inventory_warehouses(self, account: BaseLinkerAccountConfig) -> dict[str, Any]:
        return await self.call("getInventoryWarehouses", account)

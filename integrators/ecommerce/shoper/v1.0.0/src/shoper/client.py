"""Low-level Shoper REST API client with retry and rate-limit handling."""

import asyncio
import json
import logging
import time
from typing import Any

import httpx
from pinquark_common.monitoring.metrics import setup_metrics

from src.config import settings
from src.shoper.auth import ShoperAuthManager

logger = logging.getLogger(__name__)

metrics = setup_metrics("shoper")


class ShoperApiError(Exception):
    def __init__(self, status_code: int, message: str, raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}
        super().__init__(f"Shoper API {status_code}: {message}")


class ShoperClient:
    """Async HTTP client for Shoper REST API with per-account auth."""

    def __init__(self, auth_manager: ShoperAuthManager):
        self._auth = auth_manager
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _get_http_client(self, shop_url: str) -> httpx.AsyncClient:
        if shop_url not in self._clients:
            base_url = f"{shop_url.rstrip('/')}/webapi/rest"
            self._clients[shop_url] = httpx.AsyncClient(
                base_url=base_url,
                timeout=httpx.Timeout(
                    connect=settings.http_connect_timeout,
                    read=settings.http_read_timeout,
                    write=settings.http_connect_timeout,
                    pool=settings.http_connect_timeout,
                ),
            )
        return self._clients[shop_url]

    async def close(self) -> None:
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    async def request(
        self,
        method: str,
        path: str,
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
    ) -> httpx.Response:
        http_client = self._get_http_client(shop_url)

        for attempt in range(settings.max_retries):
            token = await self._auth.get_access_token(account_name, shop_url, login, password)
            headers = {"Authorization": token}

            start = time.monotonic()
            response = await http_client.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json_data,
            )
            duration = time.monotonic() - start

            operation = path.split("/")[0] if path else "unknown"
            metrics["external_api_calls_total"].labels(
                system="shoper",
                operation=operation,
                status=response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="shoper",
                operation=operation,
            ).observe(duration)

            if response.status_code == 401:
                logger.warning(
                    "Shoper 401 on attempt %d for account=%s path=%s",
                    attempt + 1,
                    account_name,
                    path,
                )
                self._auth.invalidate(account_name)
                if attempt == settings.max_retries - 1:
                    raise ShoperApiError(401, "Authentication failed after retries")
                continue

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning("Shoper rate limited, waiting %ds", retry_after)
                await asyncio.sleep(retry_after)
                continue

            return response

        raise ShoperApiError(401, f"Failed after {settings.max_retries} auth retries")

    async def get(
        self, path: str, account_name: str, shop_url: str, login: str, password: str, **kwargs: Any
    ) -> httpx.Response:
        return await self.request("GET", path, account_name, shop_url, login, password, **kwargs)

    async def post(
        self, path: str, account_name: str, shop_url: str, login: str, password: str, **kwargs: Any
    ) -> httpx.Response:
        return await self.request("POST", path, account_name, shop_url, login, password, **kwargs)

    async def put(
        self, path: str, account_name: str, shop_url: str, login: str, password: str, **kwargs: Any
    ) -> httpx.Response:
        return await self.request("PUT", path, account_name, shop_url, login, password, **kwargs)

    async def get_paged(
        self,
        entity: str,
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
        filters: dict[str, dict[str, Any]] | None = None,
        order: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of an entity."""
        all_items: list[dict[str, Any]] = []
        current_page = 1

        while True:
            params: dict[str, Any] = {"page": current_page}
            if filters:
                params["filters"] = json.dumps(filters)
            if order:
                params["order"] = ",".join(order)

            resp = await self.get(entity, account_name, shop_url, login, password, params=params)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("list", [])
            all_items.extend(items)

            pages = data.get("pages", 1)
            if current_page >= pages:
                break
            current_page += 1

        return all_items

    async def get_one(
        self,
        entity: str,
        entity_id: int,
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
    ) -> dict[str, Any]:
        resp = await self.get(f"{entity}/{entity_id}", account_name, shop_url, login, password)
        resp.raise_for_status()
        return resp.json()

    async def update_entity(
        self,
        entity: str,
        entity_id: int,
        data: dict[str, Any],
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
    ) -> httpx.Response:
        return await self.put(
            f"{entity}/{entity_id}",
            account_name,
            shop_url,
            login,
            password,
            json_data=data,
        )

    async def create_entity(
        self,
        entity: str,
        data: dict[str, Any],
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
    ) -> httpx.Response:
        return await self.post(entity, account_name, shop_url, login, password, json_data=data)

    async def get_bulk(
        self,
        entity: str,
        account_name: str,
        shop_url: str,
        login: str,
        password: str,
        filters: dict[str, dict[str, Any]] | None = None,
        order: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all pages via the /bulk endpoint for better performance."""
        all_items: list[dict[str, Any]] = []
        current_page = 1
        request_id = "pagedRequest"

        while True:
            params: dict[str, Any] = {"page": str(current_page)}
            if filters:
                params["filters"] = json.dumps(filters)
            if order:
                params["order"] = order

            bulk_request = [
                {
                    "id": request_id,
                    "path": f"/webapi/rest/{entity}",
                    "method": "GET",
                    "params": params,
                }
            ]

            resp = await self.post("bulk", account_name, shop_url, login, password, json_data=bulk_request)
            resp.raise_for_status()
            bulk_data = resp.json()

            items_list = bulk_data.get("items", [])
            page_data = None
            for item in items_list:
                if item.get("id") == request_id:
                    page_data = item.get("body")
                    break

            if not page_data:
                break

            all_items.extend(page_data.get("list", []))
            pages = page_data.get("pages", 1)
            if current_page >= pages:
                break
            current_page += 1

        return all_items

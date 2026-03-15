"""Low-level Shopify Admin REST API client with retry and rate-limit handling."""

import asyncio
import logging
import time
from typing import Any

import httpx
from pinquark_common.monitoring.metrics import setup_metrics

from src.config import ShopifyAccountConfig, settings

logger = logging.getLogger(__name__)

metrics = setup_metrics("shopify")

API_CALL_LIMIT_HEADER = "X-Shopify-Shop-Api-Call-Limit"
RETRY_AFTER_HEADER = "Retry-After"


class ShopifyApiError(Exception):
    def __init__(self, status_code: int, message: str, raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}
        super().__init__(f"Shopify API {status_code}: {message}")


class ShopifyClient:
    """Async HTTP client for Shopify Admin REST API with per-account configuration."""

    def __init__(self) -> None:
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _get_http_client(self, base_url: str) -> httpx.AsyncClient:
        if base_url not in self._clients:
            self._clients[base_url] = httpx.AsyncClient(
                base_url=base_url,
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

    @staticmethod
    def _build_base_url(account: ShopifyAccountConfig) -> str:
        shop_url = account.shop_url.rstrip("/")
        if not shop_url.startswith("https://"):
            shop_url = f"https://{shop_url}"
        return f"{shop_url}/admin/api/{account.api_version}/"

    async def request(
        self,
        method: str,
        path: str,
        account: ShopifyAccountConfig,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute an authenticated request to Shopify API with retry on rate limit."""
        base_url = self._build_base_url(account)
        http_client = self._get_http_client(base_url)
        headers = {
            "X-Shopify-Access-Token": account.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        for attempt in range(settings.max_retries):
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
                system="shopify",
                operation=operation,
                status=response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="shopify",
                operation=operation,
            ).observe(duration)

            self._log_rate_limit(response, account.name)

            if response.status_code == 401:
                logger.error(
                    "Shopify 401 Unauthorized for account=%s path=%s — access token is invalid or revoked",
                    account.name,
                    path,
                )
                raise ShopifyApiError(
                    401,
                    f"Access token invalid for account '{account.name}'. "
                    f"Verify the token in account config or POST /auth/{account.name}/validate.",
                    raw=response.json()
                    if response.headers.get("content-type", "").startswith("application/json")
                    else {},
                )

            if response.status_code == 429:
                retry_after = float(response.headers.get(RETRY_AFTER_HEADER, "2.0"))
                logger.warning(
                    "Shopify rate limited for account=%s, waiting %.1fs (attempt %d/%d)",
                    account.name,
                    retry_after,
                    attempt + 1,
                    settings.max_retries,
                )
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500:
                backoff = settings.retry_backoff_factor * (2**attempt)
                logger.warning(
                    "Shopify server error %d for account=%s path=%s, retrying in %.1fs",
                    response.status_code,
                    account.name,
                    path,
                    backoff,
                )
                await asyncio.sleep(backoff)
                continue

            return response

        raise ShopifyApiError(
            response.status_code,
            f"Failed after {settings.max_retries} retries for {path}",
        )

    def _log_rate_limit(self, response: httpx.Response, account_name: str) -> None:
        limit_header = response.headers.get(API_CALL_LIMIT_HEADER, "")
        if limit_header:
            try:
                used, total = limit_header.split("/")
                usage_pct = int(used) / int(total) * 100
                if usage_pct > 80:
                    logger.warning(
                        "Shopify API rate limit at %.0f%% (%s) for account=%s",
                        usage_pct,
                        limit_header,
                        account_name,
                    )
            except (ValueError, ZeroDivisionError):
                pass

    async def get(self, path: str, account: ShopifyAccountConfig, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, account, **kwargs)

    async def post(self, path: str, account: ShopifyAccountConfig, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, account, **kwargs)

    async def put(self, path: str, account: ShopifyAccountConfig, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", path, account, **kwargs)

    # --- High-level Shopify API methods ---

    async def get_orders(
        self,
        account: ShopifyAccountConfig,
        status: str = "any",
        limit: int = 50,
        since_id: str | None = None,
        updated_at_min: str | None = None,
        fields: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"status": status, "limit": min(limit, 250)}
        if since_id:
            params["since_id"] = since_id
        if updated_at_min:
            params["updated_at_min"] = updated_at_min
        if fields:
            params["fields"] = fields
        resp = await self.get("orders.json", account, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_order(self, order_id: str, account: ShopifyAccountConfig) -> dict:
        resp = await self.get(f"orders/{order_id}.json", account)
        resp.raise_for_status()
        return resp.json()

    async def close_order(self, order_id: str, account: ShopifyAccountConfig) -> dict:
        resp = await self.post(f"orders/{order_id}/close.json", account)
        resp.raise_for_status()
        return resp.json()

    async def open_order(self, order_id: str, account: ShopifyAccountConfig) -> dict:
        resp = await self.post(f"orders/{order_id}/open.json", account)
        resp.raise_for_status()
        return resp.json()

    async def cancel_order(
        self,
        order_id: str,
        account: ShopifyAccountConfig,
        reason: str = "other",
    ) -> dict:
        resp = await self.post(
            f"orders/{order_id}/cancel.json",
            account,
            json_data={"reason": reason},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_fulfillment_orders(self, order_id: str, account: ShopifyAccountConfig) -> dict:
        resp = await self.get(f"orders/{order_id}/fulfillment_orders.json", account)
        resp.raise_for_status()
        return resp.json()

    async def create_fulfillment(
        self,
        account: ShopifyAccountConfig,
        fulfillment_order_ids: list[int],
        tracking_number: str = "",
        tracking_company: str = "",
        notify_customer: bool = True,
    ) -> dict:
        """Create a fulfillment using the Fulfillment Orders API (2023-01+)."""
        line_items_by_fulfillment_order = [{"fulfillment_order_id": fo_id} for fo_id in fulfillment_order_ids]
        payload: dict[str, Any] = {
            "fulfillment": {
                "line_items_by_fulfillment_order": line_items_by_fulfillment_order,
                "notify_customer": notify_customer,
            }
        }
        if tracking_number or tracking_company:
            payload["fulfillment"]["tracking_info"] = {}
            if tracking_number:
                payload["fulfillment"]["tracking_info"]["number"] = tracking_number
            if tracking_company:
                payload["fulfillment"]["tracking_info"]["company"] = tracking_company

        resp = await self.post("fulfillments.json", account, json_data=payload)
        resp.raise_for_status()
        return resp.json()

    async def update_tracking(
        self,
        fulfillment_id: str,
        account: ShopifyAccountConfig,
        tracking_number: str,
        tracking_company: str = "",
        notify_customer: bool = False,
    ) -> dict:
        payload: dict[str, Any] = {
            "fulfillment": {
                "tracking_info": {
                    "number": tracking_number,
                },
                "notify_customer": notify_customer,
            }
        }
        if tracking_company:
            payload["fulfillment"]["tracking_info"]["company"] = tracking_company

        resp = await self.post(
            f"fulfillments/{fulfillment_id}/update_tracking.json",
            account,
            json_data=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_fulfillments(self, order_id: str, account: ShopifyAccountConfig) -> dict:
        resp = await self.get(f"orders/{order_id}/fulfillments.json", account)
        resp.raise_for_status()
        return resp.json()

    async def get_products(
        self,
        account: ShopifyAccountConfig,
        limit: int = 50,
        since_id: str | None = None,
        title: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": min(limit, 250)}
        if since_id:
            params["since_id"] = since_id
        if title:
            params["title"] = title
        resp = await self.get("products.json", account, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_product(self, product_id: str, account: ShopifyAccountConfig) -> dict:
        resp = await self.get(f"products/{product_id}.json", account)
        resp.raise_for_status()
        return resp.json()

    async def create_product(self, account: ShopifyAccountConfig, product_data: dict) -> dict:
        resp = await self.post("products.json", account, json_data={"product": product_data})
        resp.raise_for_status()
        return resp.json()

    async def update_product(
        self,
        product_id: str,
        account: ShopifyAccountConfig,
        product_data: dict,
    ) -> dict:
        resp = await self.put(
            f"products/{product_id}.json",
            account,
            json_data={"product": product_data},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_customers(
        self,
        account: ShopifyAccountConfig,
        limit: int = 50,
        since_id: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": min(limit, 250)}
        if since_id:
            params["since_id"] = since_id
        resp = await self.get("customers.json", account, params=params)
        resp.raise_for_status()
        return resp.json()

    async def set_inventory_level(
        self,
        account: ShopifyAccountConfig,
        inventory_item_id: int,
        location_id: int,
        available: int,
    ) -> dict:
        resp = await self.post(
            "inventory_levels/set.json",
            account,
            json_data={
                "inventory_item_id": inventory_item_id,
                "location_id": location_id,
                "available": available,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def get_locations(self, account: ShopifyAccountConfig) -> dict:
        resp = await self.get("locations.json", account)
        resp.raise_for_status()
        return resp.json()

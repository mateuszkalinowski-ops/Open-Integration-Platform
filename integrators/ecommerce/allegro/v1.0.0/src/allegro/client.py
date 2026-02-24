"""Low-level Allegro REST API client with retry and rate-limit handling."""

import logging
import time
from typing import Any

import httpx

from src.allegro.auth import AllegroAuthManager
from src.config import settings
from pinquark_common.monitoring.metrics import setup_metrics

logger = logging.getLogger(__name__)

ALLEGRO_CONTENT_TYPE = "application/vnd.allegro.public.v1+json"

metrics = setup_metrics("allegro")


class AllegroApiError(Exception):
    def __init__(self, status_code: int, message: str, raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}
        super().__init__(f"Allegro API {status_code}: {message}")


class AllegroClient:
    """Async HTTP client for Allegro REST API with per-account auth."""

    def __init__(self, auth_manager: AllegroAuthManager):
        self._auth = auth_manager
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _get_http_client(self, api_url: str) -> httpx.AsyncClient:
        if api_url not in self._clients:
            self._clients[api_url] = httpx.AsyncClient(
                base_url=api_url,
                timeout=httpx.Timeout(
                    connect=settings.http_connect_timeout,
                    read=settings.http_read_timeout,
                    write=settings.http_connect_timeout,
                    pool=settings.http_connect_timeout,
                ),
            )
        return self._clients[api_url]

    async def close(self) -> None:
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    async def request(
        self,
        method: str,
        path: str,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        accept: str = ALLEGRO_CONTENT_TYPE,
    ) -> httpx.Response:
        """Execute an authenticated request to Allegro API with retry on 401."""
        http_client = self._get_http_client(api_url)

        for attempt in range(settings.max_retries):
            access_token = await self._auth.get_access_token(
                account_name, client_id, client_secret, auth_url,
            )
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": accept,
                "Content-Type": ALLEGRO_CONTENT_TYPE,
            }

            start = time.monotonic()
            response = await http_client.request(
                method, path, headers=headers, params=params, json=json_data,
            )
            duration = time.monotonic() - start

            metrics["external_api_calls_total"].labels(
                system="allegro", operation=path.split("/")[0] if path else "unknown", status=response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="allegro", operation=path.split("/")[0] if path else "unknown",
            ).observe(duration)

            if response.status_code == 401:
                logger.warning(
                    "Allegro 401 on attempt %d for account=%s path=%s",
                    attempt + 1, account_name, path,
                )
                try:
                    await self._auth.refresh_token(account_name, client_id, client_secret, auth_url)
                except Exception:
                    if attempt == settings.max_retries - 1:
                        raise
                continue

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning("Allegro rate limited, waiting %ds", retry_after)
                import asyncio
                await asyncio.sleep(retry_after)
                continue

            return response

        raise AllegroApiError(401, f"Failed after {settings.max_retries} auth retries")

    async def get(self, path: str, account_name: str, client_id: str, client_secret: str,
                  api_url: str, auth_url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, account_name, client_id, client_secret, api_url, auth_url, **kwargs)

    async def post(self, path: str, account_name: str, client_id: str, client_secret: str,
                   api_url: str, auth_url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, account_name, client_id, client_secret, api_url, auth_url, **kwargs)

    async def put(self, path: str, account_name: str, client_id: str, client_secret: str,
                  api_url: str, auth_url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", path, account_name, client_id, client_secret, api_url, auth_url, **kwargs)

    # --- High-level Allegro API methods ---

    async def get_order_events(
        self,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
        from_event_id: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {}
        if from_event_id:
            params["from"] = from_event_id
        resp = await self.get(
            "order/events", account_name, client_id, client_secret, api_url, auth_url,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_checkout_form(
        self,
        checkout_form_id: str,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
    ) -> dict:
        resp = await self.get(
            f"order/checkout-forms/{checkout_form_id}",
            account_name, client_id, client_secret, api_url, auth_url,
        )
        resp.raise_for_status()
        return resp.json()

    async def update_fulfillment_status(
        self,
        checkout_form_id: str,
        status: str,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
    ) -> None:
        resp = await self.put(
            f"order/checkout-forms/{checkout_form_id}/fulfillment",
            account_name, client_id, client_secret, api_url, auth_url,
            json_data={"status": status},
        )
        resp.raise_for_status()

    async def get_offer(
        self,
        offer_id: str,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
    ) -> dict:
        resp = await self.get(
            f"sale/offers/{offer_id}",
            account_name, client_id, client_secret, api_url, auth_url,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_product(
        self,
        product_id: str,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
    ) -> dict:
        resp = await self.get(
            f"sale/products/{product_id}",
            account_name, client_id, client_secret, api_url, auth_url,
        )
        resp.raise_for_status()
        return resp.json()

    async def search_offers(
        self,
        phrase: str,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
        limit: int = 50,
        offset: int = 0,
        category_id: str | None = None,
        sort: str = "price_asc",
    ) -> dict:
        params: dict[str, Any] = {
            "phrase": phrase,
            "limit": min(limit, 60),
            "offset": offset,
            "sort": sort,
        }
        if category_id:
            params["category.id"] = category_id
        resp = await self.get(
            "offers/listing",
            account_name, client_id, client_secret, api_url, auth_url,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def update_offer_stock(
        self,
        offer_id: str,
        stock: int,
        account_name: str,
        client_id: str,
        client_secret: str,
        api_url: str,
        auth_url: str,
    ) -> None:
        resp = await self.put(
            f"sale/offer-quantity-change-commands/{offer_id}",
            account_name, client_id, client_secret, api_url, auth_url,
            json_data={
                "modification": {
                    "changeType": "FIXED",
                    "value": stock,
                },
            },
        )
        resp.raise_for_status()

"""Low-level Apilo REST API client.

Handles authentication, rate limiting (150 req/min), retries, and provides
high-level methods for Orders, Warehouse, Shipment, Finance, and Media APIs.
"""

import asyncio
import contextlib
import logging
import time
from typing import Any

import httpx
from pinquark_common.monitoring.metrics import setup_metrics

from src.apilo.auth import TokenManager
from src.config import ApiloAccountConfig, settings

logger = logging.getLogger(__name__)

metrics = setup_metrics("apilo")


class ApiloApiError(Exception):
    def __init__(self, status_code: int, message: str, error_code: str = "", raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.raw = raw or {}
        super().__init__(f"Apilo API {status_code}: {error_code} — {message}")


class ApiloClient:
    """Async HTTP client for Apilo REST API."""

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._token_manager: TokenManager | None = None

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
            self._token_manager = TokenManager(self._http)
        return self._http

    @property
    def token_manager(self) -> TokenManager:
        self._get_http_client()
        assert self._token_manager is not None
        return self._token_manager

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None
            self._token_manager = None

    async def _request(
        self,
        method: str,
        url: str,
        account: ApiloAccountConfig,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        content: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
        operation_name: str = "",
    ) -> Any:
        http = self._get_http_client()
        access_token = await self.token_manager.get_access_token(account)

        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        if extra_headers:
            headers.update(extra_headers)

        last_response: httpx.Response | None = None
        for attempt in range(settings.max_retries):
            start = time.monotonic()

            kwargs: dict[str, Any] = {"headers": headers, "params": params}
            if content is not None:
                kwargs["content"] = content
                headers["Content-Type"] = "application/octet-stream"
            elif json_body is not None:
                kwargs["json"] = json_body

            last_response = await http.request(method, url, **kwargs)
            duration = time.monotonic() - start

            metrics["external_api_calls_total"].labels(
                system="apilo",
                operation=operation_name,
                status=last_response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="apilo",
                operation=operation_name,
            ).observe(duration)

            if last_response.status_code == 429:
                retry_after = float(last_response.headers.get("Retry-After", "5"))
                logger.warning(
                    "Apilo rate limited, waiting %.1fs (attempt %d/%d)",
                    retry_after,
                    attempt + 1,
                    settings.max_retries,
                )
                await asyncio.sleep(retry_after)
                continue

            if last_response.status_code >= 500:
                backoff = settings.retry_backoff_factor * (2**attempt)
                logger.warning(
                    "Apilo %d, retrying in %.1fs (attempt %d/%d)",
                    last_response.status_code,
                    backoff,
                    attempt + 1,
                    settings.max_retries,
                )
                await asyncio.sleep(backoff)
                continue

            break

        if last_response is None:
            raise ApiloApiError(500, "No response received")

        if last_response.status_code >= 400:
            error_body: dict[str, Any] = {}
            with contextlib.suppress(Exception):
                error_body = last_response.json()
            raise ApiloApiError(
                last_response.status_code,
                error_body.get("message", last_response.text[:200]),
                error_code=str(error_body.get("code", "")),
                raw=error_body,
            )

        if last_response.status_code == 204:
            return {}

        if "application/json" in last_response.headers.get("content-type", ""):
            return last_response.json()

        return last_response.content

    # -----------------------------------------------------------------------
    # Connection
    # -----------------------------------------------------------------------

    async def test_connection(self, account: ApiloAccountConfig) -> dict[str, Any]:
        url = f"{account.api_url}/"
        return await self._request("GET", url, account, operation_name="testConnection")

    async def whoami(self, account: ApiloAccountConfig) -> dict[str, Any]:
        url = f"{account.api_url}/whoami/"
        return await self._request("GET", url, account, operation_name="whoami")

    # -----------------------------------------------------------------------
    # Orders API
    # -----------------------------------------------------------------------

    async def get_orders(
        self,
        account: ApiloAccountConfig,
        *,
        created_after: str | None = None,
        updated_after: str | None = None,
        order_status: int | None = None,
        order_status_ids: list[int] | None = None,
        platform_account_id: int | None = None,
        sort: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": min(limit, 512), "offset": offset}
        if created_after:
            params["createdAfter"] = created_after
        if updated_after:
            params["updatedAfter"] = updated_after
        if order_status is not None:
            params["orderStatus"] = order_status
        if order_status_ids:
            for i, sid in enumerate(order_status_ids):
                params[f"orderStatusIds[{i}]"] = sid
        if platform_account_id is not None:
            params["platformAccountId"] = platform_account_id
        if sort:
            params["sort"] = sort

        url = f"{account.api_url}/orders/"
        return await self._request("GET", url, account, params=params, operation_name="getOrders")

    async def get_order(self, account: ApiloAccountConfig, order_id: str) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/"
        return await self._request("GET", url, account, operation_name="getOrder")

    async def create_order(self, account: ApiloAccountConfig, order_data: dict[str, Any]) -> dict[str, Any]:
        url = f"{account.api_url}/orders/"
        return await self._request("POST", url, account, json_body=order_data, operation_name="createOrder")

    async def update_order_status(self, account: ApiloAccountConfig, order_id: str, status: int) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/status/"
        return await self._request(
            "PUT", url, account, json_body={"status": status}, operation_name="updateOrderStatus"
        )

    async def add_order_payment(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        payment_data: dict[str, Any],
    ) -> Any:
        url = f"{account.api_url}/orders/{order_id}/payment/"
        return await self._request("POST", url, account, json_body=payment_data, operation_name="addOrderPayment")

    async def get_order_notes(self, account: ApiloAccountConfig, order_id: str) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/note/"
        return await self._request("GET", url, account, operation_name="getOrderNotes")

    async def add_order_note(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        comment: str,
        note_type: int = 2,
    ) -> Any:
        url = f"{account.api_url}/orders/{order_id}/note/"
        return await self._request(
            "POST",
            url,
            account,
            json_body={"type": note_type, "comment": comment},
            operation_name="addOrderNote",
        )

    async def get_order_documents(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/documents/"
        params: dict[str, Any] = {"offset": offset, "limit": min(limit, 512)}
        return await self._request("GET", url, account, params=params, operation_name="getOrderDocuments")

    async def create_order_document(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        doc_data: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/documents/"
        return await self._request("POST", url, account, json_body=doc_data, operation_name="createOrderDocument")

    async def delete_order_document(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        document_id: str,
    ) -> Any:
        url = f"{account.api_url}/orders/{order_id}/documents/{document_id}/"
        return await self._request("DELETE", url, account, operation_name="deleteOrderDocument")

    async def get_order_shipments(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/shipment/"
        params: dict[str, Any] = {"offset": offset, "limit": min(limit, 512)}
        return await self._request("GET", url, account, params=params, operation_name="getOrderShipments")

    async def add_order_shipment(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        shipment_data: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/shipment/"
        return await self._request("POST", url, account, json_body=shipment_data, operation_name="addOrderShipment")

    async def get_order_shipment_detail(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        shipment_id: str,
    ) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/shipment/{shipment_id}/"
        return await self._request("GET", url, account, operation_name="getOrderShipmentDetail")

    async def get_order_tags(
        self,
        account: ApiloAccountConfig,
        order_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/tag/"
        params: dict[str, Any] = {"offset": offset, "limit": min(limit, 512)}
        return await self._request("GET", url, account, params=params, operation_name="getOrderTags")

    async def create_order_tag(self, account: ApiloAccountConfig, order_id: str, tag_id: int) -> Any:
        url = f"{account.api_url}/orders/{order_id}/tag/"
        return await self._request("POST", url, account, json_body={"tag": tag_id}, operation_name="createOrderTag")

    async def delete_order_tag(self, account: ApiloAccountConfig, order_id: str, tag_id: str) -> Any:
        url = f"{account.api_url}/orders/{order_id}/tag/{tag_id}/"
        return await self._request("DELETE", url, account, operation_name="deleteOrderTag")

    async def get_order_shipping_defaults(self, account: ApiloAccountConfig, order_id: str) -> dict[str, Any]:
        url = f"{account.api_url}/orders/{order_id}/shipping-settings-defaults/"
        return await self._request("GET", url, account, operation_name="getOrderShippingDefaults")

    # -----------------------------------------------------------------------
    # Order maps/enums
    # -----------------------------------------------------------------------

    async def get_status_map(self, account: ApiloAccountConfig) -> list[dict[str, Any]]:
        url = f"{account.api_url}/orders/status/map/"
        return await self._request("GET", url, account, operation_name="getStatusMap")

    async def get_payment_types(self, account: ApiloAccountConfig) -> list[dict[str, Any]]:
        url = f"{account.api_url}/orders/payment/map/"
        return await self._request("GET", url, account, operation_name="getPaymentTypes")

    async def get_carrier_map(self, account: ApiloAccountConfig) -> list[dict[str, Any]]:
        url = f"{account.api_url}/orders/carrier/map/"
        return await self._request("GET", url, account, operation_name="getCarrierMap")

    async def get_carrier_accounts(self, account: ApiloAccountConfig) -> list[dict[str, Any]]:
        url = f"{account.api_url}/orders/carrier-account/map/"
        return await self._request("GET", url, account, operation_name="getCarrierAccounts")

    async def get_platform_map(self, account: ApiloAccountConfig) -> list[dict[str, Any]]:
        url = f"{account.api_url}/orders/platform/map/"
        return await self._request("GET", url, account, operation_name="getPlatformMap")

    async def get_tag_map(self, account: ApiloAccountConfig) -> list[dict[str, Any]]:
        url = f"{account.api_url}/orders/tag/map/"
        return await self._request("GET", url, account, operation_name="getTagMap")

    async def get_document_types_map(self, account: ApiloAccountConfig) -> list[dict[str, Any]]:
        url = f"{account.api_url}/orders/documents/map/"
        return await self._request("GET", url, account, operation_name="getDocumentTypesMap")

    # -----------------------------------------------------------------------
    # Warehouse / Products API
    # -----------------------------------------------------------------------

    async def get_products(
        self,
        account: ApiloAccountConfig,
        *,
        product_id: int | None = None,
        sku: str | None = None,
        name: str | None = None,
        ean: str | None = None,
        status: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": min(limit, 2000), "offset": offset}
        if product_id is not None:
            params["id"] = product_id
        if sku:
            params["sku"] = sku
        if name:
            params["name"] = name
        if ean:
            params["ean"] = ean
        if status is not None:
            params["status"] = status

        url = f"{account.api_url}/warehouse/product/"
        return await self._request("GET", url, account, params=params, operation_name="getProducts")

    async def get_product(self, account: ApiloAccountConfig, product_id: int) -> dict[str, Any]:
        url = f"{account.api_url}/warehouse/product/{product_id}/"
        return await self._request("GET", url, account, operation_name="getProduct")

    async def create_products(self, account: ApiloAccountConfig, products: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{account.api_url}/warehouse/product/"
        return await self._request("POST", url, account, json_body=products, operation_name="createProducts")

    async def update_products(self, account: ApiloAccountConfig, products: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{account.api_url}/warehouse/product/"
        return await self._request("PUT", url, account, json_body=products, operation_name="updateProducts")

    async def patch_products(self, account: ApiloAccountConfig, products: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{account.api_url}/warehouse/product/"
        return await self._request("PATCH", url, account, json_body=products, operation_name="patchProducts")

    async def delete_product(self, account: ApiloAccountConfig, product_id: int) -> Any:
        url = f"{account.api_url}/warehouse/product/{product_id}/"
        return await self._request("DELETE", url, account, operation_name="deleteProduct")

    async def get_categories(
        self,
        account: ApiloAccountConfig,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        url = f"{account.api_url}/warehouse/category/"
        params: dict[str, Any] = {"offset": offset, "limit": min(limit, 512)}
        return await self._request("GET", url, account, params=params, operation_name="getCategories")

    async def create_category(self, account: ApiloAccountConfig, category_data: dict[str, Any]) -> Any:
        url = f"{account.api_url}/warehouse/category/"
        return await self._request("POST", url, account, json_body=category_data, operation_name="createCategory")

    async def get_price_lists(self, account: ApiloAccountConfig) -> dict[str, Any]:
        url = f"{account.api_url}/warehouse/price/"
        return await self._request("GET", url, account, operation_name="getPriceLists")

    # -----------------------------------------------------------------------
    # Shipment API
    # -----------------------------------------------------------------------

    async def get_shipment(self, account: ApiloAccountConfig, shipment_id: str) -> dict[str, Any]:
        url = f"{account.api_url}/shipping/shipment/{shipment_id}/"
        return await self._request("GET", url, account, operation_name="getShipment")

    async def get_shipments(
        self,
        account: ApiloAccountConfig,
        *,
        carrier_account_ids: list[int] | None = None,
        post_date_after: str | None = None,
        post_date_before: str | None = None,
        status: list[int] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if carrier_account_ids:
            for i, cid in enumerate(carrier_account_ids):
                params[f"carrierAccountId[{i}]"] = cid
        if post_date_after:
            params["postDateAfter"] = post_date_after
        if post_date_before:
            params["postDateBefore"] = post_date_before
        if status:
            for i, s in enumerate(status):
                params[f"status[{i}]"] = s

        url = f"{account.api_url}/shipping/shipment/info/"
        return await self._request("GET", url, account, params=params, operation_name="getShipments")

    async def create_shipment(self, account: ApiloAccountConfig, shipment_data: dict[str, Any]) -> dict[str, Any]:
        url = f"{account.api_url}/shipping/shipment/"
        return await self._request("POST", url, account, json_body=shipment_data, operation_name="createShipment")

    async def get_shipping_carrier_accounts(self, account: ApiloAccountConfig) -> dict[str, Any]:
        url = f"{account.api_url}/shipping/carrier-account/map/"
        return await self._request("GET", url, account, operation_name="getShippingCarrierAccounts")

    async def get_carrier_methods(self, account: ApiloAccountConfig, carrier_account_id: str) -> dict[str, Any]:
        url = f"{account.api_url}/shipping/carrier-account/{carrier_account_id}/method/"
        return await self._request("GET", url, account, operation_name="getCarrierMethods")

    async def confirm_shipment(
        self, account: ApiloAccountConfig, confirmations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        url = f"{account.api_url}/shipping/carrier-document/"
        return await self._request(
            "POST",
            url,
            account,
            json_body={"shippingConfirmations": confirmations},
            operation_name="confirmShipment",
        )

    # -----------------------------------------------------------------------
    # Finance Documents API
    # -----------------------------------------------------------------------

    async def get_finance_documents(
        self,
        account: ApiloAccountConfig,
        *,
        doc_type: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"offset": offset, "limit": min(limit, 512)}
        if doc_type is not None:
            params["type"] = doc_type

        url = f"{account.api_url}/finance/documents/"
        return await self._request("GET", url, account, params=params, operation_name="getFinanceDocuments")

    # -----------------------------------------------------------------------
    # Media API
    # -----------------------------------------------------------------------

    async def upload_media(
        self,
        account: ApiloAccountConfig,
        file_content: bytes,
        filename: str = "",
    ) -> dict[str, Any]:
        extra_headers: dict[str, str] = {}
        if filename:
            extra_headers["Content-Disposition"] = f"filename={filename}"

        url = f"{account.api_url}/media/"
        return await self._request(
            "POST",
            url,
            account,
            content=file_content,
            extra_headers=extra_headers,
            operation_name="uploadMedia",
        )

    # -----------------------------------------------------------------------
    # Sale API
    # -----------------------------------------------------------------------

    async def get_sales_channels(self, account: ApiloAccountConfig) -> Any:
        url = f"{account.api_url}/sale/"
        return await self._request("GET", url, account, operation_name="getSalesChannels")

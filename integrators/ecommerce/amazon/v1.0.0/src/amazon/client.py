"""Low-level Amazon SP-API client.

Handles authentication, rate limiting, retries, and provides high-level methods
for Orders, Catalog, Feeds, and Reports APIs.
"""

import asyncio
import json
import logging
import time
from typing import Any

import httpx

from src.config import AmazonAccountConfig, settings
from src.amazon.auth import TokenManager
from pinquark_common.monitoring.metrics import setup_metrics

logger = logging.getLogger(__name__)

metrics = setup_metrics("amazon")


class AmazonApiError(Exception):
    def __init__(self, status_code: int, message: str, error_code: str = "", raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.raw = raw or {}
        super().__init__(f"Amazon SP-API {status_code}: {error_code} — {message}")


class AmazonClient:
    """Async HTTP client for Amazon Selling Partner API."""

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
        account: AmazonAccountConfig,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        operation_name: str = "",
    ) -> dict[str, Any]:
        http = self._get_http_client()
        access_token = await self.token_manager.get_access_token(account)

        headers = {
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
            "User-Agent": f"PinquarkIntegrations/1.0 (Language=Python; Platform=Linux)",
        }

        last_response: httpx.Response | None = None
        for attempt in range(settings.max_retries):
            start = time.monotonic()
            last_response = await http.request(
                method, url, headers=headers, params=params, json=json_body,
            )
            duration = time.monotonic() - start

            metrics["external_api_calls_total"].labels(
                system="amazon", operation=operation_name, status=last_response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="amazon", operation=operation_name,
            ).observe(duration)

            if last_response.status_code == 429:
                retry_after = float(last_response.headers.get("Retry-After", "2"))
                rate_limit = last_response.headers.get("x-amzn-RateLimit-Limit", "?")
                logger.warning(
                    "Amazon rate limited (limit=%s), waiting %.1fs (attempt %d/%d)",
                    rate_limit, retry_after, attempt + 1, settings.max_retries,
                )
                await asyncio.sleep(retry_after)
                continue

            if last_response.status_code >= 500:
                backoff = settings.retry_backoff_factor * (2 ** attempt)
                logger.warning(
                    "Amazon %d, retrying in %.1fs (attempt %d/%d)",
                    last_response.status_code, backoff, attempt + 1, settings.max_retries,
                )
                await asyncio.sleep(backoff)
                continue

            break

        if last_response is None:
            raise AmazonApiError(500, "No response received")

        if last_response.status_code >= 400:
            error_body = {}
            try:
                error_body = last_response.json()
            except Exception:
                pass
            errors = error_body.get("errors", [{}])
            first_error = errors[0] if errors else {}
            raise AmazonApiError(
                last_response.status_code,
                first_error.get("message", last_response.text[:200]),
                error_code=first_error.get("code", ""),
                raw=error_body,
            )

        if last_response.status_code == 204:
            return {}

        return last_response.json()

    # -----------------------------------------------------------------------
    # Orders API (v0)
    # -----------------------------------------------------------------------

    async def get_orders(
        self,
        account: AmazonAccountConfig,
        *,
        created_after: str | None = None,
        last_updated_after: str | None = None,
        order_statuses: list[str] | None = None,
        fulfillment_channels: list[str] | None = None,
        next_token: str | None = None,
        max_results: int = 100,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "MarketplaceIds": account.marketplace_id,
            "MaxResultsPerPage": min(max_results, 100),
        }
        if created_after:
            params["CreatedAfter"] = created_after
        if last_updated_after:
            params["LastUpdatedAfter"] = last_updated_after
        if order_statuses:
            params["OrderStatuses"] = ",".join(order_statuses)
        if fulfillment_channels:
            params["FulfillmentChannels"] = ",".join(fulfillment_channels)
        if next_token:
            params["NextToken"] = next_token

        url = f"{account.base_url}/orders/v0/orders"
        result = await self._request("GET", url, account, params=params, operation_name="getOrders")
        return result.get("payload", result)

    async def get_order(self, account: AmazonAccountConfig, order_id: str) -> dict[str, Any]:
        url = f"{account.base_url}/orders/v0/orders/{order_id}"
        result = await self._request("GET", url, account, operation_name="getOrder")
        return result.get("payload", result)

    async def get_order_items(self, account: AmazonAccountConfig, order_id: str) -> dict[str, Any]:
        url = f"{account.base_url}/orders/v0/orders/{order_id}/orderItems"
        result = await self._request("GET", url, account, operation_name="getOrderItems")
        return result.get("payload", result)

    async def get_order_address(self, account: AmazonAccountConfig, order_id: str) -> dict[str, Any]:
        """Restricted operation — requires Restricted Data Token for PII access."""
        url = f"{account.base_url}/orders/v0/orders/{order_id}/address"
        result = await self._request("GET", url, account, operation_name="getOrderAddress")
        return result.get("payload", result)

    async def get_order_buyer_info(self, account: AmazonAccountConfig, order_id: str) -> dict[str, Any]:
        """Restricted operation — requires Restricted Data Token for PII access."""
        url = f"{account.base_url}/orders/v0/orders/{order_id}/buyerInfo"
        result = await self._request("GET", url, account, operation_name="getOrderBuyerInfo")
        return result.get("payload", result)

    # -----------------------------------------------------------------------
    # Catalog Items API (2022-04-01)
    # -----------------------------------------------------------------------

    async def search_catalog_items(
        self,
        account: AmazonAccountConfig,
        *,
        keywords: list[str] | None = None,
        identifiers: list[str] | None = None,
        identifiers_type: str | None = None,
        included_data: list[str] | None = None,
        page_size: int = 20,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "marketplaceIds": account.marketplace_id,
            "pageSize": min(page_size, 20),
        }
        if keywords:
            params["keywords"] = ",".join(keywords)
        if identifiers:
            params["identifiers"] = ",".join(identifiers)
        if identifiers_type:
            params["identifiersType"] = identifiers_type
        if included_data:
            params["includedData"] = ",".join(included_data)

        url = f"{account.base_url}/catalog/2022-04-01/items"
        return await self._request("GET", url, account, params=params, operation_name="searchCatalogItems")

    async def get_catalog_item(
        self,
        account: AmazonAccountConfig,
        asin: str,
        *,
        included_data: list[str] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"marketplaceIds": account.marketplace_id}
        if included_data:
            params["includedData"] = ",".join(included_data)

        url = f"{account.base_url}/catalog/2022-04-01/items/{asin}"
        return await self._request("GET", url, account, params=params, operation_name="getCatalogItem")

    # -----------------------------------------------------------------------
    # Feeds API (2021-06-30)
    # -----------------------------------------------------------------------

    async def create_feed_document(self, account: AmazonAccountConfig, content_type: str = "application/json") -> dict[str, Any]:
        url = f"{account.base_url}/feeds/2021-06-30/documents"
        body = {"contentType": content_type}
        return await self._request("POST", url, account, json_body=body, operation_name="createFeedDocument")

    async def upload_feed_data(self, upload_url: str, data: str | bytes, content_type: str = "application/json") -> None:
        """Upload feed content to the pre-signed S3 URL."""
        http = self._get_http_client()
        body = data.encode("utf-8") if isinstance(data, str) else data
        response = await http.put(upload_url, content=body, headers={"Content-Type": content_type})
        if response.status_code not in (200, 204):
            raise AmazonApiError(response.status_code, f"Feed upload failed: {response.text[:200]}")

    async def create_feed(
        self,
        account: AmazonAccountConfig,
        feed_type: str,
        input_feed_document_id: str,
        marketplace_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        url = f"{account.base_url}/feeds/2021-06-30/feeds"
        body: dict[str, Any] = {
            "feedType": feed_type,
            "inputFeedDocumentId": input_feed_document_id,
            "marketplaceIds": marketplace_ids or [account.marketplace_id],
        }
        return await self._request("POST", url, account, json_body=body, operation_name="createFeed")

    async def get_feed(self, account: AmazonAccountConfig, feed_id: str) -> dict[str, Any]:
        url = f"{account.base_url}/feeds/2021-06-30/feeds/{feed_id}"
        return await self._request("GET", url, account, operation_name="getFeed")

    async def get_feed_document(self, account: AmazonAccountConfig, feed_document_id: str) -> dict[str, Any]:
        url = f"{account.base_url}/feeds/2021-06-30/documents/{feed_document_id}"
        return await self._request("GET", url, account, operation_name="getFeedDocument")

    # -----------------------------------------------------------------------
    # Reports API (2021-06-30)
    # -----------------------------------------------------------------------

    async def create_report(
        self,
        account: AmazonAccountConfig,
        report_type: str,
        *,
        data_start_time: str | None = None,
        data_end_time: str | None = None,
        marketplace_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        url = f"{account.base_url}/reports/2021-06-30/reports"
        body: dict[str, Any] = {
            "reportType": report_type,
            "marketplaceIds": marketplace_ids or [account.marketplace_id],
        }
        if data_start_time:
            body["dataStartTime"] = data_start_time
        if data_end_time:
            body["dataEndTime"] = data_end_time
        return await self._request("POST", url, account, json_body=body, operation_name="createReport")

    async def get_report(self, account: AmazonAccountConfig, report_id: str) -> dict[str, Any]:
        url = f"{account.base_url}/reports/2021-06-30/reports/{report_id}"
        return await self._request("GET", url, account, operation_name="getReport")

    async def get_report_document(self, account: AmazonAccountConfig, report_document_id: str) -> dict[str, Any]:
        url = f"{account.base_url}/reports/2021-06-30/documents/{report_document_id}"
        return await self._request("GET", url, account, operation_name="getReportDocument")

    # -----------------------------------------------------------------------
    # Fulfillment — shipment confirmation via Feeds API
    # -----------------------------------------------------------------------

    async def submit_shipment_confirmation(
        self,
        account: AmazonAccountConfig,
        order_id: str,
        carrier_code: str,
        tracking_number: str,
        ship_date: str,
        carrier_name: str = "",
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Submit order shipment confirmation via POST_ORDER_FULFILLMENT_DATA feed."""
        fulfillment_data: dict[str, Any] = {
            "AmazonOrderID": order_id,
            "FulfillmentDate": ship_date,
            "CarrierCode": carrier_code,
            "ShippingMethod": "Standard",
            "ShipperTrackingNumber": tracking_number,
        }
        if carrier_name:
            fulfillment_data["CarrierName"] = carrier_name
        if items:
            fulfillment_data["Items"] = items

        feed_content = json.dumps({"OrderFulfillment": [fulfillment_data]})

        doc = await self.create_feed_document(account)
        feed_document_id = doc.get("feedDocumentId", doc.get("payload", {}).get("feedDocumentId", ""))
        upload_url = doc.get("url", doc.get("payload", {}).get("url", ""))

        await self.upload_feed_data(upload_url, feed_content)

        result = await self.create_feed(
            account,
            feed_type="POST_ORDER_FULFILLMENT_DATA",
            input_feed_document_id=feed_document_id,
        )
        logger.info("Submitted shipment confirmation feed for order=%s, tracking=%s", order_id, tracking_number)
        return result

    async def submit_order_acknowledgement(
        self,
        account: AmazonAccountConfig,
        order_id: str,
        status_code: str = "Success",
    ) -> dict[str, Any]:
        """Acknowledge an order via POST_ORDER_ACKNOWLEDGEMENT_DATA feed."""
        ack_data = {
            "AmazonOrderID": order_id,
            "StatusCode": status_code,
        }
        feed_content = json.dumps({"OrderAcknowledgement": [ack_data]})

        doc = await self.create_feed_document(account)
        feed_document_id = doc.get("feedDocumentId", doc.get("payload", {}).get("feedDocumentId", ""))
        upload_url = doc.get("url", doc.get("payload", {}).get("url", ""))

        await self.upload_feed_data(upload_url, feed_content)

        result = await self.create_feed(
            account,
            feed_type="POST_ORDER_ACKNOWLEDGEMENT_DATA",
            input_feed_document_id=feed_document_id,
        )
        logger.info("Submitted order acknowledgement feed for order=%s, status=%s", order_id, status_code)
        return result

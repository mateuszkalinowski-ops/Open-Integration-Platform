"""Amazon e-commerce integration — implements the EcommerceIntegration interface."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from pinquark_common.interfaces.ecommerce import EcommerceIntegration
from pinquark_common.schemas.common import SyncResult, SyncStatus
from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    StockItem,
)
from src.config import AmazonAccountConfig
from src.amazon.client import AmazonClient
from src.amazon.mapper import (
    map_amazon_order_to_order,
    map_amazon_status_to_order_status,
    map_catalog_item_to_product,
)
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class AmazonIntegration(EcommerceIntegration):
    """Full Amazon SP-API e-commerce integration supporting multiple seller accounts."""

    def __init__(self, client: AmazonClient, account_manager: AccountManager):
        self._client = client
        self._accounts = account_manager

    def _get_account(self, account_name: str) -> AmazonAccountConfig:
        account = self._accounts.get_account(account_name)
        if not account:
            raise ValueError(f"Account '{account_name}' not found")
        return account

    async def fetch_orders(
        self,
        account_name: str,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> OrdersPage:
        account = self._get_account(account_name)

        created_after = None
        if since:
            created_after = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        all_orders: list[Order] = []
        next_token: str | None = None
        fetched_pages = 0
        target_page_end = page * page_size

        while True:
            resp = await self._client.get_orders(
                account,
                created_after=created_after,
                next_token=next_token,
            )

            amazon_orders = resp.get("Orders", [])
            for order_data in amazon_orders:
                order_id = order_data.get("AmazonOrderId", "")
                try:
                    items_resp = await self._client.get_order_items(account, order_id)
                    order_items = items_resp.get("OrderItems", [])
                except Exception:
                    logger.warning("Failed to fetch items for order=%s, using empty list", order_id)
                    order_items = []

                order = map_amazon_order_to_order(order_data, order_items, account_name)
                all_orders.append(order)

            fetched_pages += 1
            next_token = resp.get("NextToken")

            if not next_token or len(all_orders) >= target_page_end:
                break

            if fetched_pages >= 10:
                break

        start = (page - 1) * page_size
        page_slice = all_orders[start:start + page_size]

        return OrdersPage(
            orders=page_slice,
            page=page,
            total=len(all_orders),
            has_next=next_token is not None or len(all_orders) > start + page_size,
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        account = self._get_account(account_name)

        order_resp = await self._client.get_order(account, order_id)
        items_resp = await self._client.get_order_items(account, order_id)
        order_items = items_resp.get("OrderItems", [])

        return map_amazon_order_to_order(order_resp, order_items, account_name)

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        """Update order status on Amazon.

        Amazon doesn't have a direct "set status" API. Status transitions happen via:
        - Shipped: submit shipment confirmation feed (POST_ORDER_FULFILLMENT_DATA)
        - Cancelled: submit order acknowledgement with Failure status
        - Other statuses: submit order acknowledgement
        """
        account = self._get_account(account_name)

        if status == OrderStatus.SHIPPED:
            logger.info(
                "Order %s status->SHIPPED requires shipment confirmation with tracking. "
                "Use POST /orders/%s/ship endpoint instead.",
                order_id, order_id,
            )
            raise ValueError(
                "To mark as SHIPPED, use the /orders/{order_id}/ship endpoint "
                "with carrier and tracking information."
            )

        if status == OrderStatus.CANCELLED:
            await self._client.submit_order_acknowledgement(account, order_id, status_code="Failure")
            logger.info("Submitted cancellation acknowledgement for order=%s", order_id)
            return

        if status == OrderStatus.PROCESSING:
            await self._client.submit_order_acknowledgement(account, order_id, status_code="Success")
            logger.info("Acknowledged order=%s", order_id)
            return

        logger.warning("Status %s cannot be directly set on Amazon for order=%s", status, order_id)

    async def acknowledge_order(self, account_name: str, order_id: str) -> dict[str, Any]:
        account = self._get_account(account_name)
        result = await self._client.submit_order_acknowledgement(account, order_id, status_code="Success")
        return result

    async def confirm_shipment(
        self,
        account_name: str,
        order_id: str,
        carrier_code: str,
        tracking_number: str,
        ship_date: str | None = None,
        carrier_name: str = "",
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        account = self._get_account(account_name)
        if not ship_date:
            ship_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = await self._client.submit_shipment_confirmation(
            account, order_id, carrier_code, tracking_number, ship_date,
            carrier_name=carrier_name, items=items,
        )
        logger.info("Shipment confirmed for order=%s, carrier=%s, tracking=%s", order_id, carrier_code, tracking_number)
        return result

    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        """Sync stock via Feeds API using POST_INVENTORY_AVAILABILITY_DATA feed."""
        account = self._get_account(account_name)

        inventory_records = []
        for item in items:
            sku = item.sku or item.product_id
            inventory_records.append({
                "sku": sku,
                "quantity": int(item.quantity),
                "fulfillment_channel_code": "DEFAULT",
            })

        feed_content = json.dumps({"inventory": inventory_records})

        try:
            doc = await self._client.create_feed_document(account)
            feed_doc_id = doc.get("feedDocumentId", doc.get("payload", {}).get("feedDocumentId", ""))
            upload_url = doc.get("url", doc.get("payload", {}).get("url", ""))

            await self._client.upload_feed_data(upload_url, feed_content)

            result = await self._client.create_feed(
                account,
                feed_type="POST_INVENTORY_AVAILABILITY_DATA",
                input_feed_document_id=feed_doc_id,
            )

            logger.info("Submitted inventory feed with %d items for account=%s", len(items), account_name)

            return SyncResult(
                status=SyncStatus.SUCCESS,
                total=len(items),
                succeeded=len(items),
                failed=0,
            )
        except Exception as exc:
            logger.warning("Stock sync failed for account=%s: %s", account_name, exc)
            return SyncResult(
                status=SyncStatus.FAILED,
                total=len(items),
                succeeded=0,
                failed=len(items),
                errors=[{"error": str(exc)}],
            )

    async def get_product(self, account_name: str, product_id: str) -> Product:
        """Get product by ASIN from Amazon Catalog API."""
        account = self._get_account(account_name)
        result = await self._client.get_catalog_item(
            account, product_id,
            included_data=["summaries", "identifiers", "images", "attributes"],
        )
        return map_catalog_item_to_product(result)

    async def search_products(
        self,
        account_name: str,
        keywords: list[str] | None = None,
        identifiers: list[str] | None = None,
        identifiers_type: str | None = None,
        page_size: int = 10,
    ) -> list[Product]:
        account = self._get_account(account_name)
        result = await self._client.search_catalog_items(
            account,
            keywords=keywords,
            identifiers=identifiers,
            identifiers_type=identifiers_type,
            included_data=["summaries", "identifiers"],
            page_size=page_size,
        )
        items = result.get("items", [])
        return [map_catalog_item_to_product(item) for item in items]

    async def create_report(
        self,
        account_name: str,
        report_type: str,
        data_start_time: str | None = None,
        data_end_time: str | None = None,
    ) -> dict[str, Any]:
        account = self._get_account(account_name)
        return await self._client.create_report(
            account, report_type,
            data_start_time=data_start_time,
            data_end_time=data_end_time,
        )

    async def get_report(self, account_name: str, report_id: str) -> dict[str, Any]:
        account = self._get_account(account_name)
        return await self._client.get_report(account, report_id)

    async def get_feed_status(self, account_name: str, feed_id: str) -> dict[str, Any]:
        account = self._get_account(account_name)
        return await self._client.get_feed(account, feed_id)

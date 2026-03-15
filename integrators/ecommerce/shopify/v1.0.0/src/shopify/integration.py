"""Shopify e-commerce integration — implements the EcommerceIntegration interface."""

import logging
from datetime import datetime
from typing import Any

from pinquark_common.interfaces.ecommerce import EcommerceIntegration
from pinquark_common.schemas.common import SyncResult, SyncStatus
from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    ProductsPage,
    StockItem,
)

from src.services.account_manager import AccountManager
from src.shopify.client import ShopifyClient
from src.shopify.mapper import (
    ORDER_STATUS_TO_SHOPIFY_ACTION,
    map_product_to_shopify,
    map_shopify_order_to_order,
    map_shopify_product_to_product,
)
from src.shopify.schemas import (
    ShopifyOrder,
    ShopifyOrdersResponse,
    ShopifyProduct,
    ShopifyProductsResponse,
)

logger = logging.getLogger(__name__)


class ShopifyIntegration(EcommerceIntegration):
    """Full Shopify e-commerce integration supporting multiple store accounts."""

    def __init__(self, client: ShopifyClient, account_manager: AccountManager):
        self._client = client
        self._accounts = account_manager

    def _get_account(self, account_name: str):
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

        kwargs: dict[str, Any] = {"limit": page_size, "status": "any"}
        if since:
            kwargs["updated_at_min"] = since.isoformat()

        raw = await self._client.get_orders(account, **kwargs)
        response = ShopifyOrdersResponse.model_validate(raw)

        orders: list[Order] = []
        for shopify_order in response.orders:
            orders.append(map_shopify_order_to_order(shopify_order, account_name))

        total = len(orders)
        return OrdersPage(
            orders=orders,
            page=page,
            total=total,
            has_next=total >= page_size,
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        account = self._get_account(account_name)
        raw = await self._client.get_order(order_id, account)
        shopify_order = ShopifyOrder.model_validate(raw.get("order", raw))
        return map_shopify_order_to_order(shopify_order, account_name)

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
        tracking_number: str = "",
        tracking_company: str = "",
    ) -> None:
        account = self._get_account(account_name)
        action = ORDER_STATUS_TO_SHOPIFY_ACTION.get(status)

        if status == OrderStatus.CANCELLED:
            await self._client.cancel_order(order_id, account)
            logger.info("Cancelled order=%s for account=%s", order_id, account_name)
            return

        if status in (OrderStatus.SHIPPED, OrderStatus.READY_FOR_SHIPMENT):
            await self._create_fulfillment(
                order_id,
                account_name,
                tracking_number,
                tracking_company,
            )
            return

        if status == OrderStatus.DELIVERED:
            await self._client.close_order(order_id, account)
            logger.info("Closed order=%s for account=%s", order_id, account_name)
            return

        logger.info(
            "Order status %s mapped to action=%s for order=%s",
            status,
            action or "none",
            order_id,
        )

    async def _create_fulfillment(
        self,
        order_id: str,
        account_name: str,
        tracking_number: str = "",
        tracking_company: str = "",
    ) -> None:
        """Create fulfillment for all open fulfillment orders."""
        account = self._get_account(account_name)

        fo_raw = await self._client.get_fulfillment_orders(order_id, account)
        fulfillment_orders = fo_raw.get("fulfillment_orders", [])

        open_fo_ids = [fo["id"] for fo in fulfillment_orders if fo.get("status") in ("open", "in_progress")]

        if not open_fo_ids:
            logger.warning("No open fulfillment orders for order=%s", order_id)
            return

        carrier = tracking_company or account.default_carrier
        await self._client.create_fulfillment(
            account,
            fulfillment_order_ids=open_fo_ids,
            tracking_number=tracking_number,
            tracking_company=carrier,
        )
        logger.info(
            "Created fulfillment for order=%s (fo_ids=%s, tracking=%s)",
            order_id,
            open_fo_ids,
            tracking_number,
        )

    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        account = self._get_account(account_name)
        location_id = int(account.default_location_id) if account.default_location_id else None
        if not location_id:
            return SyncResult(
                status=SyncStatus.FAILED,
                total=len(items),
                succeeded=0,
                failed=len(items),
                errors=[{"error": "default_location_id not configured for this account"}],
            )

        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for item in items:
            try:
                inventory_item_id = int(item.product_id) if item.product_id else 0
                if not inventory_item_id:
                    failed += 1
                    errors.append({"sku": item.sku, "error": "Missing inventory_item_id (use product_id field)"})
                    continue

                await self._client.set_inventory_level(
                    account,
                    inventory_item_id=inventory_item_id,
                    location_id=location_id,
                    available=int(item.quantity),
                )
                succeeded += 1
            except Exception as exc:
                failed += 1
                errors.append({"sku": item.sku, "error": str(exc)})
                logger.warning("Stock sync failed for sku=%s: %s", item.sku, exc)

        status = SyncStatus.SUCCESS if failed == 0 else (SyncStatus.PARTIAL if succeeded > 0 else SyncStatus.FAILED)
        return SyncResult(
            status=status,
            total=len(items),
            succeeded=succeeded,
            failed=failed,
            errors=errors,
        )

    async def get_product(self, account_name: str, product_id: str) -> Product:
        account = self._get_account(account_name)
        raw = await self._client.get_product(product_id, account)
        shopify_product = ShopifyProduct.model_validate(raw.get("product", raw))
        return map_shopify_product_to_product(shopify_product)

    async def search_products(
        self,
        account_name: str,
        query: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> ProductsPage:
        account = self._get_account(account_name)
        raw = await self._client.get_products(account, limit=page_size, title=query or None)
        response = ShopifyProductsResponse.model_validate(raw)

        products: list[Product] = []
        for sp in response.products:
            product = map_shopify_product_to_product(sp)
            product.attributes["source"] = "shopify"
            products.append(product)

        total = len(products)
        return ProductsPage(
            products=products,
            page=page,
            total=total,
            has_next=total >= page_size,
            source="shopify",
        )

    async def sync_products(
        self,
        account_name: str,
        products: list[Product],
    ) -> SyncResult:
        account = self._get_account(account_name)
        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for product in products:
            try:
                payload = map_product_to_shopify(product)
                if product.external_id and product.external_id != "0":
                    await self._client.update_product(product.external_id, account, payload)
                else:
                    await self._client.create_product(account, payload)
                succeeded += 1
            except Exception as exc:
                failed += 1
                errors.append({"sku": product.sku, "error": str(exc)})
                logger.warning("Product sync failed for sku=%s: %s", product.sku, exc)

        status = SyncStatus.SUCCESS if failed == 0 else (SyncStatus.PARTIAL if succeeded > 0 else SyncStatus.FAILED)
        return SyncResult(
            status=status,
            total=len(products),
            succeeded=succeeded,
            failed=failed,
            errors=errors,
        )

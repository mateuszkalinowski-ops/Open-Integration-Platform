"""IdoSell e-commerce integration — implements the EcommerceIntegration interface."""

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
    StockItem,
)
from src.config import IdoSellAccountConfig, settings
from src.idosell.client import IdoSellClient
from src.idosell.mapper import (
    map_idosell_order_to_order,
    map_idosell_product_to_product,
    order_status_to_idosell,
)
from src.idosell.schemas import IdoSellOrder, IdoSellProduct
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class IdoSellIntegration(EcommerceIntegration):
    """Full IdoSell e-commerce integration supporting multiple accounts."""

    def __init__(self, client: IdoSellClient, account_manager: AccountManager):
        self._client = client
        self._accounts = account_manager

    def _get_account(self, account_name: str) -> IdoSellAccountConfig:
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

        date_begin = since.strftime(settings.idosell_date_format) if since else None
        ido_page = page - 1  # IdoSell uses 0-based page indexing

        data = await self._client.search_orders(
            account,
            date_begin=date_begin,
            date_type="modified",
            page=ido_page,
            limit=page_size,
        )

        results = data.get("results", [])
        total = data.get("resultsNumberAll", 0)
        total_pages = data.get("resultsNumberPage", 1)

        orders: list[Order] = []
        for order_data in results:
            ido_order = IdoSellOrder.model_validate(order_data)
            orders.append(map_idosell_order_to_order(ido_order, account_name))

        return OrdersPage(
            orders=orders,
            page=page,
            total=total,
            has_next=page < total_pages,
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        account = self._get_account(account_name)

        try:
            serial_number = int(order_id)
            data = await self._client.get_orders(account, serial_numbers=[serial_number])
        except ValueError:
            data = await self._client.get_orders(account, order_ids=[order_id])

        results = data.get("results", [])
        if not results:
            raise ValueError(f"Order '{order_id}' not found")

        ido_order = IdoSellOrder.model_validate(results[0])
        return map_idosell_order_to_order(ido_order, account_name)

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        account = self._get_account(account_name)
        idosell_status = order_status_to_idosell(status)
        serial_number = int(order_id)

        await self._client.update_order_status(account, serial_number, idosell_status)
        logger.info(
            "Updated order=%s to status=%s (idosell=%s) for account=%s",
            order_id, status.value, idosell_status, account_name,
        )

    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        account = self._get_account(account_name)
        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        batch_size = 50
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            products_payload = [
                {
                    "productIndex": item.sku,
                    "productSizeCodeExternal": item.ean or "",
                    "stockId": int(item.warehouse_id) if item.warehouse_id else account.default_stock_id,
                    "productSizeQuantity": item.quantity,
                }
                for item in batch
            ]
            try:
                await self._client.update_stock_quantity(account, products_payload)
                succeeded += len(batch)
            except Exception as exc:
                failed += len(batch)
                errors.append({"batch_index": i, "error": str(exc)})
                logger.warning("Stock sync batch failed at index %d: %s", i, exc)

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
        data = await self._client.get_products(account, [int(product_id)])
        results = data.get("results", [])
        if not results:
            raise ValueError(f"Product '{product_id}' not found")

        ido_product = IdoSellProduct.model_validate(results[0])
        return map_idosell_product_to_product(ido_product)

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
                body = {
                    "settings": {"settingModificationType": "edit"},
                    "products": [{
                        "productId": int(product.external_id) if product.external_id else None,
                        "productDisplayedCode": product.sku,
                    }],
                }
                resp = await self._client.put("products/products", account, json_data=body)
                resp.raise_for_status()
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

    async def create_parcel(
        self,
        account_name: str,
        order_serial_number: int,
        courier_id: int,
        tracking_numbers: list[str],
    ) -> dict[str, Any]:
        """Create shipping packages for an order."""
        account = self._get_account(account_name)
        return await self._client.create_package(
            account, order_serial_number, courier_id, tracking_numbers,
        )

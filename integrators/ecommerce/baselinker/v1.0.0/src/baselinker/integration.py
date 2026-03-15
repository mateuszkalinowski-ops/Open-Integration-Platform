"""BaseLinker e-commerce integration — implements the EcommerceIntegration interface."""

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

from src.baselinker.client import BaseLinkerClient
from src.baselinker.mapper import (
    find_bl_status_id,
    map_bl_order_to_order,
    map_bl_product_to_product,
)
from src.config import BaseLinkerAccountConfig
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class BaseLinkerIntegration(EcommerceIntegration):
    """Full BaseLinker e-commerce integration supporting multiple accounts."""

    def __init__(self, client: BaseLinkerClient, account_manager: AccountManager):
        self._client = client
        self._accounts = account_manager
        self._status_cache: dict[str, dict[int, str]] = {}

    def _get_account(self, account_name: str) -> BaseLinkerAccountConfig:
        account = self._accounts.get_account(account_name)
        if not account:
            raise ValueError(f"Account '{account_name}' not found")
        return account

    async def _get_status_defs(self, account: BaseLinkerAccountConfig) -> dict[int, str]:
        if account.name not in self._status_cache:
            resp = await self._client.get_order_status_list(account)
            statuses = resp.get("statuses", [])
            self._status_cache[account.name] = {s["id"]: s["name"] for s in statuses}
        return self._status_cache[account.name]

    async def fetch_orders(
        self,
        account_name: str,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> OrdersPage:
        account = self._get_account(account_name)
        status_defs = await self._get_status_defs(account)

        params: dict[str, Any] = {}
        if since:
            params["date_confirmed_from"] = int(since.timestamp())

        resp = await self._client.get_orders(account, **params)
        bl_orders = resp.get("orders", [])

        orders: list[Order] = []
        for od in bl_orders:
            orders.append(map_bl_order_to_order(od, account_name, status_defs))

        start = (page - 1) * page_size
        page_slice = orders[start : start + page_size]
        has_next = len(bl_orders) == 100

        return OrdersPage(
            orders=page_slice,
            page=page,
            total=len(bl_orders),
            has_next=has_next,
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        account = self._get_account(account_name)
        status_defs = await self._get_status_defs(account)

        resp = await self._client.get_orders(account, date_from=0)
        bl_orders = resp.get("orders", [])
        for od in bl_orders:
            if str(od.get("order_id")) == order_id:
                return map_bl_order_to_order(od, account_name, status_defs)

        raise ValueError(f"Order '{order_id}' not found")

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        account = self._get_account(account_name)
        status_defs = await self._get_status_defs(account)
        bl_status_id = find_bl_status_id(status, status_defs)

        if bl_status_id is None:
            raise ValueError(f"Cannot map {status.value} to any BaseLinker status. Available: {status_defs}")

        await self._client.set_order_status(account, int(order_id), bl_status_id)
        logger.info("Updated order=%s to status=%s (bl_id=%d)", order_id, status, bl_status_id)

    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        account = self._get_account(account_name)
        inv_id = account.inventory_id
        wh_id = account.warehouse_id

        if not inv_id:
            return SyncResult(
                status=SyncStatus.FAILED,
                total=len(items),
                succeeded=0,
                failed=len(items),
                errors=[{"error": "inventory_id not configured"}],
            )

        batch: dict[str, dict[str, float]] = {}
        for item in items:
            pid = item.product_id or item.sku
            batch[pid] = {str(wh_id): item.quantity}

        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for i in range(0, len(batch), 1000):
            chunk = dict(list(batch.items())[i : i + 1000])
            try:
                await self._client.update_inventory_products_stock(account, inv_id, chunk)
                succeeded += len(chunk)
            except Exception as exc:
                failed += len(chunk)
                errors.append({"batch_start": i, "error": str(exc)})
                logger.warning("Stock sync batch failed: %s", exc)

        status = SyncStatus.SUCCESS if failed == 0 else (SyncStatus.PARTIAL if succeeded > 0 else SyncStatus.FAILED)
        return SyncResult(status=status, total=len(items), succeeded=succeeded, failed=failed, errors=errors)

    async def get_product(self, account_name: str, product_id: str) -> Product:
        account = self._get_account(account_name)
        inv_id = account.inventory_id
        if not inv_id:
            raise ValueError("inventory_id not configured")

        resp = await self._client.get_inventory_products_data(account, inv_id, [int(product_id)])
        products = resp.get("products", {})
        data = products.get(product_id)
        if not data:
            raise ValueError(f"Product '{product_id}' not found")

        return map_bl_product_to_product(product_id, data, account.warehouse_id)

    async def search_products(
        self,
        account_name: str,
        query: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> ProductsPage:
        account = self._get_account(account_name)
        inv_id = account.inventory_id
        if not inv_id:
            raise ValueError("inventory_id not configured")

        resp = await self._client.get_inventory_products_list(account, inv_id, page=page)
        raw_products = resp.get("products", {})

        product_ids = list(raw_products.keys())
        if not product_ids:
            return ProductsPage(products=[], page=page, total=0, has_next=False, source="baselinker")

        data_resp = await self._client.get_inventory_products_data(
            account, inv_id, [int(pid) for pid in product_ids[:page_size]]
        )
        products_data = data_resp.get("products", {})

        products: list[Product] = []
        for pid, pdata in products_data.items():
            product = map_bl_product_to_product(pid, pdata, account.warehouse_id)
            if query and query.lower() not in product.name.lower():
                continue
            product.attributes["source"] = "baselinker"
            products.append(product)

        return ProductsPage(
            products=products,
            page=page,
            total=len(products),
            has_next=len(raw_products) >= 1000,
            source="baselinker",
        )

    async def create_parcel(
        self,
        account_name: str,
        order_id: int,
        courier_code: str,
        package_number: str,
    ) -> dict[str, Any]:
        account = self._get_account(account_name)
        resp = await self._client.create_package_manual(account, order_id, courier_code, package_number)
        logger.info(
            "Created manual package for order=%d, courier=%s, number=%s", order_id, courier_code, package_number
        )
        return resp

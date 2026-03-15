"""Shoper e-commerce integration — implements the EcommerceIntegration interface."""

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

from src.config import ShoperAccountConfig
from src.services.account_manager import AccountManager
from src.shoper.client import ShoperClient
from src.shoper.mapper import (
    map_shoper_order_to_order,
    map_shoper_product_to_product,
    order_status_to_shoper,
)

logger = logging.getLogger(__name__)


class ShoperIntegration(EcommerceIntegration):
    """Full Shoper e-commerce integration supporting multiple accounts."""

    def __init__(self, client: ShoperClient, account_manager: AccountManager):
        self._client = client
        self._accounts = account_manager

    def _get_account(self, account_name: str) -> ShoperAccountConfig:
        account = self._accounts.get_account(account_name)
        if not account:
            raise ValueError(f"Account '{account_name}' not found")
        return account

    def _creds(self, account: ShoperAccountConfig) -> tuple[str, str, str, str]:
        return account.name, account.shop_url, account.login, account.password

    async def fetch_orders(
        self,
        account_name: str,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> OrdersPage:
        account = self._get_account(account_name)
        filters: dict[str, dict[str, Any]] = {}
        if since:
            filters["status_date"] = {">=": since.strftime("%Y-%m-%d %H:%M:%S")}

        params: dict[str, Any] = {"page": page}
        if filters:
            import json

            params["filters"] = json.dumps(filters)

        resp = await self._client.get("orders", *self._creds(account), params=params)
        resp.raise_for_status()
        data = resp.json()

        order_list = data.get("list", [])
        order_ids = [str(o.get("order_id")) for o in order_list]

        order_products_raw = await self._client.get_bulk(
            "order-products",
            *self._creds(account),
            filters={"order_id": {"IN": order_ids}} if order_ids else None,
        )
        products_by_order: dict[str, list[dict[str, Any]]] = {}
        for p in order_products_raw:
            oid = str(p.get("order_id"))
            products_by_order.setdefault(oid, []).append(p)

        orders: list[Order] = []
        for od in order_list:
            oid = str(od.get("order_id"))
            orders.append(map_shoper_order_to_order(od, products_by_order.get(oid, []), account_name))

        total = data.get("count", len(orders))
        return OrdersPage(
            orders=orders,
            page=page,
            total=total,
            has_next=page < data.get("pages", 1),
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        account = self._get_account(account_name)
        order_data = await self._client.get_one("orders", int(order_id), *self._creds(account))

        order_products = await self._client.get_bulk(
            "order-products",
            *self._creds(account),
            filters={"order_id": {"=": int(order_id)}},
        )
        return map_shoper_order_to_order(order_data, order_products, account_name)

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        account = self._get_account(account_name)
        shoper_status = order_status_to_shoper(status)

        resp = await self._client.update_entity(
            "orders",
            int(order_id),
            {"status_id": shoper_status},
            *self._creds(account),
        )
        resp.raise_for_status()
        logger.info("Updated order=%s to status=%s (shoper=%s)", order_id, status, shoper_status)

    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        account = self._get_account(account_name)
        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for item in items:
            try:
                product_id = int(item.product_id or item.sku)
                resp = await self._client.update_entity(
                    "products",
                    product_id,
                    {"stock": {"stock": item.quantity}},
                    *self._creds(account),
                )
                resp.raise_for_status()
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
        product_data = await self._client.get_one("products", int(product_id), *self._creds(account))
        return map_shoper_product_to_product(product_data, account.language_id)

    async def search_products(
        self,
        account_name: str,
        query: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> ProductsPage:
        account = self._get_account(account_name)
        import json as _json

        filters: dict[str, dict[str, Any]] = {}
        if query:
            filters["translations.name"] = {"LIKE": f"%{query}%"}

        params: dict[str, Any] = {"page": page, "limit": page_size}
        if filters:
            params["filters"] = _json.dumps(filters)

        resp = await self._client.get("products", *self._creds(account), params=params)
        resp.raise_for_status()
        data = resp.json()

        product_list = data.get("list", [])
        products: list[Product] = []
        for pd in product_list:
            product = map_shoper_product_to_product(pd, account.language_id)
            product.attributes["source"] = "shoper"
            products.append(product)

        total = data.get("count", len(products))
        return ProductsPage(
            products=products,
            page=page,
            total=total,
            has_next=page < data.get("pages", 1),
            source="shoper",
        )

    async def create_parcel(
        self,
        account_name: str,
        order_id: int,
        waybill: str | None = None,
        shipping_id: int | None = None,
        is_sent: bool = False,
    ) -> int:
        """Create a parcel for an order in Shoper."""
        account = self._get_account(account_name)

        if shipping_id is None:
            order = await self._client.get_one("orders", order_id, *self._creds(account))
            shipping_id = order.get("shipping_id")

        parcel_data: dict[str, Any] = {
            "order_id": order_id,
            "shipping_id": shipping_id,
            "sent": 1 if is_sent else 0,
        }
        if waybill:
            parcel_data["shipping_code"] = waybill

        resp = await self._client.create_entity("parcels", parcel_data, *self._creds(account))
        resp.raise_for_status()
        return resp.json()

    async def update_parcel(
        self,
        account_name: str,
        order_id: int,
        waybill: str | None = None,
        is_sent: bool | None = None,
    ) -> None:
        """Update an existing parcel for an order."""
        account = self._get_account(account_name)

        parcels = await self._client.get_paged(
            "parcels",
            *self._creds(account),
            filters={"order_id": {"=": order_id}},
        )
        if not parcels:
            raise ValueError(f"No parcels found for order {order_id}")

        parcel_id = parcels[0].get("parcel_id")
        update_data: dict[str, Any] = {}
        if waybill is not None:
            update_data["shipping_code"] = waybill
        if is_sent is not None:
            update_data["sent"] = 1 if is_sent else 0

        if update_data:
            resp = await self._client.update_entity("parcels", parcel_id, update_data, *self._creds(account))
            resp.raise_for_status()

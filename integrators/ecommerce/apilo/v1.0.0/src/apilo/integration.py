"""Apilo e-commerce integration — implements the EcommerceIntegration interface."""

import logging
from datetime import UTC, datetime
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

from src.apilo.client import ApiloClient
from src.apilo.mapper import (
    map_apilo_order_to_order,
    map_apilo_product_to_product,
    map_order_status_to_apilo,
)
from src.config import ApiloAccountConfig
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class ApiloIntegration(EcommerceIntegration):
    """Full Apilo e-commerce integration supporting multiple accounts."""

    def __init__(self, client: ApiloClient, account_manager: AccountManager):
        self._client = client
        self._accounts = account_manager
        self._status_maps: dict[str, list[dict[str, Any]]] = {}

    def _get_account(self, account_name: str) -> ApiloAccountConfig:
        account = self._accounts.get_account(account_name)
        if not account:
            raise ValueError(f"Account '{account_name}' not found")
        return account

    async def _get_status_map(self, account_name: str) -> list[dict[str, Any]]:
        if account_name not in self._status_maps:
            account = self._get_account(account_name)
            try:
                self._status_maps[account_name] = await self._client.get_status_map(account)
            except Exception:
                logger.warning("Failed to load status map for account=%s", account_name)
                self._status_maps[account_name] = []
        return self._status_maps[account_name]

    def _get_status_name(self, status_id: int, status_map: list[dict[str, Any]]) -> str:
        for entry in status_map:
            if int(entry.get("id", 0)) == status_id:
                return entry.get("name", "")
        return ""

    async def fetch_orders(
        self,
        account_name: str,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> OrdersPage:
        account = self._get_account(account_name)
        status_map = await self._get_status_map(account_name)

        params: dict[str, Any] = {}
        if since:
            params["updated_after"] = since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+0000")

        offset = (page - 1) * page_size
        resp = await self._client.get_orders(
            account,
            updated_after=params.get("updated_after"),
            offset=offset,
            limit=page_size,
            sort="updatedAtDesc",
        )

        apilo_orders = resp.get("orders", [])
        total_count = resp.get("totalCount", 0)

        orders: list[Order] = []
        for order_data in apilo_orders:
            status_id = order_data.get("status", 0)
            status_name = self._get_status_name(status_id, status_map)
            order = map_apilo_order_to_order(order_data, account_name, status_name)
            orders.append(order)

        return OrdersPage(
            orders=orders,
            page=page,
            total=total_count,
            has_next=(offset + len(orders)) < total_count,
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        account = self._get_account(account_name)
        status_map = await self._get_status_map(account_name)

        order_data = await self._client.get_order(account, order_id)
        status_id = order_data.get("status", 0)
        status_name = self._get_status_name(status_id, status_map)

        return map_apilo_order_to_order(order_data, account_name, status_name)

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        account = self._get_account(account_name)
        status_map = await self._get_status_map(account_name)

        apilo_status_id = map_order_status_to_apilo(status, status_map)
        if apilo_status_id is None:
            raise ValueError(
                f"Cannot map status '{status}' to Apilo status ID. "
                f"Available statuses: {[s.get('name') for s in status_map]}"
            )

        await self._client.update_order_status(account, order_id, apilo_status_id)
        logger.info("Updated order=%s status to %s (apilo_id=%d)", order_id, status, apilo_status_id)

    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        """Sync stock via Apilo PATCH products endpoint."""
        account = self._get_account(account_name)

        patch_data = []
        for item in items:
            entry: dict[str, Any] = {"quantity": int(item.quantity)}
            if item.sku:
                entry["sku"] = item.sku
            if item.product_id:
                try:
                    entry["id"] = int(item.product_id)
                except (ValueError, TypeError):
                    entry["originalCode"] = item.product_id
            patch_data.append(entry)

        try:
            await self._client.patch_products(account, patch_data)
            logger.info("Stock sync completed: %d items for account=%s", len(items), account_name)
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
        account = self._get_account(account_name)
        result = await self._client.get_product(account, int(product_id))
        return map_apilo_product_to_product(result)

    async def search_products(
        self,
        account_name: str,
        query: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> ProductsPage:
        account = self._get_account(account_name)
        offset = (page - 1) * page_size

        kwargs: dict[str, Any] = {"offset": offset, "limit": page_size}
        if query:
            kwargs["name"] = query

        resp = await self._client.get_products(account, **kwargs)
        apilo_products = resp.get("products", [])
        total = resp.get("totalCount", 0)

        products = [map_apilo_product_to_product(p) for p in apilo_products]
        return ProductsPage(
            products=products,
            page=page,
            total=total,
            has_next=(offset + len(products)) < total,
            source="apilo",
        )

    async def sync_products(
        self,
        account_name: str,
        products: list[Product],
    ) -> SyncResult:
        account = self._get_account(account_name)

        product_data = []
        for p in products:
            entry: dict[str, Any] = {
                "sku": p.sku,
                "name": p.name,
                "quantity": int(p.stock_quantity),
                "priceWithTax": str(p.price),
                "tax": p.attributes.get("tax", "23"),
                "status": 1,
            }
            if p.ean:
                entry["ean"] = p.ean
            if p.description:
                entry["description"] = p.description
            if p.external_id:
                entry["originalCode"] = p.external_id
            product_data.append(entry)

        try:
            await self._client.create_products(account, product_data)
            return SyncResult(
                status=SyncStatus.SUCCESS,
                total=len(products),
                succeeded=len(products),
                failed=0,
            )
        except Exception as exc:
            logger.warning("Product sync failed for account=%s: %s", account_name, exc)
            return SyncResult(
                status=SyncStatus.FAILED,
                total=len(products),
                succeeded=0,
                failed=len(products),
                errors=[{"error": str(exc)}],
            )

    # -----------------------------------------------------------------------
    # Apilo-specific operations
    # -----------------------------------------------------------------------

    async def create_order(self, account_name: str, order_data: dict[str, Any]) -> dict[str, Any]:
        account = self._get_account(account_name)
        return await self._client.create_order(account, order_data)

    async def add_order_payment(
        self,
        account_name: str,
        order_id: str,
        payment_data: dict[str, Any],
    ) -> Any:
        account = self._get_account(account_name)
        return await self._client.add_order_payment(account, order_id, payment_data)

    async def add_order_note(
        self,
        account_name: str,
        order_id: str,
        comment: str,
        note_type: int = 2,
    ) -> Any:
        account = self._get_account(account_name)
        return await self._client.add_order_note(account, order_id, comment, note_type)

    async def add_order_shipment(
        self,
        account_name: str,
        order_id: str,
        shipment_data: dict[str, Any],
    ) -> dict[str, Any]:
        account = self._get_account(account_name)
        return await self._client.add_order_shipment(account, order_id, shipment_data)

    async def manage_order_tag(
        self,
        account_name: str,
        order_id: str,
        tag_id: int,
        *,
        remove: bool = False,
    ) -> Any:
        account = self._get_account(account_name)
        if remove:
            return await self._client.delete_order_tag(account, order_id, str(tag_id))
        return await self._client.create_order_tag(account, order_id, tag_id)

    async def get_maps(self, account_name: str) -> dict[str, Any]:
        """Fetch all reference maps (statuses, payment types, carriers, platforms, tags)."""
        account = self._get_account(account_name)
        return {
            "statuses": await self._client.get_status_map(account),
            "payment_types": await self._client.get_payment_types(account),
            "carriers": await self._client.get_carrier_map(account),
            "carrier_accounts": await self._client.get_carrier_accounts(account),
            "platforms": await self._client.get_platform_map(account),
            "tags": await self._client.get_tag_map(account),
            "document_types": await self._client.get_document_types_map(account),
        }

    async def create_shipment(self, account_name: str, shipment_data: dict[str, Any]) -> dict[str, Any]:
        account = self._get_account(account_name)
        return await self._client.create_shipment(account, shipment_data)

    async def get_shipment(self, account_name: str, shipment_id: str) -> dict[str, Any]:
        account = self._get_account(account_name)
        return await self._client.get_shipment(account, shipment_id)

"""WooCommerce e-commerce integration — implements the EcommerceIntegration interface."""

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
from src.woocommerce.client import WooCommerceClient
from src.woocommerce.mapper import (
    map_woo_order_to_order,
    map_woo_product_to_product,
    order_status_to_woo_status,
)
from src.woocommerce.schemas import WooOrder, WooProduct
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class WooCommerceIntegration(EcommerceIntegration):
    """Full WooCommerce e-commerce integration supporting multiple store accounts."""

    def __init__(self, client: WooCommerceClient, account_manager: AccountManager):
        self._client = client
        self._accounts = account_manager

    def _get_account(self, account_name: str):  # noqa: ANN202
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
        status: str | None = None,
        *,
        customer: int | None = None,
        product: int | None = None,
        after: str | None = None,
        before: str | None = None,
    ) -> OrdersPage:
        self._get_account(account_name)

        modified_after = since.isoformat() if since else None

        raw_orders = await self._client.list_orders(
            account_name=account_name,
            per_page=page_size,
            page=page,
            status=status,
            modified_after=modified_after,
            customer=customer,
            product=product,
            after=after,
            before=before,
        )

        orders: list[Order] = []
        for raw in raw_orders:
            woo_order = WooOrder.model_validate(raw)
            orders.append(map_woo_order_to_order(woo_order, account_name))

        has_next = len(raw_orders) >= page_size
        return OrdersPage(
            orders=orders,
            page=page,
            total=len(orders) if not has_next else page * page_size + 1,
            has_next=has_next,
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        self._get_account(account_name)
        raw = await self._client.get_order(int(order_id), account_name)
        woo_order = WooOrder.model_validate(raw)
        return map_woo_order_to_order(woo_order, account_name)

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        self._get_account(account_name)
        woo_status = order_status_to_woo_status(status)
        await self._client.update_order(
            int(order_id), account_name, {"status": woo_status.value},
        )
        logger.info("Updated order=%s to status=%s (woo=%s)", order_id, status, woo_status.value)

    async def sync_stock(
        self,
        account_name: str,
        items: list[StockItem],
    ) -> SyncResult:
        self._get_account(account_name)
        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for item in items:
            try:
                product_id = int(item.product_id) if item.product_id else None
                if not product_id and item.sku:
                    product_id = await self._find_product_id_by_sku(account_name, item.sku)
                if not product_id:
                    raise ValueError(f"Cannot resolve product for sku={item.sku}, product_id={item.product_id}")

                await self._client.update_product_stock(
                    product_id, int(item.quantity), account_name,
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
        self._get_account(account_name)
        raw = await self._client.get_product(int(product_id), account_name)
        woo_product = WooProduct.model_validate(raw)
        return map_woo_product_to_product(woo_product)

    async def search_products(
        self,
        account_name: str,
        query: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> ProductsPage:
        self._get_account(account_name)

        raw_products = await self._client.list_products(
            account_name=account_name,
            per_page=page_size,
            page=page,
            search=query or None,
        )

        products: list[Product] = []
        for raw in raw_products:
            woo_product = WooProduct.model_validate(raw)
            product = map_woo_product_to_product(woo_product)
            product.attributes["source"] = "woocommerce"
            products.append(product)

        has_next = len(raw_products) >= page_size
        return ProductsPage(
            products=products,
            page=page,
            total=len(products) if not has_next else page * page_size + 1,
            has_next=has_next,
            source="woocommerce",
        )

    async def upload_invoice(
        self,
        account_name: str,
        order_id: str,
        invoice_file: bytes,
        invoice_filename: str = "invoice.pdf",
        customer_note: bool = False,
    ) -> dict[str, Any]:
        """Upload an invoice PDF and attach it to a WooCommerce order.

        1. Uploads the PDF via wp/v2/media
        2. Stores the media URL as order meta (_invoice_url)
        3. Adds an order note with a link to the invoice
        """
        self._get_account(account_name)
        oid = int(order_id)

        media = await self._client.upload_media(
            account_name, invoice_file, invoice_filename,
        )
        media_url = media.get("source_url", "")
        media_id = media.get("id", "")

        await self._client.update_order_meta(
            oid, account_name, "_invoice_url", media_url,
        )
        await self._client.update_order_meta(
            oid, account_name, "_invoice_media_id", str(media_id),
        )

        note_text = f"Faktura: {invoice_filename} — {media_url}"
        await self._client.create_order_note(
            oid, account_name, note_text, customer_note=customer_note,
        )

        logger.info("Uploaded invoice=%s for order=%s, media_id=%s", invoice_filename, order_id, media_id)
        return {
            "media_id": media_id,
            "media_url": media_url,
            "filename": invoice_filename,
        }

    async def sync_products(
        self,
        account_name: str,
        products: list[Product],
    ) -> SyncResult:
        self._get_account(account_name)
        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for product in products:
            try:
                data: dict[str, Any] = {
                    "name": product.name,
                    "sku": product.sku,
                    "regular_price": str(product.price) if product.price else "",
                    "description": product.description,
                }
                if product.stock_quantity is not None:
                    data["manage_stock"] = True
                    data["stock_quantity"] = int(product.stock_quantity)

                if product.external_id:
                    await self._client.update_product(int(product.external_id), account_name, data)
                else:
                    await self._client.create_product(account_name, data)
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

    async def _find_product_id_by_sku(self, account_name: str, sku: str) -> int | None:
        """Look up a product ID by SKU via the WooCommerce API."""
        products = await self._client.list_products(account_name, sku=sku, per_page=1)
        if products:
            return products[0].get("id")
        return None

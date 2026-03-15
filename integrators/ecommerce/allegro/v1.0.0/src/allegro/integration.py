"""Allegro e-commerce integration — implements the EcommerceIntegration interface."""

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

from src.allegro.client import AllegroClient
from src.allegro.mapper import (
    extract_ean_from_parameters,
    map_checkout_to_order,
    order_status_to_fulfillment,
)
from src.allegro.schemas import AllegroCheckoutForm
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class AllegroIntegration(EcommerceIntegration):
    """Full Allegro e-commerce integration supporting multiple accounts."""

    def __init__(self, client: AllegroClient, account_manager: AccountManager):
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
        params: dict[str, Any] = {
            "offset": (page - 1) * page_size,
            "limit": page_size,
        }
        if since:
            params["updatedAt.gte"] = since.isoformat()

        resp = await self._client.get(
            "order/checkout-forms",
            account.name,
            account.client_id,
            account.client_secret,
            account.api_url,
            account.auth_url,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

        orders: list[Order] = []
        for checkout_data in data.get("checkoutForms", []):
            checkout = AllegroCheckoutForm.model_validate(checkout_data)
            orders.append(map_checkout_to_order(checkout, account_name))

        total = data.get("count", len(orders))
        return OrdersPage(
            orders=orders,
            page=page,
            total=total,
            has_next=(page * page_size) < total,
        )

    async def get_order(self, account_name: str, order_id: str) -> Order:
        account = self._get_account(account_name)
        checkout_data = await self._client.get_checkout_form(
            order_id,
            account.name,
            account.client_id,
            account.client_secret,
            account.api_url,
            account.auth_url,
        )
        checkout = AllegroCheckoutForm.model_validate(checkout_data)
        return map_checkout_to_order(checkout, account_name)

    async def update_order_status(
        self,
        account_name: str,
        order_id: str,
        status: OrderStatus,
    ) -> None:
        account = self._get_account(account_name)
        fulfillment = order_status_to_fulfillment(status)
        await self._client.update_fulfillment_status(
            order_id,
            fulfillment.value,
            account.name,
            account.client_id,
            account.client_secret,
            account.api_url,
            account.auth_url,
        )
        logger.info("Updated order=%s to status=%s (fulfillment=%s)", order_id, status, fulfillment)

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
                await self._client.update_offer_stock(
                    item.product_id or item.sku,
                    int(item.quantity),
                    account.name,
                    account.client_id,
                    account.client_secret,
                    account.api_url,
                    account.auth_url,
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
        offer_data = await self._client.get_offer(
            product_id,
            account.name,
            account.client_id,
            account.client_secret,
            account.api_url,
            account.auth_url,
        )
        ean = extract_ean_from_parameters(offer_data.get("parameters", []))
        return Product(
            external_id=offer_data["id"],
            sku=offer_data.get("external", {}).get("id", "") if offer_data.get("external") else "",
            ean=ean,
            name=offer_data.get("name", ""),
        )

    async def upload_invoice(
        self,
        account_name: str,
        order_id: str,
        invoice_file: bytes,
        invoice_filename: str = "invoice.pdf",
        invoice_number: str = "",
    ) -> dict:
        """Upload an invoice PDF to an Allegro order (two-step process).

        Step 1: POST metadata (invoiceNumber + file name) → returns invoiceId
        Step 2: PUT binary PDF to /invoices/{invoiceId}/file
        """
        account = self._get_account(account_name)
        auth_args = (account.name, account.client_id, account.client_secret, account.api_url, account.auth_url)

        meta = await self._client.create_invoice_metadata(
            order_id,
            invoice_number or invoice_filename,
            invoice_filename,
            *auth_args,
        )
        invoice_id = meta["id"]

        await self._client.upload_invoice_file(
            order_id,
            invoice_id,
            invoice_file,
            *auth_args,
        )

        logger.info(
            "Uploaded invoice=%s (id=%s) for order=%s",
            invoice_filename,
            invoice_id,
            order_id,
        )
        return {"invoice_id": invoice_id, "filename": invoice_filename}

    async def get_order_invoices(self, account_name: str, order_id: str) -> dict:
        """Retrieve invoice details for an Allegro order."""
        account = self._get_account(account_name)
        return await self._client.get_order_invoices(
            order_id,
            account.name,
            account.client_id,
            account.client_secret,
            account.api_url,
            account.auth_url,
        )

    async def search_products(
        self,
        account_name: str,
        query: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> ProductsPage:
        account = self._get_account(account_name)
        offset = (page - 1) * page_size

        data = await self._client.search_offers(
            phrase=query,
            account_name=account.name,
            client_id=account.client_id,
            client_secret=account.client_secret,
            api_url=account.api_url,
            auth_url=account.auth_url,
            limit=page_size,
            offset=offset,
        )

        items = data.get("items", {})
        promoted = items.get("promoted", [])
        regular = items.get("regular", [])
        all_offers = promoted + regular

        products: list[Product] = []
        for offer in all_offers:
            price_data = offer.get("sellingMode", {}).get("price", {})
            products.append(
                Product(
                    external_id=offer.get("id", ""),
                    name=offer.get("name", ""),
                    price=float(price_data.get("amount", 0)),
                    currency=price_data.get("currency", "PLN"),
                    attributes={"url": offer.get("url", ""), "source": "allegro"},
                )
            )

        total = data.get("searchMeta", {}).get("totalCount", len(products))
        return ProductsPage(
            products=products,
            page=page,
            total=total,
            has_next=(offset + page_size) < total,
            source="allegro",
        )

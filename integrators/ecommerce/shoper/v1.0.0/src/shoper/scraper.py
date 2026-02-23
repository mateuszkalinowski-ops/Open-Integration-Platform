"""Background scraper — polls Shoper for new orders, products, and users."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from src.config import ShoperAccountConfig, settings
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.shoper.client import ShoperClient
from src.shoper.mapper import map_shoper_order_to_order, map_shoper_product_to_product
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


class ShoperScraper:
    """Periodically fetches new data from all configured Shoper accounts."""

    def __init__(
        self,
        client: ShoperClient,
        account_manager: AccountManager,
        state_store: StateStore,
        kafka_producer: KafkaMessageProducer | None = None,
    ):
        self._client = client
        self._accounts = account_manager
        self._state = state_store
        self._kafka = kafka_producer
        self._running = False
        self._last_timestamps: dict[str, dict[str, str]] = {}

    async def start(self) -> None:
        self._running = True
        self._last_timestamps = await self._state.load_all_timestamps()
        logger.info(
            "Shoper scraper started, interval=%ds, accounts=%d",
            settings.scraping_interval_seconds,
            len(self._accounts.list_accounts()),
        )
        while self._running:
            await self._scrape_all_accounts()
            await asyncio.sleep(settings.scraping_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        logger.info("Shoper scraper stopped")

    async def _scrape_all_accounts(self) -> None:
        for account in self._accounts.list_accounts():
            try:
                await self._scrape_account(account)
            except Exception:
                logger.exception("Error scraping account=%s", account.name)

    async def _scrape_account(self, account: ShoperAccountConfig) -> None:
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        if settings.scrape_orders:
            await self._scrape_orders(account, now_str)
        if settings.scrape_products:
            await self._scrape_products(account, now_str)
        if settings.scrape_users:
            await self._scrape_users(account, now_str)

    async def _scrape_orders(self, account: ShoperAccountConfig, now_str: str) -> None:
        last = self._get_last_timestamp(account.name, "orders")
        filters: dict[str, dict[str, Any]] = {}
        if last:
            filters["status_date"] = {">=": last, "<": now_str}

        orders = await self._client.get_paged(
            "orders", account.name, account.shop_url, account.login, account.password,
            filters=filters,
            order=["status_date"],
        )
        if not orders:
            await self._save_timestamp(account.name, "orders", now_str)
            return

        order_ids = [str(o.get("order_id")) for o in orders]
        order_products = await self._client.get_bulk(
            "order-products", account.name, account.shop_url, account.login, account.password,
            filters={"order_id": {"IN": order_ids}},
        )
        products_by_order: dict[str, list[dict[str, Any]]] = {}
        for p in order_products:
            oid = str(p.get("order_id"))
            products_by_order.setdefault(oid, []).append(p)

        for order_data in orders:
            oid = str(order_data.get("order_id"))
            prods = products_by_order.get(oid, [])
            order = map_shoper_order_to_order(order_data, prods, account.name)

            if self._kafka:
                await self._kafka.send(
                    settings.kafka_topic_orders_out,
                    order.model_dump(mode="json"),
                    key=order.external_id,
                )

        logger.info("Scraped %d orders for account=%s", len(orders), account.name)
        await self._save_timestamp(account.name, "orders", now_str)

    async def _scrape_products(self, account: ShoperAccountConfig, now_str: str) -> None:
        last = self._get_last_timestamp(account.name, "products")
        filters: dict[str, dict[str, Any]] = {}
        if last:
            filters["add_date"] = {">=": last, "<": now_str}

        products = await self._client.get_paged(
            "products", account.name, account.shop_url, account.login, account.password,
            filters=filters,
            order=["add_date"],
        )
        if not products:
            await self._save_timestamp(account.name, "products", now_str)
            return

        for product_data in products:
            product = map_shoper_product_to_product(product_data, account.language_id)
            if self._kafka:
                await self._kafka.send(
                    settings.kafka_topic_products_out,
                    product.model_dump(mode="json"),
                    key=product.external_id,
                )

        logger.info("Scraped %d products for account=%s", len(products), account.name)
        await self._save_timestamp(account.name, "products", now_str)

    async def _scrape_users(self, account: ShoperAccountConfig, now_str: str) -> None:
        last = self._get_last_timestamp(account.name, "users")
        filters: dict[str, dict[str, Any]] = {"active": {"=": "1"}}
        if last:
            filters["date_add"] = {">=": last, "<": now_str}

        users = await self._client.get_paged(
            "users", account.name, account.shop_url, account.login, account.password,
            filters=filters,
            order=["date_add"],
        )
        if not users:
            await self._save_timestamp(account.name, "users", now_str)
            return

        for user_data in users:
            if self._kafka:
                await self._kafka.send(
                    settings.kafka_topic_users_out,
                    user_data,
                    key=str(user_data.get("user_id", "")),
                )

        logger.info("Scraped %d users for account=%s", len(users), account.name)
        await self._save_timestamp(account.name, "users", now_str)

    def _get_last_timestamp(self, account_name: str, entity: str) -> str | None:
        return self._last_timestamps.get(account_name, {}).get(entity)

    async def _save_timestamp(self, account_name: str, entity: str, timestamp: str) -> None:
        self._last_timestamps.setdefault(account_name, {})[entity] = timestamp
        await self._state.save_timestamp(account_name, entity, timestamp)

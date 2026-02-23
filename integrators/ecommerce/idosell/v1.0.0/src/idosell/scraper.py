"""Background scraper — polls IdoSell for new and updated orders."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from src.config import IdoSellAccountConfig, settings
from src.idosell.client import IdoSellClient
from src.idosell.mapper import map_idosell_order_to_order, map_idosell_product_to_product
from src.idosell.schemas import IdoSellOrder, IdoSellProduct
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


class OrderScraper:
    """Periodically fetches new data from all configured IdoSell accounts."""

    def __init__(
        self,
        client: IdoSellClient,
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
            "IdoSell scraper started, interval=%ds, accounts=%d",
            settings.scraping_interval_seconds,
            len(self._accounts.list_accounts()),
        )
        while self._running:
            await self._scrape_all_accounts()
            await asyncio.sleep(settings.scraping_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        logger.info("IdoSell scraper stopped")

    async def _scrape_all_accounts(self) -> None:
        for account in self._accounts.list_accounts():
            try:
                await self._scrape_account(account)
            except Exception:
                logger.exception("Error scraping account=%s", account.name)

    async def _scrape_account(self, account: IdoSellAccountConfig) -> None:
        now = datetime.now(timezone.utc)
        now_str = now.strftime(settings.idosell_date_format)

        if settings.scrape_orders:
            await self._scrape_orders(account, now_str)
        if settings.scrape_products:
            await self._scrape_products(account, now_str)

    async def _scrape_orders(self, account: IdoSellAccountConfig, now_str: str) -> None:
        last = self._get_last_timestamp(account.name, "orders")

        total_scraped = 0
        page = 0
        while True:
            data = await self._client.search_orders(
                account,
                date_begin=last,
                date_end=now_str,
                date_type="modified",
                page=page,
                limit=settings.results_limit,
            )

            results = data.get("results", [])
            if not results:
                break

            for order_data in results:
                ido_order = IdoSellOrder.model_validate(order_data)
                order = map_idosell_order_to_order(ido_order, account.name)

                if self._kafka:
                    await self._kafka.send(
                        settings.kafka_topic_orders_out,
                        order.model_dump(mode="json"),
                        key=order.external_id,
                    )

            total_scraped += len(results)
            total_pages = data.get("resultsNumberPage", 1)
            if page + 1 >= total_pages:
                break
            page += 1

        if total_scraped:
            logger.info("Scraped %d orders for account=%s", total_scraped, account.name)
        await self._save_timestamp(account.name, "orders", now_str)

    async def _scrape_products(self, account: IdoSellAccountConfig, now_str: str) -> None:
        last = self._get_last_timestamp(account.name, "products")

        total_scraped = 0
        page = 0
        while True:
            data = await self._client.search_products(
                account,
                modified_after=last,
                page=page,
                limit=settings.results_limit,
            )

            results = data.get("results", [])
            if not results:
                break

            for product_data in results:
                ido_product = IdoSellProduct.model_validate(product_data)
                product = map_idosell_product_to_product(ido_product)

                if self._kafka:
                    await self._kafka.send(
                        settings.kafka_topic_products_out,
                        product.model_dump(mode="json"),
                        key=product.external_id,
                    )

            total_scraped += len(results)
            total_pages = data.get("resultsNumberPage", 1)
            if page + 1 >= total_pages:
                break
            page += 1

        if total_scraped:
            logger.info("Scraped %d products for account=%s", total_scraped, account.name)
        await self._save_timestamp(account.name, "products", now_str)

    def _get_last_timestamp(self, account_name: str, entity: str) -> str | None:
        return self._last_timestamps.get(account_name, {}).get(entity)

    async def _save_timestamp(self, account_name: str, entity: str, timestamp: str) -> None:
        self._last_timestamps.setdefault(account_name, {})[entity] = timestamp
        await self._state.save_timestamp(account_name, entity, timestamp)

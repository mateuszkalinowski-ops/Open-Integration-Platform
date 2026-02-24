"""Background scraper — polls Apilo REST API for new/updated orders."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from src.config import ApiloAccountConfig, settings
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.apilo.client import ApiloClient
from src.apilo.mapper import map_apilo_order_to_order
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


class ApiloScraper:
    """Periodically fetches new/updated orders from all configured Apilo accounts."""

    def __init__(
        self,
        client: ApiloClient,
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
            "Apilo scraper started, interval=%ds, accounts=%d",
            settings.scraping_interval_seconds,
            len(self._accounts.list_accounts()),
        )
        while self._running:
            await self._scrape_all_accounts()
            await asyncio.sleep(settings.scraping_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        logger.info("Apilo scraper stopped")

    async def _scrape_all_accounts(self) -> None:
        for account in self._accounts.list_accounts():
            try:
                await self._scrape_account(account)
            except Exception:
                logger.exception("Error scraping account=%s", account.name)

    async def _scrape_account(self, account: ApiloAccountConfig) -> None:
        if settings.scrape_orders:
            await self._scrape_orders(account)

    async def _scrape_orders(self, account: ApiloAccountConfig) -> None:
        last_updated = self._get_last_timestamp(account.name, "orders_last_updated")
        if not last_updated:
            default_lookback = datetime.now(timezone.utc) - timedelta(hours=24)
            last_updated = default_lookback.strftime("%Y-%m-%dT%H:%M:%S+0000")

        try:
            resp = await self._client.get_orders(
                account, updated_after=last_updated, sort="updatedAtAsc", limit=200,
            )
        except Exception as exc:
            logger.warning("getOrders failed for account=%s: %s", account.name, exc)
            return

        apilo_orders = resp.get("orders", [])
        if not apilo_orders:
            return

        published = 0
        latest_update = last_updated

        for order_data in apilo_orders:
            order = map_apilo_order_to_order(order_data, account.name)

            if self._kafka:
                await self._kafka.send(
                    settings.kafka_topic_orders_out,
                    order.model_dump(mode="json"),
                    key=order.external_id,
                )
            published += 1

            order_update_time = order_data.get("updatedAt", "")
            if order_update_time > latest_update:
                latest_update = order_update_time

        if published:
            logger.info("Scraped %d orders for account=%s", published, account.name)

        await self._save_timestamp(account.name, "orders_last_updated", latest_update)

    def _get_last_timestamp(self, account_name: str, entity: str) -> str | None:
        return self._last_timestamps.get(account_name, {}).get(entity)

    async def _save_timestamp(self, account_name: str, entity: str, timestamp: str) -> None:
        self._last_timestamps.setdefault(account_name, {})[entity] = timestamp
        await self._state.save_timestamp(account_name, entity, timestamp)

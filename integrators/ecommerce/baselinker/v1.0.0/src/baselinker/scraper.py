"""Background scraper — polls BaseLinker for new orders via getJournalList."""

import asyncio
import logging
from typing import Any

from src.config import BaseLinkerAccountConfig, settings
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.baselinker.client import BaseLinkerClient
from src.baselinker.mapper import map_bl_order_to_order, map_bl_product_to_product
from pinquark_common.kafka import KafkaMessageProducer, wrap_event

logger = logging.getLogger(__name__)


class BaseLinkerScraper:
    """Periodically fetches new data from all configured BaseLinker accounts."""

    def __init__(
        self,
        client: BaseLinkerClient,
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
        self._status_cache: dict[str, dict[int, str]] = {}

    async def start(self) -> None:
        self._running = True
        self._last_timestamps = await self._state.load_all_timestamps()
        logger.info(
            "BaseLinker scraper started, interval=%ds, accounts=%d",
            settings.scraping_interval_seconds,
            len(self._accounts.list_accounts()),
        )
        while self._running:
            await self._scrape_all_accounts()
            await asyncio.sleep(settings.scraping_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        logger.info("BaseLinker scraper stopped")

    async def _get_status_defs(self, account: BaseLinkerAccountConfig) -> dict[int, str]:
        if account.name not in self._status_cache:
            resp = await self._client.get_order_status_list(account)
            statuses = resp.get("statuses", [])
            self._status_cache[account.name] = {s["id"]: s["name"] for s in statuses}
        return self._status_cache[account.name]

    async def _scrape_all_accounts(self) -> None:
        for account in self._accounts.list_accounts():
            try:
                await self._scrape_account(account)
            except Exception:
                logger.exception("Error scraping account=%s", account.name)

    async def _scrape_account(self, account: BaseLinkerAccountConfig) -> None:
        if settings.scrape_orders:
            await self._scrape_orders(account)

    async def _scrape_orders(self, account: BaseLinkerAccountConfig) -> None:
        """Use getJournalList to detect new/changed orders, then fetch them."""
        last_log_id_str = self._get_last_timestamp(account.name, "journal_log_id")
        last_log_id = int(last_log_id_str) if last_log_id_str else 0

        try:
            journal = await self._client.get_journal_list(account, last_log_id=last_log_id)
        except Exception as exc:
            logger.warning("getJournalList failed for account=%s: %s", account.name, exc)
            return

        logs = journal.get("logs", [])
        if not logs:
            return

        order_ids: set[int] = set()
        max_log_id = last_log_id
        for log_entry in logs:
            log_id = log_entry.get("log_id", 0)
            object_id = log_entry.get("object_id", log_entry.get("order_id", 0))
            if object_id:
                order_ids.add(object_id)
            if log_id > max_log_id:
                max_log_id = log_id

        if not order_ids:
            await self._save_timestamp(account.name, "journal_log_id", str(max_log_id))
            return

        status_defs = await self._get_status_defs(account)

        resp = await self._client.get_orders(account, date_from=0)
        all_orders = resp.get("orders", [])

        published = 0
        for od in all_orders:
            if od.get("order_id") in order_ids:
                order = map_bl_order_to_order(od, account.name, status_defs)
                if self._kafka:
                    envelope = wrap_event(
                        connector_name="baselinker",
                        event="order.created",
                        data=order.model_dump(mode="json"),
                        account_name=account.name,
                    )
                    await self._kafka.send(
                        settings.kafka_topic_orders_out,
                        envelope,
                        key=order.external_id,
                    )
                published += 1

        if published:
            logger.info("Scraped %d orders for account=%s", published, account.name)

        await self._save_timestamp(account.name, "journal_log_id", str(max_log_id))

    def _get_last_timestamp(self, account_name: str, entity: str) -> str | None:
        return self._last_timestamps.get(account_name, {}).get(entity)

    async def _save_timestamp(self, account_name: str, entity: str, timestamp: str) -> None:
        self._last_timestamps.setdefault(account_name, {})[entity] = timestamp
        await self._state.save_timestamp(account_name, entity, timestamp)

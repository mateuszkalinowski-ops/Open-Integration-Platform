"""Background order scraper — polls WooCommerce for new/modified orders on a configurable interval."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from pinquark_common.kafka import KafkaMessageProducer

from src.config import WooCommerceAccountConfig, settings
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.woocommerce.client import WooCommerceClient
from src.woocommerce.mapper import map_woo_order_to_order
from src.woocommerce.schemas import WooOrder

logger = logging.getLogger(__name__)


class OrderScraper:
    """Periodically fetches new/modified orders from all configured WooCommerce stores."""

    def __init__(
        self,
        client: WooCommerceClient,
        account_manager: AccountManager,
        state_store: StateStore,
        kafka_producer: KafkaMessageProducer | None = None,
    ):
        self._client = client
        self._accounts = account_manager
        self._state_store = state_store
        self._kafka = kafka_producer
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info(
            "Order scraper started, interval=%ds, accounts=%d",
            settings.scraping_interval_seconds,
            len(self._accounts.list_accounts()),
        )
        while self._running:
            await self._scrape_all_accounts()
            await asyncio.sleep(settings.scraping_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        logger.info("Order scraper stopped")

    async def _scrape_all_accounts(self) -> None:
        for account in self._accounts.list_accounts():
            try:
                await self._scrape_account(account)
            except Exception:
                logger.exception("Error scraping orders for account=%s", account.name)

    async def _scrape_account(self, account: WooCommerceAccountConfig) -> None:
        last_modified = await self._state_store.get_last_scraped(account.name, "orders")
        modified_after = last_modified or (datetime.now(UTC) - timedelta(hours=24)).isoformat()

        raw_orders = await self._client.list_orders(
            account_name=account.name,
            per_page=settings.default_per_page,
            modified_after=modified_after,
        )

        if not raw_orders:
            return

        newest_modified: datetime | None = None

        for raw in raw_orders:
            woo_order = WooOrder.model_validate(raw)
            order = map_woo_order_to_order(woo_order, account.name)

            if woo_order.date_modified and (newest_modified is None or woo_order.date_modified > newest_modified):
                newest_modified = woo_order.date_modified

            if self._kafka:
                await self._kafka.send(
                    settings.kafka_topic_orders_out,
                    order.model_dump(mode="json"),
                    key=order.external_id,
                )
            else:
                logger.info(
                    "Order scraped (no Kafka): id=%s account=%s status=%s",
                    order.external_id,
                    account.name,
                    order.status,
                )

        if newest_modified:
            await self._state_store.save_last_scraped(
                account.name,
                "orders",
                newest_modified.isoformat(),
            )

        logger.info(
            "Scraped orders account=%s: %d orders fetched",
            account.name,
            len(raw_orders),
        )

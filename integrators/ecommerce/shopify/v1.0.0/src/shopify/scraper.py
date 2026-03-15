"""Background order scraper — polls Shopify orders API on a configurable interval.

Uses a two-pass strategy:
1. Fetch new orders via since_id (orders created after the last known order)
2. Fetch recently updated orders via updated_at_min (orders modified since last scrape)

This ensures both new orders and status changes on existing orders are captured.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from pinquark_common.kafka import KafkaMessageProducer, wrap_event

from src.config import ShopifyAccountConfig, settings
from src.models.database import TokenStore
from src.services.account_manager import AccountManager
from src.shopify.client import ShopifyClient
from src.shopify.mapper import map_shopify_order_to_order
from src.shopify.schemas import ShopifyOrder, ShopifyOrdersResponse

logger = logging.getLogger(__name__)


class OrderScraper:
    """Periodically fetches new and updated orders from all configured Shopify stores.

    Pass 1 (since_id): catches newly created orders.
    Pass 2 (updated_at_min): catches status changes on existing orders.
    """

    def __init__(
        self,
        client: ShopifyClient,
        account_manager: AccountManager,
        token_store: TokenStore,
        kafka_producer: KafkaMessageProducer | None = None,
    ):
        self._client = client
        self._accounts = account_manager
        self._token_store = token_store
        self._kafka = kafka_producer
        self._running = False
        self._last_order_ids: dict[str, str] = {}
        self._last_scrape_times: dict[str, datetime] = {}

    async def start(self) -> None:
        self._running = True
        self._last_order_ids = await self._token_store.load_all_last_order_ids()
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
                logger.exception("Error scraping account=%s", account.name)

    async def _scrape_account(self, account: ShopifyAccountConfig) -> None:
        seen_ids: set[str] = set()
        total_published = 0

        since_id = self._last_order_ids.get(account.name)
        if since_id:
            new_count = await self._fetch_new_orders(account, since_id, seen_ids)
            total_published += new_count

        last_scrape = self._last_scrape_times.get(account.name)
        if last_scrape:
            buffer = timedelta(seconds=settings.scraping_interval_seconds, minutes=1)
            updated_since = last_scrape - buffer
            updated_count = await self._fetch_updated_orders(account, updated_since, seen_ids)
            total_published += updated_count

        if not since_id and not last_scrape:
            new_count = await self._fetch_new_orders(account, None, seen_ids)
            total_published += new_count

        self._last_scrape_times[account.name] = datetime.now(UTC)

        if total_published > 0:
            logger.info("Scraped account=%s: %d orders published", account.name, total_published)

    async def _fetch_new_orders(
        self,
        account: ShopifyAccountConfig,
        since_id: str | None,
        seen_ids: set[str],
    ) -> int:
        raw = await self._client.get_orders(
            account,
            status="any",
            limit=250,
            since_id=since_id,
        )

        response = ShopifyOrdersResponse.model_validate(raw)
        if not response.orders:
            return 0

        count = 0
        for shopify_order in response.orders:
            order_id = str(shopify_order.id)
            if order_id not in seen_ids:
                seen_ids.add(order_id)
                await self._process_order(shopify_order, account)
                count += 1

        last_order = response.orders[-1]
        last_id = str(last_order.id)
        self._last_order_ids[account.name] = last_id
        await self._token_store.save_last_order_id(account.name, last_id)

        return count

    async def _fetch_updated_orders(
        self,
        account: ShopifyAccountConfig,
        updated_since: datetime,
        seen_ids: set[str],
    ) -> int:
        raw = await self._client.get_orders(
            account,
            status="any",
            limit=250,
            updated_at_min=updated_since.isoformat(),
        )

        response = ShopifyOrdersResponse.model_validate(raw)
        if not response.orders:
            return 0

        count = 0
        for shopify_order in response.orders:
            order_id = str(shopify_order.id)
            if order_id not in seen_ids:
                seen_ids.add(order_id)
                await self._process_order(shopify_order, account)
                count += 1

        return count

    async def _process_order(
        self,
        shopify_order: ShopifyOrder,
        account: ShopifyAccountConfig,
    ) -> None:
        order = map_shopify_order_to_order(shopify_order, account.name)

        if self._kafka:
            envelope = wrap_event(
                connector_name="shopify",
                event="order.created",
                data=order.model_dump(mode="json"),
                account_name=account.name,
            )
            await self._kafka.send(
                settings.kafka_topic_orders_out,
                envelope,
                key=order.external_id,
            )
            logger.info(
                "Published order=%s to Kafka for account=%s",
                order.external_id,
                account.name,
            )
        else:
            logger.info(
                "Order scraped (no Kafka): id=%s account=%s status=%s",
                order.external_id,
                account.name,
                order.status,
            )

"""Background order scraper — polls Allegro order events on a configurable interval."""

import asyncio
import logging
from typing import Any

from src.allegro.client import AllegroClient
from src.allegro.mapper import map_checkout_to_order, extract_ean_from_parameters
from src.allegro.schemas import (
    AllegroCheckoutForm,
    AllegroOrderEvent,
    AllegroOrderEventsResponse,
    OrderEventType,
    PROCESSABLE_EVENT_TYPES,
)
from src.config import AllegroAccountConfig, settings
from src.models.database import TokenStore
from src.services.account_manager import AccountManager
from pinquark_common.kafka import KafkaMessageProducer, wrap_event

logger = logging.getLogger(__name__)

ALLEGRO_EVENT_TYPE_MAP: dict[OrderEventType, str] = {
    OrderEventType.READY_FOR_PROCESSING: "order.ready_for_processing",
    OrderEventType.BUYER_CANCELLED: "order.buyer_cancelled",
    OrderEventType.AUTO_CANCELLED: "order.auto_cancelled",
    OrderEventType.BUYER_MODIFIED: "order.buyer_modified",
    OrderEventType.BOUGHT: "order.bought",
    OrderEventType.FILLED_IN: "order.filled_in",
    OrderEventType.FULFILLMENT_STATUS_CHANGED: "order.status_changed",
}


class OrderScraper:
    """Periodically fetches new order events from all configured Allegro accounts."""

    def __init__(
        self,
        client: AllegroClient,
        account_manager: AccountManager,
        token_store: TokenStore,
        kafka_producer: KafkaMessageProducer | None = None,
    ):
        self._client = client
        self._accounts = account_manager
        self._token_store = token_store
        self._kafka = kafka_producer
        self._running = False
        self._last_event_ids: dict[str, str] = {}

    async def start(self) -> None:
        self._running = True
        self._last_event_ids = await self._token_store.load_all_last_event_ids()
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

    async def _scrape_account(self, account: AllegroAccountConfig) -> None:
        from_event_id = self._last_event_ids.get(account.name)

        raw = await self._client.get_order_events(
            account_name=account.name,
            client_id=account.client_id,
            client_secret=account.client_secret,
            api_url=account.api_url,
            auth_url=account.auth_url,
            from_event_id=from_event_id,
        )

        events_response = AllegroOrderEventsResponse.model_validate(raw)
        if not events_response.events:
            return

        processable = [e for e in events_response.events if e.type in PROCESSABLE_EVENT_TYPES]
        deduplicated = self._deduplicate_events(processable)

        for event in deduplicated:
            await self._process_event(event, account)

        last = events_response.events[-1]
        self._last_event_ids[account.name] = last.id
        await self._token_store.save_last_event_id(account.name, last.id)

        logger.info(
            "Scraped account=%s: %d events, %d processable, %d deduplicated",
            account.name,
            len(events_response.events),
            len(processable),
            len(deduplicated),
        )

    def _deduplicate_events(self, events: list[AllegroOrderEvent]) -> list[AllegroOrderEvent]:
        """Keep only the most recent event per checkout form."""
        seen: dict[str, AllegroOrderEvent] = {}
        for event in events:
            checkout_id = self._extract_checkout_id(event)
            if checkout_id:
                seen[checkout_id] = event
        return list(seen.values())

    @staticmethod
    def _extract_checkout_id(event: AllegroOrderEvent) -> str | None:
        if event.order and event.order.checkout_form:
            return event.order.checkout_form.id
        return None

    async def _process_event(self, event: AllegroOrderEvent, account: AllegroAccountConfig) -> None:
        if not event.order or not event.order.checkout_form:
            logger.warning("Event %s has no checkout form, skipping", event.id)
            return

        checkout = event.order.checkout_form
        product_details = await self._fetch_product_details(checkout, account)
        order = map_checkout_to_order(checkout, account.name, product_details)

        event_name = ALLEGRO_EVENT_TYPE_MAP.get(event.type, f"order.{event.type.value.lower()}")

        if self._kafka:
            envelope = wrap_event(
                connector_name="allegro",
                event=event_name,
                data=order.model_dump(mode="json"),
                account_name=account.name,
            )
            await self._kafka.send(
                settings.kafka_topic_orders_out,
                envelope,
                key=order.external_id,
            )
            logger.info(
                "Published order=%s event=%s to Kafka for account=%s",
                order.external_id, event_name, account.name,
            )
        else:
            logger.info(
                "Order scraped (no Kafka): id=%s account=%s event=%s status=%s",
                order.external_id, account.name, event_name, order.status,
            )

    async def _fetch_product_details(
        self,
        checkout: AllegroCheckoutForm,
        account: AllegroAccountConfig,
    ) -> dict[str, dict[str, Any]]:
        """Fetch offer and product details to extract EAN, SKU, etc."""
        details: dict[str, dict[str, Any]] = {}
        for item in checkout.line_items:
            offer_id = item.offer.id
            try:
                offer_data = await self._client.get_offer(
                    offer_id, account.name, account.client_id, account.client_secret,
                    account.api_url, account.auth_url,
                )
                ean = extract_ean_from_parameters(offer_data.get("parameters", []))
                product_id = ""
                if offer_data.get("product") and offer_data["product"].get("id"):
                    product_id = offer_data["product"]["id"]
                    try:
                        product_data = await self._client.get_product(
                            product_id, account.name, account.client_id, account.client_secret,
                            account.api_url, account.auth_url,
                        )
                        if not ean:
                            ean = extract_ean_from_parameters(product_data.get("parameters", []))
                    except Exception:
                        logger.debug("Could not fetch product %s", product_id)

                details[offer_id] = {
                    "ean": ean,
                    "sku": offer_data.get("external", {}).get("id", offer_id) if offer_data.get("external") else offer_id,
                    "name": offer_data.get("name", ""),
                    "product_id": product_id,
                }
            except Exception:
                logger.debug("Could not fetch offer %s details", offer_id)
                details[offer_id] = {"ean": "", "sku": offer_id, "name": item.offer.name, "product_id": ""}
        return details

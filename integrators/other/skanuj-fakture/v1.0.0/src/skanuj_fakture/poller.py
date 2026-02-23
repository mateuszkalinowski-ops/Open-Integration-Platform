"""Background poller for new scanned documents in SkanujFakture."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from src.config import settings
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.skanuj_fakture.client import SkanujFaktureClient
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


class DocumentPoller:
    """Periodically polls SkanujFakture for newly scanned documents."""

    def __init__(
        self,
        account_manager: AccountManager,
        state_store: StateStore,
        kafka_producer: KafkaMessageProducer | None = None,
    ) -> None:
        self._account_manager = account_manager
        self._state_store = state_store
        self._kafka_producer = kafka_producer
        self._running = False
        self._clients: dict[str, SkanujFaktureClient] = {}

    def _get_client(self, account_name: str) -> SkanujFaktureClient | None:
        if account_name not in self._clients:
            account = self._account_manager.get_account(account_name)
            if account is None:
                return None
            self._clients[account_name] = SkanujFaktureClient(account)
        return self._clients[account_name]

    async def start(self) -> None:
        self._running = True
        logger.info("Document poller started (interval=%ds)", settings.polling_interval_seconds)
        while self._running:
            try:
                await self._poll_all_accounts()
            except Exception:
                logger.exception("Polling cycle failed")
            await asyncio.sleep(settings.polling_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

    async def _poll_all_accounts(self) -> None:
        for account in self._account_manager.list_accounts():
            try:
                await self._poll_account(account.name)
            except Exception:
                logger.exception("Polling failed for account %s", account.name)

    async def _poll_account(self, account_name: str) -> None:
        client = self._get_client(account_name)
        if client is None:
            return

        account = self._account_manager.get_account(account_name)
        if account is None or account.company_id is None:
            logger.debug("No company_id configured for account %s, trying to resolve", account_name)
            try:
                companies = await client.get_companies()
                if not companies:
                    return
                company_id = companies[0].get("company", {}).get("id")
                if company_id is None:
                    return
            except Exception:
                logger.exception("Failed to get companies for %s", account_name)
                return
        else:
            company_id = account.company_id

        statuses = [s.strip() for s in settings.polling_status_filter.split(",")]
        documents = await client.get_documents(company_id, document_statuses=statuses)

        known_ids = await self._state_store.load_known_document_ids(account_name)
        new_docs = [d for d in documents if d.get("id") not in known_ids]

        if not new_docs:
            return

        logger.info("Found %d new documents for account %s", len(new_docs), account_name)

        for doc in new_docs:
            doc_id = doc.get("id")
            if doc_id is None:
                continue
            await self._state_store.save_document_id(account_name, doc_id)

            if self._kafka_producer:
                await self._publish_document_event(account_name, doc)

    async def _publish_document_event(self, account_name: str, document: dict[str, Any]) -> None:
        if self._kafka_producer is None:
            return
        event = {
            "account_name": account_name,
            "document_id": document.get("id"),
            "number": document.get("number"),
            "date": document.get("date"),
            "netto": document.get("netto"),
            "brutto": document.get("brutto"),
            "contractor": document.get("contractor", {}).get("name") if document.get("contractor") else None,
            "status": document.get("documentStatus", {}).get("name") if document.get("documentStatus") else None,
            "invoice_type": document.get("invoiceType"),
            "polled_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._kafka_producer.send(
            settings.kafka_topic_documents_scanned,
            value=event,
            key=str(document.get("id", "")),
        )
        logger.debug("Published document event for doc %s", document.get("id"))

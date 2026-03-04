"""Background poller for new scanned documents in SkanujFakture."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from src.config import settings
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.skanuj_fakture.client import SkanujFaktureClient
from src.skanuj_fakture.schemas import Document
from pinquark_common.kafka import KafkaMessageProducer, wrap_event

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
        logger.info("Document poller started (interval=%ds), waiting 30s for account provisioning...", settings.polling_interval_seconds)
        await asyncio.sleep(30)
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
        accounts = self._account_manager.list_accounts()
        if not accounts:
            logger.warning("No accounts configured — skipping poll cycle. Provision accounts via POST /accounts.")
            return
        logger.info("Polling %d account(s): %s", len(accounts), [a.name for a in accounts])
        for account in accounts:
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
            success = await self._publish_document_event(account_name, doc)
            if success:
                await self._state_store.save_document_id(account_name, doc_id)

    def _normalize_document(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse raw API response through Pydantic model to normalize keys to snake_case."""
        try:
            doc = Document(**raw)
            normalized = doc.model_dump(by_alias=False, exclude_none=False)
            normalized["document_id"] = normalized.pop("id", None)
            return normalized
        except Exception:
            logger.warning("Failed to normalize document via Pydantic, using raw data")
            result: dict[str, Any] = {"document_id": raw.get("id")}
            result.update(raw)
            return result

    async def _publish_document_event(self, account_name: str, document: dict[str, Any]) -> bool:
        event = self._normalize_document(document)
        event["account_name"] = account_name
        event["polled_at"] = datetime.now(timezone.utc).isoformat()

        if self._kafka_producer:
            envelope = wrap_event(
                connector_name="skanuj-fakture",
                event="document.scanned",
                data=event,
                account_name=account_name,
            )
            await self._kafka_producer.send(
                settings.kafka_topic_documents_scanned,
                value=envelope,
                key=str(event.get("document_id", "")),
            )

        if settings.platform_event_notify:
            ok = await self._notify_platform(event)
            if not ok:
                return False

        logger.debug("Published document event for doc %s", event.get("document_id"))
        return True

    async def _notify_platform(self, event: dict[str, Any]) -> bool:
        url = f"{settings.platform_api_url}/internal/events"
        payload = {
            "connector_name": "skanuj-fakture",
            "event": "document.scanned",
            "data": event,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code >= 400:
                    logger.error(
                        "Platform event notify FAILED: status=%s body=%s doc_id=%s",
                        resp.status_code, resp.text[:500], event.get("document_id"),
                    )
                    return False
                logger.info(
                    "Platform event notify OK: status=%s doc_id=%s workflows=%s",
                    resp.status_code, event.get("document_id"), resp.text[:200],
                )
                return True
        except Exception:
            logger.exception("Platform event notify unreachable at %s", url)
            return False

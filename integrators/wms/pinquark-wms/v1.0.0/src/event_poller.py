"""Background poller that detects new/changed data in Pinquark WMS.

Periodically calls GET endpoints for documents, articles, contractors,
positions, and feedbacks. Compares with previously seen state and emits
events to the platform via POST /internal/events.

State is stored in-memory keyed by (entity, unique_key). On restart
the first cycle snapshots current data without emitting events.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from src.client import PinquarkWmsClient
from src.config import settings
from src.schemas import WmsCredentials

logger = logging.getLogger("pinquark-wms-poller")


def _entity_key(entity: dict[str, Any], entity_type: str) -> str:
    """Build a unique key for a given entity."""
    if entity_type == "document":
        return f"{entity.get('source', 'ERP')}:{entity.get('erpId', entity.get('wmsId', ''))}"
    if entity_type == "article":
        return f"{entity.get('source', 'ERP')}:{entity.get('erpId', entity.get('wmsId', ''))}"
    if entity_type == "contractor":
        return f"{entity.get('source', 'ERP')}:{entity.get('erpId', entity.get('wmsId', ''))}"
    if entity_type == "position":
        doc_id = entity.get("documentId", "")
        doc_src = entity.get("documentSource", "")
        return f"{doc_src}:{doc_id}"
    if entity_type == "feedback":
        return str(entity.get("id", ""))
    return json.dumps(entity, sort_keys=True, default=str)


def _content_hash(entity: dict[str, Any]) -> str:
    """Deterministic hash of entity content for change detection."""
    raw = json.dumps(entity, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


class EventPoller:
    """Polls Pinquark WMS API for changes and emits events to the platform."""

    def __init__(self, wms_client: PinquarkWmsClient) -> None:
        self._wms_client = wms_client
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._http_client: httpx.AsyncClient | None = None

        self._state: dict[str, dict[str, str]] = {}
        self._initialized: set[str] = set()

        self._credential_store: dict[str, WmsCredentials] = {}

    def register_credentials(self, account_name: str, creds: WmsCredentials) -> None:
        self._credential_store[account_name] = creds
        logger.info("Registered polling credentials for account=%s", account_name)

    async def start(self) -> None:
        if not settings.event_polling_enabled:
            logger.info("Event polling disabled")
            return
        self._running = True
        self._http_client = httpx.AsyncClient(timeout=15.0)
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "Event poller started (interval=%ds, platform=%s)",
            settings.event_polling_interval_seconds,
            settings.platform_api_url,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._http_client:
            await self._http_client.aclose()
        logger.info("Event poller stopped")

    async def _loop(self) -> None:
        await asyncio.sleep(settings.event_polling_initial_delay)
        while self._running:
            await self._poll_cycle()
            await asyncio.sleep(settings.event_polling_interval_seconds)

    def reset_state(self) -> None:
        """Clear in-memory state so next poll treats everything as new."""
        self._state.clear()
        self._initialized.clear()
        logger.info("Poller state reset — next cycle will emit events for all entities")

    async def _poll_cycle(self) -> None:
        if not self._credential_store:
            logger.info("No credentials registered, skipping poll cycle")
            return

        logger.info(
            "Poll cycle starting for %d account(s): %s",
            len(self._credential_store),
            ", ".join(self._credential_store.keys()),
        )
        for account_name, creds in list(self._credential_store.items()):
            try:
                await self._poll_account(account_name, creds)
            except Exception:
                logger.exception("Poll cycle failed for account=%s", account_name)

    async def _poll_account(self, account_name: str, creds: WmsCredentials) -> None:
        await self._poll_entity(account_name, creds, "document", "document.synced")
        await self._poll_entity(account_name, creds, "article", "article.synced")
        await self._poll_entity(account_name, creds, "contractor", "contractor.synced")
        await self._poll_positions(account_name, creds)
        await self._poll_feedbacks(account_name, creds)

    async def _poll_entity(
        self,
        account_name: str,
        creds: WmsCredentials,
        entity_type: str,
        event_name: str,
    ) -> None:
        fetch_map = {
            "document": self._wms_client.get_documents,
            "article": self._wms_client.get_articles,
            "contractor": self._wms_client.get_contractors,
        }
        fetch_fn = fetch_map.get(entity_type)
        if not fetch_fn:
            return

        try:
            data, status = await fetch_fn(creds)
        except Exception:
            logger.warning("Failed to fetch %ss for account=%s", entity_type, account_name, exc_info=True)
            return

        if status >= 400:
            logger.warning("Fetch %ss returned HTTP %d for account=%s", entity_type, status, account_name)
            return
        if not isinstance(data, list):
            logger.warning("Fetch %ss returned non-list (%s) for account=%s", entity_type, type(data).__name__, account_name)
            return

        state_key = f"{account_name}:{entity_type}"
        current_state = self._state.get(state_key, {})
        new_state: dict[str, str] = {}
        is_first_run = state_key not in self._initialized

        events_emitted = 0
        for item in data:
            key = _entity_key(item, entity_type)
            content = _content_hash(item)
            new_state[key] = content

            if is_first_run:
                continue

            prev = current_state.get(key)
            if prev is None or prev != content:
                item["account_name"] = account_name
                item["_change_type"] = "new" if prev is None else "updated"
                await self._emit_event(event_name, item)
                events_emitted += 1

        self._state[state_key] = new_state
        self._initialized.add(state_key)

        if is_first_run:
            logger.info(
                "Baseline snapshot: %d %s(s) for account=%s (events start from next cycle)",
                len(data), entity_type, account_name,
            )
        elif events_emitted > 0:
            logger.info(
                "Emitted %d %s events for account=%s",
                events_emitted, event_name, account_name,
            )
        else:
            logger.info("No changes in %s for account=%s (%d items)", entity_type, account_name, len(data))

    async def _poll_positions(self, account_name: str, creds: WmsCredentials) -> None:
        try:
            data, status = await self._wms_client.get_positions(creds)
        except Exception:
            logger.debug("Failed to fetch positions for account=%s", account_name)
            return

        if status >= 400 or not isinstance(data, list):
            return

        state_key = f"{account_name}:position"
        current_state = self._state.get(state_key, {})
        new_state: dict[str, str] = {}
        is_first_run = state_key not in self._initialized

        events_emitted = 0
        for wrapper in data:
            key = _entity_key(wrapper, "position")
            content = _content_hash(wrapper)
            new_state[key] = content

            if is_first_run:
                continue

            prev = current_state.get(key)
            if prev is None or prev != content:
                wrapper["account_name"] = account_name
                wrapper["_change_type"] = "new" if prev is None else "updated"
                await self._emit_event("position.synced", wrapper)
                events_emitted += 1

        self._state[state_key] = new_state
        self._initialized.add(state_key)

        if events_emitted > 0:
            logger.info(
                "Emitted %d position.synced events for account=%s",
                events_emitted, account_name,
            )

    async def _poll_feedbacks(self, account_name: str, creds: WmsCredentials) -> None:
        try:
            data, status = await self._wms_client.get_feedbacks(creds)
        except Exception:
            logger.debug("Failed to fetch feedbacks for account=%s", account_name)
            return

        if status >= 400 or not isinstance(data, list):
            return

        state_key = f"{account_name}:feedback"
        known_ids = self._state.get(state_key, {})
        new_ids: dict[str, str] = {}
        is_first_run = state_key not in self._initialized

        events_emitted = 0
        for fb in data:
            fb_id = str(fb.get("id", ""))
            new_ids[fb_id] = "1"

            if is_first_run:
                continue

            if fb_id not in known_ids:
                fb["account_name"] = account_name
                await self._emit_event("feedback.received", fb)
                events_emitted += 1

        self._state[state_key] = new_ids
        self._initialized.add(state_key)

        if events_emitted > 0:
            logger.info(
                "Emitted %d feedback.received events for account=%s",
                events_emitted, account_name,
            )

    async def _emit_event(self, event_name: str, data: dict[str, Any]) -> None:
        if not settings.platform_api_url or not self._http_client:
            logger.warning("Platform URL not configured, event %s not sent", event_name)
            return

        payload = {
            "connector_name": "pinquark-wms",
            "event": event_name,
            "data": data,
        }

        try:
            resp = await self._http_client.post(
                f"{settings.platform_api_url}/internal/events",
                json=payload,
            )
            if resp.status_code < 300:
                resp_body = resp.json()
                logger.info(
                    "Event %s -> platform: flows=%s workflows=%s",
                    event_name,
                    resp_body.get("flows_triggered", "?"),
                    resp_body.get("workflows_triggered", "?"),
                )
            else:
                logger.error(
                    "Platform rejected event %s: HTTP %d %s",
                    event_name, resp.status_code, resp.text[:300],
                )
        except Exception:
            logger.error("Failed to send event %s to platform", event_name, exc_info=True)

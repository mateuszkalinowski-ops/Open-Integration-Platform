"""Background poller — periodically checks for new emails via IMAP."""

import asyncio
import contextlib
import hashlib
import logging
from datetime import UTC, datetime

import httpx
from pinquark_common.kafka import KafkaMessageProducer, wrap_event

from src.config import EmailAccountConfig, settings
from src.email_client.imap_client import ImapClient
from src.models.database import StateStore
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class EmailPoller:
    """Periodically fetches new emails from all configured accounts."""

    def __init__(
        self,
        account_manager: AccountManager,
        state_store: StateStore,
        kafka_producer: KafkaMessageProducer | None = None,
    ):
        self._accounts = account_manager
        self._state = state_store
        self._kafka = kafka_producer
        self._running = False
        self._last_timestamps: dict[str, dict[str, str]] = {}
        self._imap_clients: dict[str, ImapClient] = {}
        self._http_client: httpx.AsyncClient | None = None
        self._seen_cache: dict[str, set[str]] = {}
        self._seen_cache_limit = 1000

    def _get_imap_client(self, account: EmailAccountConfig) -> ImapClient:
        if account.name not in self._imap_clients:
            self._imap_clients[account.name] = ImapClient(
                host=account.imap_host,
                port=account.imap_port,
                login=account.login,
                password=account.password,
                use_ssl=account.use_ssl,
            )
        return self._imap_clients[account.name]

    @staticmethod
    def _derive_message_key(email_msg: object) -> str:
        """Derive a stable dedup key for an email; falls back to a hash when Message-ID is absent."""
        mid = getattr(email_msg, "message_id", None)
        if mid:
            return mid
        parts = "|".join(
            [
                getattr(email_msg, "subject", "") or "",
                getattr(email_msg, "sender", "") or "",
                getattr(email_msg, "date", "") or "",
            ]
        )
        return "sha256:" + hashlib.sha256(parts.encode()).hexdigest()

    async def start(self) -> None:
        self._running = True
        self._last_timestamps = await self._state.load_all_timestamps()
        for account in self._accounts.list_accounts():
            self._seen_cache[account.name] = await self._state.load_seen_ids(account.name, self._seen_cache_limit)
        if settings.platform_event_notify:
            self._http_client = httpx.AsyncClient(timeout=15.0)
        logger.info(
            "Email poller started, interval=%ds, accounts=%d, platform_notify=%s",
            settings.polling_interval_seconds,
            len(self._accounts.list_accounts()),
            bool(self._http_client),
        )
        while self._running:
            await self._poll_all_accounts()
            await asyncio.sleep(settings.polling_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        for imap in self._imap_clients.values():
            await imap.disconnect()
        self._imap_clients.clear()
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("Email poller stopped")

    async def _poll_all_accounts(self) -> None:
        for account in self._accounts.list_accounts():
            try:
                await self._poll_account(account)
            except Exception:
                logger.exception("Error polling account=%s, resetting IMAP connection", account.name)
                await self.reset_imap_client(account.name)

    async def reset_imap_client(self, account_name: str) -> None:
        """Disconnect and remove cached IMAP client so next poll reconnects."""
        client = self._imap_clients.pop(account_name, None)
        if client:
            with contextlib.suppress(Exception):
                await client.disconnect()

    async def _poll_account(self, account: EmailAccountConfig) -> None:
        imap = self._get_imap_client(account)
        now = datetime.now(UTC)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        last = self._get_last_timestamp(account.name, "emails")
        since: datetime | None = None
        if last:
            since = datetime.strptime(last, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)

        folder = account.polling_folder or settings.polling_folder
        page = await imap.fetch_emails(
            folder=folder,
            account_name=account.name,
            since=since,
            max_count=settings.polling_max_emails,
            unseen_only=True,
        )

        if not page.emails:
            await self._save_timestamp(account.name, "emails", now_str)
            return

        seen = self._seen_cache.setdefault(account.name, set())
        new_emails = [m for m in page.emails if self._derive_message_key(m) not in seen]
        if not new_emails:
            await self._save_timestamp(account.name, "emails", now_str)
            return

        cred_name = account.name.split(":", 1)[1] if ":" in account.name else account.name

        all_notified = True
        for email_msg in new_emails:
            msg_key = self._derive_message_key(email_msg)
            email_data = email_msg.model_dump(mode="json")
            email_data["account_name"] = cred_name
            if account.tenant_id:
                email_data["_tenant_id"] = account.tenant_id

            delivered = False
            if self._kafka:
                envelope = wrap_event(
                    connector_name="email-client",
                    event="email.received",
                    data=email_data,
                    account_name=cred_name,
                )
                try:
                    await self._kafka.send(
                        settings.kafka_topic_emails_received,
                        envelope,
                        key=msg_key,
                    )
                    delivered = True
                except Exception:
                    logger.exception("Kafka send failed for msg_key=%s", msg_key)

                if delivered:
                    seen.add(msg_key)
                    await self._state.mark_seen(account.name, msg_key)
                    if not await self._notify_platform("email.received", email_data):
                        logger.warning("Platform notify failed for msg_key=%s, Kafka delivery succeeded", msg_key)
                else:
                    all_notified = False
                    continue
            else:
                if await self._notify_platform("email.received", email_data):
                    seen.add(msg_key)
                    await self._state.mark_seen(account.name, msg_key)
                else:
                    logger.warning("Platform notify failed for msg_key=%s, will retry next poll", msg_key)
                    all_notified = False

        logger.info(
            "Polled %d emails (%d new) for account=%s folder=%s notified=%s",
            len(page.emails),
            len(new_emails),
            account.name,
            folder,
            all_notified,
        )
        if all_notified:
            await self._save_timestamp(account.name, "emails", now_str)

    def _get_last_timestamp(self, account_name: str, entity: str) -> str | None:
        return self._last_timestamps.get(account_name, {}).get(entity)

    async def _save_timestamp(self, account_name: str, entity: str, timestamp: str) -> None:
        self._last_timestamps.setdefault(account_name, {})[entity] = timestamp
        await self._state.save_timestamp(account_name, entity, timestamp)

    async def _notify_platform(self, event: str, data: dict) -> bool:
        """Notify the platform about an event. Returns True on success."""
        if not self._http_client:
            return True
        try:
            url = f"{settings.platform_api_url}/internal/events"
            headers: dict[str, str] = {}
            if settings.platform_internal_secret:
                headers["X-Internal-Secret"] = settings.platform_internal_secret
            elif settings.platform_api_key:
                headers["X-API-Key"] = settings.platform_api_key
            resp = await self._http_client.post(
                url,
                json={
                    "connector_name": "email-client",
                    "event": event,
                    "data": data,
                },
                headers=headers,
            )
            if resp.status_code < 300:
                logger.debug("Platform notified: event=%s status=%d", event, resp.status_code)
                return True
            logger.warning("Platform notify failed: event=%s status=%d", event, resp.status_code)
            return False
        except Exception:
            logger.exception("Failed to notify platform about event=%s", event)
            return False

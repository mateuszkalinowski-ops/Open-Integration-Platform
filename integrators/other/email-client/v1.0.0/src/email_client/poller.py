"""Background poller — periodically checks for new emails via IMAP."""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from src.config import EmailAccountConfig, settings
from src.email_client.imap_client import ImapClient
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from pinquark_common.kafka import KafkaMessageProducer, wrap_event

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

    async def start(self) -> None:
        self._running = True
        self._last_timestamps = await self._state.load_all_timestamps()
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
                await self._reset_imap_client(account.name)

    async def _reset_imap_client(self, account_name: str) -> None:
        client = self._imap_clients.pop(account_name, None)
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass

    async def _poll_account(self, account: EmailAccountConfig) -> None:
        imap = self._get_imap_client(account)
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        last = self._get_last_timestamp(account.name, "emails")
        since: datetime | None = None
        if last:
            since = datetime.strptime(last, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

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

        all_notified = True
        for email_msg in page.emails:
            email_data = email_msg.model_dump(mode="json")
            email_data["account_name"] = account.name

            if self._kafka:
                envelope = wrap_event(
                    connector_name="email-client",
                    event="email.received",
                    data=email_data,
                    account_name=account.name,
                )
                await self._kafka.send(
                    settings.kafka_topic_emails_received,
                    envelope,
                    key=email_msg.message_id or "",
                )

            if not await self._notify_platform("email.received", email_data):
                all_notified = False

        logger.info(
            "Polled %d new emails for account=%s folder=%s notified=%s",
            len(page.emails), account.name, folder, all_notified,
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
            if settings.platform_api_key:
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
            logger.warning("Platform notify failed: event=%s status=%d body=%s", event, resp.status_code, resp.text[:200])
            return False
        except Exception:
            logger.exception("Failed to notify platform about event=%s", event)
            return False

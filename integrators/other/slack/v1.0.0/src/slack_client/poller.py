"""Background message poller — polls Slack channels for new messages on a configurable interval."""

import asyncio
import logging

from src.config import settings
from src.services.account_manager import AccountManager
from src.slack_client.client import SlackClient
from src.slack_client.schemas import SlackMessage
from src.models.database import StateStore
from pinquark_common.kafka import KafkaMessageProducer, wrap_event

logger = logging.getLogger(__name__)


class MessagePoller:
    """Periodically fetches new messages from configured Slack channels."""

    def __init__(
        self,
        account_manager: AccountManager,
        state_store: StateStore,
        kafka_producer: KafkaMessageProducer | None = None,
    ):
        self._accounts = account_manager
        self._state_store = state_store
        self._kafka = kafka_producer
        self._clients: dict[str, SlackClient] = {}
        self._running = False

    def _get_client(self, account_name: str, bot_token: str) -> SlackClient:
        if account_name not in self._clients:
            self._clients[account_name] = SlackClient(bot_token)
        return self._clients[account_name]

    async def start(self) -> None:
        self._running = True
        logger.info(
            "Message poller started, interval=%ds, accounts=%d",
            settings.polling_interval_seconds,
            len(self._accounts.list_accounts()),
        )
        while self._running:
            await self._poll_all_accounts()
            await asyncio.sleep(settings.polling_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        logger.info("Message poller stopped")

    async def _poll_all_accounts(self) -> None:
        for account in self._accounts.list_accounts():
            try:
                client = self._get_client(account.name, account.bot_token)
                await self._poll_account(account.name, client)
            except Exception:
                logger.exception("Error polling messages for account=%s", account.name)

    async def _poll_account(self, account_name: str, client: SlackClient) -> None:
        channels_data = await client.conversations_list(
            types="public_channel,private_channel", limit=100,
        )
        member_channels = [
            ch for ch in channels_data.get("channels", [])
            if ch.get("is_member", False)
        ]

        for ch in member_channels:
            channel_id = ch["id"]
            channel_name = ch.get("name", "")
            last_ts = await self._state_store.get_timestamp(account_name, f"channel:{channel_id}")

            history = await client.conversations_history(
                channel_id, limit=20, oldest=last_ts or "",
            )
            raw_messages = history.get("messages", [])
            if not raw_messages:
                continue

            newest_ts = last_ts or ""
            for msg_data in reversed(raw_messages):
                ts = msg_data.get("ts", "")
                if last_ts and ts <= last_ts:
                    continue

                message = SlackMessage(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    user_id=msg_data.get("user", ""),
                    text=msg_data.get("text", ""),
                    ts=ts,
                    thread_ts=msg_data.get("thread_ts", ""),
                    bot_id=msg_data.get("bot_id", ""),
                    files=msg_data.get("files", []),
                    account_name=account_name,
                )

                if self._kafka:
                    envelope = wrap_event(
                        connector_name="slack",
                        event="message.received",
                        data=message.model_dump(mode="json"),
                        account_name=account_name,
                    )
                    await self._kafka.send(
                        settings.kafka_topic_messages_received,
                        envelope,
                        key=f"{channel_id}:{ts}",
                    )
                else:
                    logger.info(
                        "Message polled (no Kafka): channel=%s user=%s ts=%s",
                        channel_name, message.user_id, ts,
                    )

                if ts > newest_ts:
                    newest_ts = ts

            if newest_ts and newest_ts != last_ts:
                await self._state_store.save_timestamp(account_name, f"channel:{channel_id}", newest_ts)

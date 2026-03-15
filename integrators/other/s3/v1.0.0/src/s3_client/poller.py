"""Background poller that detects new objects in S3 buckets."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from pinquark_common.kafka import KafkaMessageProducer, wrap_event

from src.config import settings
from src.models.database import StateStore
from src.s3_client.client import S3Client
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class ObjectPoller:
    """Periodically scans configured S3 buckets for new objects across all accounts."""

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

    def _effective_interval(self) -> int:
        """Use the smallest per-account interval, falling back to global."""
        intervals = [
            a.polling_interval_seconds
            for a in self._account_manager.list_accounts()
            if a.polling_interval_seconds is not None
        ]
        if intervals:
            return min(min(intervals), settings.polling_interval_seconds)
        return settings.polling_interval_seconds

    async def start(self) -> None:
        self._running = True
        interval = self._effective_interval()
        logger.info("Object poller started (interval=%ds)", interval)
        while self._running:
            try:
                await self._poll_all_accounts()
            except Exception:
                logger.exception("Error during polling cycle")
            await asyncio.sleep(interval)

    async def stop(self) -> None:
        self._running = False
        logger.info("Object poller stopped")

    async def _poll_all_accounts(self) -> None:
        accounts = self._account_manager.list_accounts()
        for account in accounts:
            account_polling = account.polling_enabled
            if account_polling is None:
                account_polling = True
            if not account_polling:
                continue
            try:
                await self._poll_account(account.name)
            except Exception:
                logger.exception("Polling failed for account=%s", account.name)

    async def _poll_account(self, account_name: str) -> None:
        account = self._account_manager.get_account(account_name)
        if not account:
            return

        poll_bucket = account.polling_bucket or settings.polling_bucket or account.default_bucket
        if not poll_bucket:
            logger.debug("No polling bucket configured for account=%s", account_name)
            return

        poll_prefix = account.polling_prefix or settings.polling_prefix

        client = S3Client(
            account=account,
            connect_timeout=settings.connect_timeout,
            read_timeout=settings.operation_timeout,
        )

        objects = await client.list_objects(
            poll_bucket,
            prefix=poll_prefix,
        )

        known_keys = await self._state_store.get_known_files(account_name)
        new_objects = []
        current_key_set: set[str] = set()

        for obj in objects:
            current_key_set.add(obj.key)
            if obj.key not in known_keys:
                new_objects.append(obj)

        if new_objects:
            logger.info(
                "Found %d new objects for account=%s in s3://%s/%s",
                len(new_objects),
                account_name,
                poll_bucket,
                settings.polling_prefix,
            )
            for obj in new_objects:
                await self._emit_object_event(account_name, poll_bucket, obj)

        await self._state_store.update_known_files(account_name, current_key_set)

    async def _emit_object_event(
        self,
        account_name: str,
        bucket: str,
        obj: Any,
    ) -> None:
        event_data = {
            "key": obj.key,
            "bucket": bucket,
            "size": obj.size,
            "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
            "etag": obj.etag,
            "account_name": account_name,
            "detected_at": datetime.now(UTC).isoformat(),
        }

        if self._kafka_producer:
            envelope = wrap_event(
                connector_name="s3",
                event="object.new",
                data=event_data,
                account_name=account_name,
            )
            await self._kafka_producer.send(
                settings.kafka_topic_object_new,
                envelope,
                key=account_name,
            )
            logger.debug("Published object.new event to Kafka: %s", obj.key)
        else:
            logger.info("New object detected (no Kafka): %s in s3://%s", obj.key, bucket)

        if settings.platform_event_notify and settings.platform_api_url:
            try:
                import httpx

                _headers: dict[str, str] = {}
                if settings.platform_internal_secret:
                    _headers["X-Internal-Secret"] = settings.platform_internal_secret
                elif settings.platform_api_key:
                    _headers["X-API-Key"] = settings.platform_api_key
                async with httpx.AsyncClient(timeout=10.0) as http_client:
                    await http_client.post(
                        f"{settings.platform_api_url}/internal/events",
                        json={
                            "connector_name": "s3",
                            "event": "object.new",
                            "data": event_data,
                        },
                        headers=_headers,
                    )
            except Exception:
                logger.debug("Failed to notify platform about object.new event", exc_info=True)

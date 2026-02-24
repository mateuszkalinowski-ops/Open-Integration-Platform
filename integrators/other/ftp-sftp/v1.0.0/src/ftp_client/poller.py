"""Background poller that detects new files on FTP/SFTP servers."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from src.config import settings
from src.ftp_client.client import FtpSftpClient
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from pinquark_common.kafka import KafkaMessageProducer

logger = logging.getLogger(__name__)


class FilePoller:
    """Periodically scans configured directories for new files across all accounts."""

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

    async def start(self) -> None:
        self._running = True
        logger.info("File poller started (interval=%ds)", settings.polling_interval_seconds)
        while self._running:
            try:
                await self._poll_all_accounts()
            except Exception:
                logger.exception("Error during polling cycle")
            await asyncio.sleep(settings.polling_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        logger.info("File poller stopped")

    async def _poll_all_accounts(self) -> None:
        accounts = self._account_manager.list_accounts()
        for account in accounts:
            try:
                await self._poll_account(account.name)
            except Exception:
                logger.exception("Polling failed for account=%s", account.name)

    async def _poll_account(self, account_name: str) -> None:
        account = self._account_manager.get_account(account_name)
        if not account:
            return

        client = FtpSftpClient(
            account=account,
            connect_timeout=settings.connect_timeout,
            operation_timeout=settings.operation_timeout,
        )

        poll_path = settings.polling_path
        files = await client.list_files(poll_path)

        known_files = await self._state_store.get_known_files(account_name)

        new_files = []
        current_file_set: set[str] = set()
        for f in files:
            if f.is_directory:
                continue
            current_file_set.add(f.path)
            if f.path not in known_files:
                new_files.append(f)

        if new_files:
            logger.info(
                "Found %d new files for account=%s in %s",
                len(new_files), account_name, poll_path,
            )
            for f in new_files:
                await self._emit_file_event(account_name, f)

        await self._state_store.update_known_files(account_name, current_file_set)

    async def _emit_file_event(self, account_name: str, file_info: Any) -> None:
        event_data = {
            "filename": file_info.filename,
            "path": file_info.path,
            "size": file_info.size,
            "modified_at": file_info.modified_at.isoformat() if file_info.modified_at else None,
            "account_name": account_name,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

        if self._kafka_producer:
            await self._kafka_producer.send(
                settings.kafka_topic_file_new,
                event_data,
                key=account_name,
            )
            logger.debug("Published file.new event to Kafka: %s", file_info.filename)
        else:
            logger.info("New file detected (no Kafka): %s at %s", file_info.filename, file_info.path)

        if settings.platform_event_notify and settings.platform_api_url:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=10.0) as http_client:
                    await http_client.post(
                        f"{settings.platform_api_url}/internal/events",
                        json={
                            "connector_name": "ftp-sftp",
                            "event": "file.new",
                            "data": event_data,
                        },
                        headers={"X-API-Key": settings.platform_api_key} if settings.platform_api_key else {},
                    )
            except Exception:
                logger.debug("Failed to notify platform about file.new event", exc_info=True)

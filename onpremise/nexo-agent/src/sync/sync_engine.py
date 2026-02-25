"""Bidirectional sync engine — polls Nexo for changes and pushes to cloud.

Handles:
- Outbound: detect changes in Nexo -> queue -> send to cloud platform
- Inbound: receive commands from cloud -> execute in Nexo
- Offline resilience: queue operations when cloud is unreachable
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from src.bridge.nexo_connection import NexoConnectionPool
from src.config import settings
from src.services.nexo.contractor_service import ContractorService
from src.services.nexo.product_service import ProductService
from src.services.nexo.stock_service import StockService
from src.sync.offline_queue import OfflineQueue

logger = logging.getLogger(__name__)


class SyncEngine:
    """Manages bidirectional sync between Nexo ERP and the cloud platform."""

    def __init__(
        self,
        connection_pool: NexoConnectionPool,
        offline_queue: OfflineQueue,
    ):
        self._pool = connection_pool
        self._queue = offline_queue
        self._running = False
        self._task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._client = httpx.AsyncClient(timeout=60.0)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Sync engine started (interval=%ds)", settings.sync_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._client.aclose()
        logger.info("Sync engine stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._run_sync_cycle()
            except Exception:
                logger.exception("Sync cycle failed")
            await asyncio.sleep(settings.sync_interval_seconds)

    async def _run_sync_cycle(self) -> None:
        """Execute one full sync cycle."""
        if not self._pool._connection.is_connected:
            logger.warning("Nexo not connected, skipping sync cycle")
            return

        logger.debug("Starting sync cycle")
        start = datetime.now(timezone.utc)

        await self._sync_outbound_contractors()
        await self._sync_outbound_products()
        await self._sync_outbound_stock()

        await self._flush_queue()

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.debug("Sync cycle completed in %.1fs", elapsed)

    async def _sync_outbound_contractors(self) -> None:
        """Detect new/changed contractors and queue them for cloud sync."""
        try:
            conn = self._pool.ensure_connected()
            svc = ContractorService(conn)
            result = svc.list_contractors(page=1, page_size=settings.sync_batch_size)

            last_state = await self._queue.get_sync_state("contractors", "outbound")
            last_sync = last_state.get("last_sync_at") if last_state else None

            synced_count = 0
            for item in result.get("items", []):
                updated = item.get("updated_at")
                if last_sync and updated and updated <= last_sync:
                    continue

                await self._queue.enqueue("contractor", "sync", item)
                synced_count += 1

            if synced_count > 0:
                await self._queue.update_sync_state("contractors", "outbound")
                logger.info("Queued %d contractors for outbound sync", synced_count)
        except Exception:
            logger.debug("Contractor outbound sync skipped", exc_info=True)

    async def _sync_outbound_products(self) -> None:
        """Detect new/changed products and queue them for cloud sync."""
        try:
            conn = self._pool.ensure_connected()
            svc = ProductService(conn)
            result = svc.list_products(page=1, page_size=settings.sync_batch_size)

            last_state = await self._queue.get_sync_state("products", "outbound")
            last_sync = last_state.get("last_sync_at") if last_state else None

            synced_count = 0
            for item in result.get("items", []):
                updated = item.get("updated_at")
                if last_sync and updated and updated <= last_sync:
                    continue

                await self._queue.enqueue("product", "sync", item)
                synced_count += 1

            if synced_count > 0:
                await self._queue.update_sync_state("products", "outbound")
                logger.info("Queued %d products for outbound sync", synced_count)
        except Exception:
            logger.debug("Product outbound sync skipped", exc_info=True)

    async def _sync_outbound_stock(self) -> None:
        """Sync current stock levels to cloud."""
        try:
            conn = self._pool.ensure_connected()
            svc = StockService(conn)
            result = svc.get_stock_levels()

            if result.items:
                payload = {
                    "warehouse": result.warehouse_symbol,
                    "items": [item.model_dump() for item in result.items],
                    "total": result.total_products,
                    "as_of": result.as_of.isoformat() if result.as_of else None,
                }
                await self._queue.enqueue("stock", "full_sync", payload)
                await self._queue.update_sync_state("stock", "outbound")
                logger.info("Queued stock levels sync (%d items)", result.total_products)
        except Exception:
            logger.debug("Stock outbound sync skipped", exc_info=True)

    async def _flush_queue(self) -> None:
        """Send queued operations to the cloud platform."""
        if not settings.cloud_platform_url or not settings.cloud_api_key:
            return

        pending = await self._queue.get_pending(limit=50)
        if not pending:
            return

        logger.debug("Flushing %d queued operations to cloud", len(pending))

        for item in pending:
            try:
                response = await self._client.post(
                    f"{settings.cloud_platform_url}/api/v1/agents/sync",
                    json={
                        "agent_id": settings.agent_id,
                        "entity_type": item["entity_type"],
                        "operation": item["operation"],
                        "payload": item["payload"],
                    },
                    headers={
                        "Authorization": f"Bearer {settings.cloud_api_key}",
                        "X-Agent-Id": settings.agent_id,
                    },
                )
                if response.status_code < 300:
                    await self._queue.mark_processed(item["id"])
                else:
                    await self._queue.mark_failed(
                        item["id"],
                        f"HTTP {response.status_code}: {response.text[:200]}",
                    )
            except httpx.RequestError as exc:
                await self._queue.mark_failed(item["id"], str(exc))
                logger.debug("Cloud unreachable during flush, will retry next cycle")
                break

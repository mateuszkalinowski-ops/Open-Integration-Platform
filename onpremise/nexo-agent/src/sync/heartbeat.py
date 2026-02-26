"""Heartbeat service — sends periodic status to Pinquark Cloud.

Reports: agent version, connection status, queue depth,
system resources, and ERP health information.
"""

import asyncio
import logging
import platform
import time
from datetime import datetime, timezone

import httpx

from src.bridge.nexo_connection import NexoConnectionPool
from src.config import settings
from src.sync.offline_queue import OfflineQueue

logger = logging.getLogger(__name__)


class HeartbeatService:
    def __init__(
        self,
        connection_pool: NexoConnectionPool,
        offline_queue: OfflineQueue,
    ):
        self._pool = connection_pool
        self._queue = offline_queue
        self._running = False
        self._task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._client = httpx.AsyncClient(timeout=30.0)
        self._consecutive_cloud_failures = 0

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "Heartbeat service started (interval=%ds, cloud=%s)",
            settings.heartbeat_interval_seconds,
            settings.cloud_platform_url,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._client.aclose()
        logger.info("Heartbeat service stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._send_heartbeat()
            except Exception:
                logger.exception("Heartbeat send failed")
            await asyncio.sleep(settings.heartbeat_interval_seconds)

    async def _send_heartbeat(self) -> None:
        conn = self._pool._connection

        erp_ping = {"status": "disconnected"}
        if conn.is_connected:
            erp_ping = conn.ping()

        queue_depth = await self._queue.get_queue_depth()

        payload = {
            "agent_id": settings.agent_id,
            "agent_version": settings.app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "erp": {
                "type": "insert-nexo",
                "product": settings.nexo_product,
                "connected": conn.is_connected,
                "status": conn.status.value,
                "consecutive_failures": conn.consecutive_failures,
                "ping": erp_ping,
            },
            "queue": {
                "depth": queue_depth,
                "total_pending": queue_depth.get("pending", 0),
            },
            "system": {
                "os": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "uptime_seconds": round(time.monotonic(), 1),
            },
        }

        if not settings.cloud_platform_url or not settings.cloud_api_key:
            logger.debug("Heartbeat (local only): %s", payload.get("erp", {}).get("status"))
            return

        try:
            response = await self._client.post(
                f"{settings.cloud_platform_url}/api/v1/agents/heartbeat",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.cloud_api_key}",
                    "X-Agent-Id": settings.agent_id,
                },
            )
            if response.status_code < 300:
                self._consecutive_cloud_failures = 0
                logger.debug("Heartbeat sent successfully")
            else:
                self._consecutive_cloud_failures += 1
                logger.warning(
                    "Heartbeat rejected: status=%d, failures=%d",
                    response.status_code,
                    self._consecutive_cloud_failures,
                )
        except httpx.RequestError:
            self._consecutive_cloud_failures += 1
            logger.warning(
                "Cloud unreachable (failures=%d), operations queued locally",
                self._consecutive_cloud_failures,
            )

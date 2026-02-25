"""SQLite-based offline queue for operations when cloud connection is lost.

Queues outbound sync operations locally and replays them when connectivity
is restored. Implements the resilience pattern from AGENTS.md Section 8.2.
"""

import json
import logging
from datetime import datetime, timezone

import aiosqlite

logger = logging.getLogger(__name__)


class OfflineQueue:
    def __init__(self, db_path: str = "nexo_agent_queue.db"):
        self._db_path = db_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS outbound_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP NULL,
                    error TEXT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    entity_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    last_sync_at TIMESTAMP,
                    last_id TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (entity_type, direction)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_status
                ON outbound_queue(status)
            """)
            await db.commit()
        logger.info("Offline queue initialized: %s", self._db_path)

    async def enqueue(self, entity_type: str, operation: str, payload: dict) -> int:
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "INSERT INTO outbound_queue (entity_type, operation, payload) VALUES (?, ?, ?)",
                (entity_type, operation, json.dumps(payload, default=str)),
            )
            await db.commit()
            row_id = cursor.lastrowid or 0
            logger.debug("Enqueued: type=%s op=%s id=%d", entity_type, operation, row_id)
            return row_id

    async def get_pending(self, limit: int = 100) -> list[dict]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, entity_type, operation, payload, attempts, max_attempts
                   FROM outbound_queue
                   WHERE status = 'pending' AND attempts < max_attempts
                   ORDER BY id ASC LIMIT ?""",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "entity_type": row["entity_type"],
                    "operation": row["operation"],
                    "payload": json.loads(row["payload"]),
                    "attempts": row["attempts"],
                }
                for row in rows
            ]

    async def mark_processed(self, queue_id: int) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE outbound_queue SET status = 'processed', processed_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), queue_id),
            )
            await db.commit()

    async def mark_failed(self, queue_id: int, error: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """UPDATE outbound_queue
                   SET attempts = attempts + 1,
                       error = ?,
                       status = CASE WHEN attempts + 1 >= max_attempts THEN 'dead_letter' ELSE 'pending' END
                   WHERE id = ?""",
                (error, queue_id),
            )
            await db.commit()

    async def get_queue_depth(self) -> dict:
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT status, COUNT(*) as cnt FROM outbound_queue GROUP BY status"
            )
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    async def update_sync_state(
        self, entity_type: str, direction: str, last_id: str = ""
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO sync_state (entity_type, direction, last_sync_at, last_id, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(entity_type, direction) DO UPDATE SET
                       last_sync_at = excluded.last_sync_at,
                       last_id = excluded.last_id,
                       updated_at = excluded.updated_at""",
                (entity_type, direction, now, last_id, now),
            )
            await db.commit()

    async def get_sync_state(self, entity_type: str, direction: str) -> dict | None:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM sync_state WHERE entity_type = ? AND direction = ?",
                (entity_type, direction),
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

"""Async state persistence using aiosqlite for poller timestamps."""

import logging

import aiosqlite

from src.config import settings

logger = logging.getLogger(__name__)

DB_PATH = "email_client_integrator.db"


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite"):
        path = url.split("///")[-1]
        return path if path else DB_PATH
    return DB_PATH


class StateStore:
    """Async SQLite-backed store for poller state."""

    def __init__(self) -> None:
        self._db_path = _db_path()

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS poller_state (
                    account_name TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    last_timestamp TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (account_name, entity)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS seen_message_ids (
                    account_name TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (account_name, message_id)
                )
            """)
            await db.commit()
        logger.info("State store initialized at %s", self._db_path)

    async def save_timestamp(self, account_name: str, entity: str, timestamp: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO poller_state (account_name, entity, last_timestamp)
                   VALUES (?, ?, ?)
                   ON CONFLICT(account_name, entity)
                   DO UPDATE SET last_timestamp=excluded.last_timestamp, updated_at=CURRENT_TIMESTAMP""",
                (account_name, entity, timestamp),
            )
            await db.commit()

    async def load_all_timestamps(self) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute("SELECT account_name, entity, last_timestamp FROM poller_state") as cursor,
        ):
            async for row in cursor:
                account_name, entity, timestamp = row
                result.setdefault(account_name, {})[entity] = timestamp
        return result

    async def mark_seen(self, account_name: str, message_id: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO seen_message_ids (account_name, message_id) VALUES (?, ?)",
                (account_name, message_id),
            )
            await db.commit()

    async def is_seen(self, account_name: str, message_id: str) -> bool:
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute(
                "SELECT 1 FROM seen_message_ids WHERE account_name = ? AND message_id = ?",
                (account_name, message_id),
            ) as cursor,
        ):
            return await cursor.fetchone() is not None

    async def load_seen_ids(self, account_name: str, limit: int = 500) -> set[str]:
        result: set[str] = set()
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute(
                "SELECT message_id FROM seen_message_ids WHERE account_name = ? ORDER BY seen_at DESC LIMIT ?",
                (account_name, limit),
            ) as cursor,
        ):
            async for row in cursor:
                result.add(row[0])
        return result

    async def prune_seen_ids(self, account_name: str, keep: int = 1000) -> None:
        """Remove oldest entries beyond the keep limit."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """DELETE FROM seen_message_ids
                   WHERE account_name = ? AND rowid NOT IN (
                       SELECT rowid FROM seen_message_ids
                       WHERE account_name = ? ORDER BY seen_at DESC LIMIT ?
                   )""",
                (account_name, account_name, keep),
            )
            await db.commit()

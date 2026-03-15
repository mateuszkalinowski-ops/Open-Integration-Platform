"""Async state persistence using aiosqlite for poller state tracking."""

import logging

import aiosqlite

from src.config import settings

logger = logging.getLogger(__name__)

DB_PATH = "skanuj_fakture_integrator.db"


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite"):
        path = url.split("///")[-1]
        return path if path else DB_PATH
    return DB_PATH


class StateStore:
    """Async SQLite-backed store for poller state — tracks which documents have been seen."""

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
                CREATE TABLE IF NOT EXISTS known_documents (
                    account_name TEXT NOT NULL,
                    document_id INTEGER NOT NULL,
                    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (account_name, document_id)
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

    async def save_document_id(self, account_name: str, document_id: int) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT OR IGNORE INTO known_documents (account_name, document_id) VALUES (?, ?)""",
                (account_name, document_id),
            )
            await db.commit()

    async def load_known_document_ids(self, account_name: str) -> set[int]:
        result: set[int] = set()
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute(
                "SELECT document_id FROM known_documents WHERE account_name = ?",
                (account_name,),
            ) as cursor,
        ):
            async for row in cursor:
                result.add(row[0])
        return result

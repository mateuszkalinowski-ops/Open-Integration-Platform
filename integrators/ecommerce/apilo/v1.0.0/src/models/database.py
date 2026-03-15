"""Async state persistence using aiosqlite for scraper timestamps."""

import logging

import aiosqlite

from src.config import settings

logger = logging.getLogger(__name__)

DB_PATH = "apilo_integrator.db"


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite"):
        path = url.split("///")[-1]
        return path if path else DB_PATH
    return DB_PATH


class StateStore:
    """Async SQLite-backed store for scraper state."""

    def __init__(self) -> None:
        self._db_path = _db_path()

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scraper_state (
                    account_name TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    last_timestamp TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (account_name, entity)
                )
            """)
            await db.commit()
        logger.info("State store initialized at %s", self._db_path)

    async def save_timestamp(self, account_name: str, entity: str, timestamp: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO scraper_state (account_name, entity, last_timestamp)
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
            db.execute("SELECT account_name, entity, last_timestamp FROM scraper_state") as cursor,
        ):
            async for row in cursor:
                account_name, entity, timestamp = row
                result.setdefault(account_name, {})[entity] = timestamp
        return result

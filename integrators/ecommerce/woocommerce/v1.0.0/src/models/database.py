"""Lightweight async state persistence using aiosqlite.

Stores scraper checkpoint state and account metadata.
"""

import logging

import aiosqlite

from src.config import settings

logger = logging.getLogger(__name__)

DB_PATH = "woocommerce_integrator.db"


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite"):
        path = url.split("///")[-1]
        return path if path else DB_PATH
    return DB_PATH


class StateStore:
    """Async SQLite-backed store for scraper state and metadata."""

    def __init__(self) -> None:
        self._db_path = _db_path()

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scraper_state (
                    account_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    last_scraped TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (account_name, entity_type)
                )
            """)
            await db.commit()
        logger.info("State store initialized at %s", self._db_path)

    async def save_last_scraped(self, account_name: str, entity_type: str, timestamp: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO scraper_state (account_name, entity_type, last_scraped)
                   VALUES (?, ?, ?)
                   ON CONFLICT(account_name, entity_type)
                   DO UPDATE SET last_scraped=excluded.last_scraped, updated_at=CURRENT_TIMESTAMP""",
                (account_name, entity_type, timestamp),
            )
            await db.commit()

    async def get_last_scraped(self, account_name: str, entity_type: str) -> str | None:
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute(
                "SELECT last_scraped FROM scraper_state WHERE account_name = ? AND entity_type = ?",
                (account_name, entity_type),
            ) as cursor,
        ):
            row = await cursor.fetchone()
            return row[0] if row else None

    async def get_all_states(self) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute("SELECT account_name, entity_type, last_scraped FROM scraper_state") as cursor,
        ):
            async for row in cursor:
                account_name, entity_type, last_scraped = row
                if account_name not in result:
                    result[account_name] = {}
                result[account_name][entity_type] = last_scraped
        return result

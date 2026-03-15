"""Lightweight async token and state persistence using aiosqlite.

Stores OAuth tokens (encrypted) and scraper checkpoint state.
Can be swapped for PostgreSQL via DATABASE_URL env var.
"""

import json
import logging
from typing import Any

import aiosqlite
from pinquark_common.security import decrypt_value, encrypt_value

from src.config import settings

logger = logging.getLogger(__name__)

DB_PATH = "allegro_integrator.db"


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite"):
        path = url.split("///")[-1]
        return path if path else DB_PATH
    return DB_PATH


class TokenStore:
    """Async SQLite-backed store for OAuth tokens and scraper state."""

    def __init__(self):
        self._db_path = _db_path()
        self._encryption_key = settings.encryption_key

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    account_name TEXT PRIMARY KEY,
                    token_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scraper_state (
                    account_name TEXT PRIMARY KEY,
                    last_event_id TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
        logger.info("Token store initialized at %s", self._db_path)

    async def save_token(self, account_name: str, token_data: dict[str, Any]) -> None:
        raw = json.dumps(token_data, default=str)
        stored = encrypt_value(raw, self._encryption_key) if self._encryption_key else raw
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO oauth_tokens (account_name, token_data)
                   VALUES (?, ?)
                   ON CONFLICT(account_name) DO UPDATE SET token_data=excluded.token_data, updated_at=CURRENT_TIMESTAMP""",
                (account_name, stored),
            )
            await db.commit()

    async def load_all_tokens(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute("SELECT account_name, token_data FROM oauth_tokens") as cursor,
        ):
            async for row in cursor:
                account_name, stored = row
                try:
                    raw = decrypt_value(stored, self._encryption_key) if self._encryption_key else stored
                    result[account_name] = json.loads(raw)
                except Exception:
                    logger.warning("Failed to decrypt token for account=%s, skipping", account_name)
        return result

    async def delete_token(self, account_name: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM oauth_tokens WHERE account_name = ?", (account_name,))
            await db.commit()

    async def save_last_event_id(self, account_name: str, event_id: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO scraper_state (account_name, last_event_id)
                   VALUES (?, ?)
                   ON CONFLICT(account_name) DO UPDATE SET last_event_id=excluded.last_event_id, updated_at=CURRENT_TIMESTAMP""",
                (account_name, event_id),
            )
            await db.commit()

    async def load_all_last_event_ids(self) -> dict[str, str]:
        result: dict[str, str] = {}
        async with (
            aiosqlite.connect(self._db_path) as db,
            db.execute("SELECT account_name, last_event_id FROM scraper_state") as cursor,
        ):
            async for row in cursor:
                result[row[0]] = row[1]
        return result

"""Async SQLite state store for persisting poller state (known object keys)."""

import json
import logging

import aiosqlite

from src.config import settings

logger = logging.getLogger(__name__)

DB_PATH = "s3_state.db"


class StateStore:
    """Lightweight SQLite-backed persistence for polling state."""

    def __init__(self) -> None:
        self._db_path = DB_PATH
        db_url = settings.database_url
        if ":///" in db_url:
            path_part = db_url.split(":///", 1)[1]
            if path_part:
                self._db_path = path_part

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS known_files (
                    account_name TEXT PRIMARY KEY,
                    file_paths TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            await db.commit()
        logger.info("State store initialized at %s", self._db_path)

    async def get_known_files(self, account_name: str) -> set[str]:
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT file_paths FROM known_files WHERE account_name = ?",
                (account_name,),
            )
            row = await cursor.fetchone()
            if row:
                return set(json.loads(row[0]))
            return set()

    async def update_known_files(self, account_name: str, file_paths: set[str]) -> None:
        paths_json = json.dumps(sorted(file_paths))
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO known_files (account_name, file_paths)
                VALUES (?, ?)
                ON CONFLICT(account_name) DO UPDATE SET file_paths = excluded.file_paths
                """,
                (account_name, paths_json),
            )
            await db.commit()

    async def load_all_timestamps(self) -> None:
        """Health-check probe — verifies DB connectivity."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("SELECT COUNT(*) FROM known_files")

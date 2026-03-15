"""Database initialisation & migration runner.

Usage:
    python -m db.init_db              # apply all pending migrations
    python -m db.init_db --stamp      # mark current DB as up-to-date (existing DB baseline)
    python -m db.init_db --check      # exit 0 if up-to-date, 1 otherwise
    python -m db.init_db --current    # print current revision

On a **fresh** database the script creates the ``alembic_version`` table and
runs every migration from 001 onward.

On an **existing** database that predates Alembic (no ``alembic_version``
table) the script detects live tables and stamps the baseline revision so
that future migrations apply incrementally.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

PLATFORM_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = PLATFORM_DIR / "alembic.ini"
BASELINE_REV = "001"


def _alembic_cfg() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(PLATFORM_DIR / "db" / "migrations"))

    from config import settings

    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def _sync_url() -> str:
    from config import settings

    return settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")


def _table_exists(engine, table_name: str) -> bool:  # type: ignore[no-untyped-def]
    insp = inspect(engine)
    return table_name in insp.get_table_names()


def apply_migrations() -> None:
    """Run ``alembic upgrade head``, auto-stamping baseline for existing DBs."""
    sync_url = _sync_url()
    engine = create_engine(sync_url)

    has_alembic = _table_exists(engine, "alembic_version")
    has_tables = _table_exists(engine, "tenants")

    cfg = _alembic_cfg()
    cfg.set_main_option("sqlalchemy.url", sync_url)

    if has_tables and not has_alembic:
        print(f"[init_db] Existing database detected without alembic_version — stamping baseline ({BASELINE_REV})")
        command.stamp(cfg, BASELINE_REV)

    print("[init_db] Running migrations (upgrade head)...")
    command.upgrade(cfg, "head")
    print("[init_db] Migrations complete.")

    engine.dispose()


def stamp_baseline() -> None:
    """Mark the DB at the baseline revision without running SQL."""
    sync_url = _sync_url()
    cfg = _alembic_cfg()
    cfg.set_main_option("sqlalchemy.url", sync_url)
    command.stamp(cfg, BASELINE_REV)
    print(f"[init_db] Stamped at {BASELINE_REV}")


def show_current() -> None:
    sync_url = _sync_url()
    cfg = _alembic_cfg()
    cfg.set_main_option("sqlalchemy.url", sync_url)
    command.current(cfg, verbose=True)


def check_current() -> bool:
    """Return True if the DB is at head."""
    sync_url = _sync_url()
    cfg = _alembic_cfg()
    cfg.set_main_option("sqlalchemy.url", sync_url)

    engine = create_engine(sync_url)
    if not _table_exists(engine, "alembic_version"):
        engine.dispose()
        return False

    with engine.connect() as conn:
        row = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
    engine.dispose()

    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()

    current = row[0] if row else None
    is_current = current == head
    print(f"[init_db] current={current}  head={head}  up_to_date={is_current}")
    return is_current


def main() -> None:
    sys.path.insert(0, str(PLATFORM_DIR))

    parser = argparse.ArgumentParser(description="Pinquark DB initialisation")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stamp", action="store_true", help="Stamp baseline without running SQL")
    group.add_argument("--check", action="store_true", help="Check if DB is at head")
    group.add_argument("--current", action="store_true", help="Show current revision")
    args = parser.parse_args()

    if args.stamp:
        stamp_baseline()
    elif args.check:
        ok = check_current()
        sys.exit(0 if ok else 1)
    elif args.current:
        show_current()
    else:
        apply_migrations()


if __name__ == "__main__":
    main()

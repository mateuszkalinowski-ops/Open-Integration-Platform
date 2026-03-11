"""Background OAuth2 token refresher.

Runs every 60 seconds, finds tokens expiring within 5 minutes,
and proactively refreshes them to avoid interruptions.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.connector_registry import ConnectorRegistry
from core.credential_vault import CredentialVault
from core.oauth2_manager import OAuth2Manager

logger = structlog.get_logger(__name__)


class OAuth2Refresher:
    """Proactive background refresher for OAuth2 tokens."""

    def __init__(
        self,
        oauth2_manager: OAuth2Manager,
        session_factory: async_sessionmaker[AsyncSession],
        registry: ConnectorRegistry,
        vault: CredentialVault | None = None,
        *,
        check_interval: int = 60,
        refresh_before_expiry: int = 300,
    ) -> None:
        self._manager = oauth2_manager
        self._session_factory = session_factory
        self._registry = registry
        self._vault = vault
        self._check_interval = check_interval
        self._refresh_before = refresh_before_expiry
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "oauth2_refresher.started",
            interval=self._check_interval,
            refresh_before=self._refresh_before,
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("oauth2_refresher.stopped")

    async def _loop(self) -> None:
        while True:
            try:
                await self._refresh_expiring_tokens()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("oauth2_refresher.error")
            await asyncio.sleep(self._check_interval)

    def _get_refresh_window(self, connector_name: str) -> int:
        """Return the refresh-before-expiry window for a connector (seconds).

        Uses ``refresh_before_expiry_seconds`` from the connector manifest's
        ``oauth2`` block when available; falls back to the instance-level default.
        """
        oauth2 = self._get_oauth2_config(connector_name)
        if oauth2:
            val = oauth2.get("refresh_before_expiry_seconds")
            if isinstance(val, int) and val > 0:
                return val
        return self._refresh_before

    async def _refresh_expiring_tokens(self) -> None:
        async with self._session_factory() as db:
            from db.base import set_rls_bypass
            await set_rls_bypass(db)

            max_window = self._refresh_before
            for m in self._registry.get_all():
                oauth2_cfg = getattr(m, "oauth2", None) or {}
                rbe = oauth2_cfg.get("refresh_before_expiry_seconds")
                if isinstance(rbe, int) and rbe > 0:
                    max_window = max(max_window, rbe)

            tokens = await self._manager.get_tokens_expiring_soon(db, max_window)
            if not tokens:
                return

            tokens = [
                t for t in tokens
                if t.expires_at is not None
                and t.expires_at
                <= datetime.now(timezone.utc) + timedelta(seconds=self._get_refresh_window(t.connector_name))
            ]
            if not tokens:
                return

            logger.info("oauth2_refresher.found_expiring", count=len(tokens))

            for token in tokens:
                oauth2_config = self._get_oauth2_config(token.connector_name)
                if not oauth2_config:
                    logger.warning(
                        "oauth2_refresher.no_config",
                        connector=token.connector_name,
                    )
                    continue

                merged_config = dict(oauth2_config)
                if self._vault:
                    try:
                        creds = await self._vault.retrieve_all(
                            db, token.tenant_id, token.connector_name,
                            credential_name=token.credential_name,
                        )
                        if "client_id" in creds:
                            merged_config["client_id"] = creds["client_id"]
                        if "client_secret" in creds:
                            merged_config["client_secret"] = creds["client_secret"]
                    except Exception:
                        logger.warning(
                            "oauth2_refresher.credential_load_failed",
                            connector=token.connector_name,
                        )

                try:
                    await self._manager.refresh_token(db, token, merged_config)
                except Exception:
                    logger.exception(
                        "oauth2_refresher.refresh_failed",
                        connector=token.connector_name,
                        tenant_id=str(token.tenant_id),
                    )

            await db.commit()

    def _get_oauth2_config(self, connector_name: str) -> dict[str, Any] | None:
        """Look up OAuth2 config from connector manifest."""
        manifests = self._registry.get_by_name(connector_name)
        if not manifests:
            return None
        manifest = manifests[0]
        oauth2: dict[str, Any] = getattr(manifest, "oauth2", {}) or {}
        if not oauth2:
            cv = manifest.credential_validation or {}
            oauth2 = cv.get("oauth2", {})
        return oauth2 if oauth2 else None

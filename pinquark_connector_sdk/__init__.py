"""Workspace import shim for the local connector SDK package.

Allows repository-local imports like ``import pinquark_connector_sdk`` to work
without installing the SDK wheel first. This keeps migrated connector tests and
entrypoints importable directly from the monorepo checkout.
"""

from __future__ import annotations

from pathlib import Path

_SDK_PACKAGE_DIR = Path(__file__).resolve().parents[1] / "sdk/python/pinquark_connector_sdk"
if str(_SDK_PACKAGE_DIR) not in __path__:
    __path__.append(str(_SDK_PACKAGE_DIR))

from .app import ConnectorApp
from .decorators import action, trigger, webhook
from .legacy import augment_legacy_fastapi_app

__all__ = ["ConnectorApp", "action", "trigger", "webhook", "augment_legacy_fastapi_app"]

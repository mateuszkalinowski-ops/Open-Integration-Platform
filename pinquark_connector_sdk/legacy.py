"""Workspace shim for the SDK legacy bridge module."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "sdk/python/pinquark_connector_sdk/legacy.py"
_SPEC = importlib.util.spec_from_file_location("pinquark_connector_sdk._legacy_impl", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

augment_legacy_fastapi_app = _MODULE.augment_legacy_fastapi_app

__all__ = ["augment_legacy_fastapi_app"]

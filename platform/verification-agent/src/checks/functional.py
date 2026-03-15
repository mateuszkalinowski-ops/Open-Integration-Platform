"""Tier 3 — Functional smoke tests dispatcher.

Auto-discovers test modules by convention — no hardcoded registries needed.
When a new connector test file is added to the correct category folder, it
is automatically picked up.

Resolution order:
  1. checks/{category}/{connector_name}.py  (connector-specific)
  2. checks/{category}/generic.py           (category fallback)
  3. SKIP — no tests available
"""

import importlib
import logging
from typing import Any

import httpx

from src.checks.common import result
from src.discovery import VerificationTarget

logger = logging.getLogger(__name__)


def _resolve_test_module(name: str, interface: str, category: str) -> Any | None:
    """Dynamically resolve the test module for a connector.

    Tries connector-specific module first, then interface-based, then
    category generic fallback.
    """
    normalized_name = name.replace("-", "_")
    normalized_interface = interface.replace("-", "_")
    normalized_category = category.replace("-", "_")

    candidates = [
        f"src.checks.{normalized_category}.{normalized_name}",
        f"src.checks.{normalized_category}.{normalized_interface}",
        f"src.checks.{normalized_category}.generic",
    ]

    if interface != category:
        candidates.insert(1, f"src.checks.other.{normalized_interface}")

    for module_name in candidates:
        try:
            return importlib.import_module(module_name)
        except ImportError:
            continue

    return None


async def run_tier3(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    """Run Tier 3 functional checks based on connector identity."""
    if not target.credentials:
        return [result("functional_tests", "SKIP", 0, error="No credentials — skipping functional tests")]

    name = target.manifest.name
    interface = target.manifest.interface
    category = target.manifest.category

    module = _resolve_test_module(name, interface, category)

    if module:
        return await module.run(client, target)

    return [
        result(
            "functional_smoke",
            "SKIP",
            0,
            error=f"No functional tests defined for category={category} interface={interface}",
        )
    ]

"""Tier 3 — Functional smoke tests dispatcher.

Routes each connector to its dedicated test module based on connector name,
interface, or category. Per-connector tests live in category subdirectories:

    checks/courier/       — courier connector tests
    checks/ecommerce/     — e-commerce connector tests
    checks/erp/           — ERP connector tests
    checks/automation/    — automation connector tests
    checks/other/         — other connectors (skanuj-fakture, email, ftp, etc.)

Each category has a generic.py fallback; connector-specific files override it.
"""

from typing import Any

import httpx

from src.checks.common import result
from src.checks.courier import dhl_express as courier_dhl_express
from src.checks.courier import generic as courier_generic
from src.checks.ecommerce import generic as ecommerce_generic
from src.checks.other import account_based as other_account_based
from src.checks.other import skanuj_fakture as other_skanuj_fakture
from src.discovery import VerificationTarget

_CONNECTOR_REGISTRY: dict[str, Any] = {
    "skanuj-fakture": other_skanuj_fakture,
    "dhl-express": courier_dhl_express,
}

_INTERFACE_REGISTRY: dict[str, Any] = {
    "email": other_account_based,
    "ftp-sftp": other_account_based,
}

_CATEGORY_REGISTRY: dict[str, Any] = {
    "courier": courier_generic,
    "ecommerce": ecommerce_generic,
}


async def run_tier3(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    """Run Tier 3 functional checks based on connector identity."""
    if not target.credentials:
        return [result("functional_tests", "SKIP", 0,
                       error="No credentials — skipping functional tests")]

    name = target.manifest.name
    interface = target.manifest.interface
    category = target.manifest.category

    module = (
        _CONNECTOR_REGISTRY.get(name)
        or _INTERFACE_REGISTRY.get(interface)
        or _CATEGORY_REGISTRY.get(category)
    )

    if module:
        return await module.run(client, target)

    return [result("functional_smoke", "SKIP", 0,
                   error=f"No functional tests defined for category={category} interface={interface}")]

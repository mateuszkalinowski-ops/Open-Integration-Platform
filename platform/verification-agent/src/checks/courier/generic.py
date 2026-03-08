"""Tier 3 functional checks — Generic courier connector fallback.

Tests read-only endpoints: pickup points, rates, tracking status.
Used when no connector-specific test module exists.
"""

from typing import Any

import httpx

from src.checks.common import get_check
from src.discovery import VerificationTarget


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url

    if "get_pickup_points" in target.manifest.capabilities:
        results.append(await get_check(
            client, f"{base}/pickup-points", "list_pickup_points",
        ))

    if "get_rates" in target.manifest.capabilities or "rates.get" in target.manifest.actions:
        results.append(await get_check(
            client, f"{base}/rates", "rates_endpoint",
        ))

    return results

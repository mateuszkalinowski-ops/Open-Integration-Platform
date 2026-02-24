"""Tier 3 functional checks — Generic e-commerce connector fallback.

Tests read-only listing endpoints: orders, products.
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
    account = (target.credentials or {}).get("account_name", "verification-agent")

    if "order.fetch" in target.manifest.actions:
        results.append(await get_check(
            client, f"{base}/orders", "list_orders",
            params={"account_name": account, "per_page": "1"},
        ))

    if "product.search" in target.manifest.actions:
        results.append(await get_check(
            client, f"{base}/products/search", "search_products",
            params={"account_name": account, "query": "test", "page": "1", "page_size": "1"},
        ))

    return results

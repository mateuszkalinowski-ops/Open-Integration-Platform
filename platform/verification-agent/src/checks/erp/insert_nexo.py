"""Tier 3 functional checks — InsERT Nexo (Subiekt) cloud connector.

Tests the cloud connector's ability to proxy requests to on-premise agents.
The agent must be reachable for functional tests to pass.
"""

from typing import Any

import httpx

from src.checks.common import req_check, result
from src.discovery import VerificationTarget


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url

    r, resp = await req_check(client, "GET", f"{base}/accounts", "list_accounts")
    results.append(r)

    accounts = []
    if resp and resp.status_code == 200:
        data = resp.json()
        accounts = data.get("accounts", [])

    if not accounts:
        results.append(
            result("agent_connectivity", "SKIP", 0, error="No agent accounts configured — skipping agent tests")
        )
        return results

    account_name = accounts[0].get("name", "")

    r, resp = await req_check(
        client,
        "GET",
        f"{base}/agents/{account_name}/health",
        "agent_health",
    )
    results.append(r)

    if resp and resp.status_code == 502:
        results.append(
            result("agent_tests", "SKIP", 0, error="On-premise agent unreachable (502) — skipping agent tests")
        )
        return results

    r, _ = await req_check(
        client,
        "GET",
        f"{base}/agents/{account_name}/connection/status",
        "agent_connection_status",
    )
    results.append(r)

    r, _ = await req_check(
        client,
        "GET",
        f"{base}/agents/{account_name}/contractors",
        "list_contractors",
        params={"page": 1, "page_size": 5},
    )
    results.append(r)

    r, _ = await req_check(
        client,
        "GET",
        f"{base}/agents/{account_name}/products",
        "list_products",
        params={"page": 1, "page_size": 5},
    )
    results.append(r)

    r, _ = await req_check(
        client,
        "GET",
        f"{base}/agents/{account_name}/documents/sales",
        "list_sales_documents",
        params={"page": 1, "page_size": 5},
    )
    results.append(r)

    r, _ = await req_check(
        client,
        "GET",
        f"{base}/agents/{account_name}/orders",
        "list_orders",
        params={"page": 1, "page_size": 5},
    )
    results.append(r)

    r, _ = await req_check(
        client,
        "GET",
        f"{base}/agents/{account_name}/stock",
        "get_stock_levels",
    )
    results.append(r)

    return results

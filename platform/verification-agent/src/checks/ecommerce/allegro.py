"""Tier 3 functional checks — Allegro connector.

Exercises all implemented endpoints: accounts, auth status, orders
(list, get, status update, invoices), products (get, search), and
stock sync.  Read-only checks run unconditionally; write operations
use safe test data and accept expected error statuses.
"""

import base64
import logging
from typing import Any

import httpx

from src.checks.common import PDF_STUB, get_check, req_check, result
from src.discovery import VerificationTarget

logger = logging.getLogger(__name__)


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url
    creds = target.credentials or {}
    account = creds.get("account_name", "verification-agent")
    p = {"account_name": account}

    # ── Tier 1 supplement: health, readiness, docs ──

    results.append(await get_check(client, f"{base}/health", "health"))
    results.append(await get_check(client, f"{base}/readiness", "readiness"))
    results.append(await get_check(client, f"{base}/docs", "docs"))

    # ── Accounts ──

    results.append(await get_check(client, f"{base}/accounts", "list_accounts"))

    # ── Auth status ──

    results.append(await get_check(
        client, f"{base}/auth/status", "all_auth_statuses",
    ))
    results.append(await get_check(
        client, f"{base}/auth/{account}/status", "auth_status",
    ))

    # ── Orders ──

    check, resp = await req_check(
        client, "GET", f"{base}/orders", "list_orders",
        params={**p, "page": "1", "page_size": "1"},
        accept_statuses=(200, 401),
    )
    results.append(check)

    order_id = _extract_first_order_id(resp)

    if order_id:
        results.append(await get_check(
            client, f"{base}/orders/{order_id}", "get_order", params=p,
        ))

        results.append(await get_check(
            client, f"{base}/orders/{order_id}/invoices", "get_order_invoices",
            params=p,
        ))
    else:
        results.append(result(
            "get_order", "SKIP", 0,
            error="No order found to test — list may be empty or auth failed",
        ))
        results.append(result(
            "get_order_invoices", "SKIP", 0,
            error="No order found to test",
        ))

    # Order status update — use a nonexistent order to avoid side effects
    status_check, _ = await req_check(
        client, "PUT",
        f"{base}/orders/VERIFICATION_AGENT_TEST_000/status",
        "update_order_status",
        params=p,
        json_body={"status": "SENT"},
        accept_statuses=(200, 401, 404, 422),
    )
    results.append(status_check)

    # Invoice upload — test with stub PDF on nonexistent order
    invoice_check, _ = await req_check(
        client, "POST",
        f"{base}/orders/VERIFICATION_AGENT_TEST_000/invoice",
        "upload_invoice_json",
        params=p,
        json_body={
            "invoice_base64": base64.b64encode(PDF_STUB).decode(),
            "filename": "verification_test.pdf",
            "invoice_number": "FV-TEST/0000",
        },
        accept_statuses=(200, 201, 401, 404, 422),
    )
    results.append(invoice_check)

    # ── Products ──

    check, _ = await req_check(
        client, "GET", f"{base}/products/search", "search_products",
        params={**p, "query": "test", "page": "1", "page_size": "1"},
        accept_statuses=(200, 401),
    )
    results.append(check)

    prod_check, _ = await req_check(
        client, "GET", f"{base}/products/VERIFICATION_AGENT_PROD_000", "get_product_nonexistent",
        params=p,
        accept_statuses=(200, 401, 404),
    )
    results.append(prod_check)

    # ── Stock sync ──

    stock_check, _ = await req_check(
        client, "POST", f"{base}/stock/sync", "sync_stock",
        params=p,
        json_body={"items": []},
        accept_statuses=(200, 401, 422),
    )
    results.append(stock_check)

    return results


def _extract_first_order_id(resp: httpx.Response | None) -> str | None:
    if not resp or resp.status_code != 200:
        return None
    try:
        data = resp.json()
        orders = data.get("orders") or data.get("items") or []
        if orders and isinstance(orders, list):
            return orders[0].get("order_id") or orders[0].get("id")
    except (KeyError, IndexError, ValueError, TypeError):
        pass
    return None

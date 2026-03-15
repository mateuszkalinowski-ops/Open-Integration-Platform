"""Tier 3 functional checks — WooCommerce connector.

Exercises all implemented endpoints across the full WooCommerce REST API v3:
orders, products, customers, coupons, taxes, reports, webhooks, settings,
payment gateways, shipping zones, and system status.

Read-only checks run unconditionally; write operations use safe test data
and accept expected error statuses (401/404/422).
"""

import logging
from typing import Any

import httpx

from src.checks.common import get_check, req_check, result
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

    # ── Tier 1: health, readiness, docs ──

    results.append(await get_check(client, f"{base}/health", "health"))
    results.append(await get_check(client, f"{base}/readiness", "readiness"))
    results.append(await get_check(client, f"{base}/docs", "docs"))

    # ── Accounts ──

    results.append(await get_check(client, f"{base}/accounts", "list_accounts"))

    # ── Auth ──

    results.append(await get_check(client, f"{base}/auth/status", "all_auth_statuses"))
    results.append(await get_check(client, f"{base}/auth/{account}/status", "auth_status"))

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/connection/{account}/status",
        "connection_status",
    )
    results.append(chk)

    # ══ ORDERS ══

    chk, resp = await req_check(
        client,
        "GET",
        f"{base}/orders",
        "list_orders",
        params={**p, "page": 1, "page_size": 5},
        accept_statuses=(200, 401),
    )
    results.append(chk)

    order_id = _extract_first_id(resp, "orders")

    if order_id:
        results.append(
            await get_check(
                client,
                f"{base}/orders/{order_id}",
                "get_order",
                params=p,
            )
        )
        results.append(
            await get_check(
                client,
                f"{base}/orders/{order_id}/notes",
                "list_order_notes",
                params=p,
            )
        )
        results.append(
            await get_check(
                client,
                f"{base}/orders/{order_id}/refunds",
                "list_order_refunds",
                params=p,
            )
        )
    else:
        results.append(result("get_order", "SKIP", 0, error="No orders found"))
        results.append(result("list_order_notes", "SKIP", 0, error="No orders found"))
        results.append(result("list_order_refunds", "SKIP", 0, error="No orders found"))

    chk, _ = await req_check(
        client,
        "PUT",
        f"{base}/orders/99999999/status",
        "update_order_status_dummy",
        json_body={"status": "processing"},
        params=p,
        accept_statuses=(200, 401, 404, 422),
    )
    results.append(chk)

    # ══ PRODUCTS ══

    chk, resp = await req_check(
        client,
        "GET",
        f"{base}/products",
        "list_products",
        params={**p, "page": 1, "per_page": 5},
        accept_statuses=(200, 401),
    )
    results.append(chk)

    product_id = _extract_first_id_from_list(resp)

    if product_id:
        results.append(
            await get_check(
                client,
                f"{base}/products/{product_id}",
                "get_product",
                params=p,
            )
        )
        results.append(
            await get_check(
                client,
                f"{base}/products/{product_id}/variations",
                "list_variations",
                params=p,
            )
        )
    else:
        results.append(result("get_product", "SKIP", 0, error="No products found"))
        results.append(result("list_variations", "SKIP", 0, error="No products found"))

    results.append(
        await get_check(
            client,
            f"{base}/products/search",
            "search_products",
            params={**p, "query": "test"},
        )
    )

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/products/categories",
        "list_product_categories",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/products/tags",
        "list_product_tags",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/products/attributes",
        "list_product_attributes",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/products/reviews",
        "list_product_reviews",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/products/shipping_classes",
        "list_shipping_classes",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ CUSTOMERS ══

    chk, resp = await req_check(
        client,
        "GET",
        f"{base}/customers",
        "list_customers",
        params={**p, "page": 1, "per_page": 5},
        accept_statuses=(200, 401),
    )
    results.append(chk)

    customer_id = _extract_first_id_from_list(resp)
    if customer_id:
        results.append(
            await get_check(
                client,
                f"{base}/customers/{customer_id}",
                "get_customer",
                params=p,
            )
        )
        results.append(
            await get_check(
                client,
                f"{base}/customers/{customer_id}/downloads",
                "list_customer_downloads",
                params=p,
            )
        )
    else:
        results.append(result("get_customer", "SKIP", 0, error="No customers found"))
        results.append(result("list_customer_downloads", "SKIP", 0, error="No customers found"))

    # ══ COUPONS ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/coupons",
        "list_coupons",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ TAX RATES ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/taxes",
        "list_tax_rates",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/taxes/classes",
        "list_tax_classes",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ REPORTS ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/reports",
        "list_reports",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/reports/sales",
        "sales_report",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/reports/top_sellers",
        "top_sellers_report",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/reports/orders/totals",
        "orders_totals",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/reports/products/totals",
        "products_totals",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ WEBHOOKS ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/webhooks",
        "list_webhooks",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ SETTINGS ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/settings",
        "list_settings_groups",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ PAYMENT GATEWAYS ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/payment_gateways",
        "list_payment_gateways",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ SHIPPING ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/shipping/zones",
        "list_shipping_zones",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/shipping_methods",
        "list_shipping_methods",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ SYSTEM STATUS ══

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/system_status",
        "get_system_status",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/system_status/tools",
        "list_system_status_tools",
        params=p,
        accept_statuses=(200, 401),
    )
    results.append(chk)

    # ══ STOCK SYNC ══

    chk, _ = await req_check(
        client,
        "POST",
        f"{base}/stock/sync",
        "stock_sync_dummy",
        json_body={"items": [{"sku": "VERIFICATION_TEST_SKU", "quantity": 0}]},
        params=p,
        accept_statuses=(200, 401, 404, 422),
    )
    results.append(chk)

    return results


def _extract_first_id(resp: httpx.Response | None, list_key: str) -> int | None:
    if not resp or resp.status_code != 200:
        return None
    try:
        data = resp.json()
        if isinstance(data, dict) and list_key in data:
            items = data[list_key]
        elif isinstance(data, list):
            items = data
        else:
            return None
        if items:
            return items[0].get("id") or items[0].get("order_id")
    except (KeyError, IndexError, ValueError, TypeError):
        pass
    return None


def _extract_first_id_from_list(resp: httpx.Response | None) -> int | None:
    if not resp or resp.status_code != 200:
        return None
    try:
        data = resp.json()
        if isinstance(data, list) and data:
            return data[0].get("id")
    except (KeyError, IndexError, ValueError, TypeError):
        pass
    return None

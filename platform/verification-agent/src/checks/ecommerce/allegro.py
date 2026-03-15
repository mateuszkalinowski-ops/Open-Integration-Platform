"""Tier 3 functional checks — Allegro connector."""

from typing import Any

import httpx

from src.checks.common import get_check, req_check, result
from src.discovery import VerificationTarget


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url
    creds = target.credentials or {}
    account = creds.get("account_name", "verification-agent")
    p = {"account_name": account}

    results.append(await get_check(client, f"{base}/health", "health"))
    results.append(await get_check(client, f"{base}/readiness", "readiness"))
    results.append(await get_check(client, f"{base}/docs", "docs_endpoint"))

    results.append(await get_check(client, f"{base}/accounts", "list_accounts"))

    chk, _ = await req_check(
        client,
        "GET",
        f"{base}/auth/{account}/status",
        "auth_status",
        accept_statuses=(200, 401, 404),
    )
    results.append(chk)

    results.append(
        await get_check(
            client,
            f"{base}/orders",
            "list_orders",
            params={**p, "page": 1, "page_size": 5},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/orders/events",
            "order_events",
            params={**p, "limit": 5},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/orders/event-stats",
            "order_event_stats",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/orders/carriers",
            "order_carriers",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/offers",
            "list_offers",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    _, resp_offers = await req_check(
        client,
        "GET",
        f"{base}/offers",
        "list_offers_for_id",
        params={**p, "limit": 1, "offset": 0},
        accept_statuses=(200, 401),
    )
    offer_id = _extract_first_id(resp_offers, "offers", "id")

    if offer_id:
        results.append(
            await get_check(
                client,
                f"{base}/offers/{offer_id}",
                "get_offer",
                params=p,
            )
        )
        results.append(
            await get_check(
                client,
                f"{base}/offers/{offer_id}/rating",
                "offer_rating",
                params=p,
            )
        )
        results.append(
            await get_check(
                client,
                f"{base}/offers/{offer_id}/promo",
                "offer_promo",
                params=p,
            )
        )
    else:
        results.append(result("get_offer", "SKIP", 0, error="No offers found to test"))
        results.append(result("offer_rating", "SKIP", 0, error="No offers found to test"))
        results.append(result("offer_promo", "SKIP", 0, error="No offers found to test"))

    results.append(
        await get_check(
            client,
            f"{base}/offers/events",
            "offer_events",
            params={**p, "limit": 5},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/products/search",
            "search_products",
            params={**p, "query": "test", "page": 1, "page_size": 5},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/categories",
            "list_categories",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/stock/sync",
            "stock_sync_options",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/variants",
            "list_variants",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/tags",
            "list_tags",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/promotions",
            "list_promotions",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/turnover-discounts",
            "list_turnover_discounts",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/bundles",
            "list_bundles",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/payments/history",
            "payment_history",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/payments/refunds",
            "payment_refunds",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/shipments/services",
            "shipment_services",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/returns",
            "list_returns",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/delivery/methods",
            "delivery_methods",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/delivery/settings",
            "delivery_settings",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/delivery/shipping-rates",
            "shipping_rates",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/warranties",
            "list_warranties",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/return-policies",
            "list_return_policies",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/messages/threads",
            "list_message_threads",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/billing/types",
            "billing_types",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/billing/entries",
            "billing_entries",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/user/info",
            "user_info",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/user/ratings",
            "user_ratings",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/user/sales-quality",
            "sales_quality",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/commission-refunds",
            "commission_refunds",
            params={**p, "limit": 5, "offset": 0},
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/additional-services/groups",
            "additional_service_groups",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/additional-services/definitions",
            "additional_service_defs",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/size-tables",
            "list_size_tables",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/points-of-service",
            "list_points_of_service",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/contacts",
            "list_contacts",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/pricing/offer-quotes",
            "pricing_quotes",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/badges/campaigns",
            "badge_campaigns",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/badges",
            "list_badges",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/compatibility/categories",
            "compat_categories",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/fulfillment/stock",
            "fulfillment_stock",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/fulfillment/products",
            "fulfillment_products",
            params=p,
        )
    )

    results.append(
        await get_check(
            client,
            f"{base}/fulfillment/advance-ship-notices",
            "fulfillment_asn_list",
            params=p,
        )
    )

    return results


def _extract_first_id(
    resp: httpx.Response | None,
    list_key: str,
    id_key: str = "id",
) -> str | None:
    if resp is None or resp.status_code != 200:
        return None
    try:
        data = resp.json()
        items = data if isinstance(data, list) else data.get(list_key, [])
        if items:
            return str(items[0].get(id_key, ""))
    except (ValueError, KeyError, TypeError, IndexError):
        pass
    return None

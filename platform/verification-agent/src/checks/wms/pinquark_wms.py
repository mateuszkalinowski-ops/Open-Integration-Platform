"""Tier 3 functional checks — Pinquark WMS connector.

Exercises all documented endpoints: articles, article batches, documents,
positions, contractors, feedback, errors, and poller management.

Read-only checks (GET-style POSTs) run unconditionally; write operations
use safe test data and accept expected error statuses (401/404/422/502).
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

    creds_body: dict[str, Any] = {
        "credentials": {
            "api_url": creds.get("api_url", ""),
            "username": creds.get("username", ""),
            "password": creds.get("password", ""),
        }
    }
    has_creds = bool(creds.get("api_url") and creds.get("username"))

    # ── Tier 1: health, readiness, docs ──

    results.append(await get_check(client, f"{base}/health", "health"))
    results.append(await get_check(client, f"{base}/readiness", "readiness"))
    results.append(await get_check(client, f"{base}/docs", "docs_endpoint"))

    # ── Auth ──

    if has_creds:
        chk, resp = await req_check(
            client, "POST", f"{base}/auth/sign-in", "auth_sign_in",
            json_body=creds_body,
            accept_statuses=(200, 401),
        )
        results.append(chk)
    else:
        results.append(result("auth_sign_in", "SKIP", 0, error="No credentials available"))

    # ── Poller ──

    results.append(await get_check(client, f"{base}/poller/status", "poller_status"))

    # ══ ARTICLES ══

    if has_creds:
        chk, resp = await req_check(
            client, "POST", f"{base}/articles/get", "get_articles",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/articles/get-delete-commands", "get_articles_delete_commands",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/articles/create", "create_article_dummy",
            json_body={
                **creds_body,
                "article": {
                    "erpId": 999999,
                    "name": "VERIFICATION_TEST_ARTICLE",
                    "symbol": "VER_TEST",
                    "source": "ERP",
                },
            },
            accept_statuses=(200, 401, 422, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/articles/delete", "delete_article_dummy",
            json_body={
                **creds_body,
                "command": {"uniqueCode": "VER_TEST_NONEXISTENT"},
            },
            accept_statuses=(200, 401, 404, 422, 502),
        )
        results.append(chk)
    else:
        for name in ("get_articles", "get_articles_delete_commands",
                      "create_article_dummy", "delete_article_dummy"):
            results.append(result(name, "SKIP", 0, error="No credentials available"))

    # ══ ARTICLE BATCHES ══

    if has_creds:
        chk, _ = await req_check(
            client, "POST", f"{base}/article-batches/get", "get_article_batches",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)
    else:
        results.append(result("get_article_batches", "SKIP", 0, error="No credentials available"))

    # ══ DOCUMENTS ══

    if has_creds:
        chk, _ = await req_check(
            client, "POST", f"{base}/documents/get", "get_documents",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/documents/get-delete-commands", "get_documents_delete_commands",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/documents/create", "create_document_dummy",
            json_body={
                **creds_body,
                "document": {
                    "erpId": 999999,
                    "documentType": "PZ",
                    "source": "ERP",
                    "symbol": "VER/TEST/001",
                },
            },
            accept_statuses=(200, 401, 422, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/documents/delete", "delete_document_dummy",
            json_body={
                **creds_body,
                "command": {"uniqueCode": "VER_TEST_NONEXISTENT"},
            },
            accept_statuses=(200, 401, 404, 422, 502),
        )
        results.append(chk)
    else:
        for name in ("get_documents", "get_documents_delete_commands",
                      "create_document_dummy", "delete_document_dummy"):
            results.append(result(name, "SKIP", 0, error="No credentials available"))

    # ══ POSITIONS ══

    if has_creds:
        chk, _ = await req_check(
            client, "POST", f"{base}/positions/get", "get_positions",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/positions/get-delete-commands", "get_positions_delete_commands",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)
    else:
        for name in ("get_positions", "get_positions_delete_commands"):
            results.append(result(name, "SKIP", 0, error="No credentials available"))

    # ══ CONTRACTORS ══

    if has_creds:
        chk, _ = await req_check(
            client, "POST", f"{base}/contractors/get", "get_contractors",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/contractors/get-delete-commands", "get_contractors_delete_commands",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/contractors/create", "create_contractor_dummy",
            json_body={
                **creds_body,
                "contractor": {
                    "erpId": 999999,
                    "name": "VERIFICATION_TEST_CONTRACTOR",
                    "symbol": "VER_TEST",
                    "source": "ERP",
                },
            },
            accept_statuses=(200, 401, 422, 502),
        )
        results.append(chk)
    else:
        for name in ("get_contractors", "get_contractors_delete_commands",
                      "create_contractor_dummy"):
            results.append(result(name, "SKIP", 0, error="No credentials available"))

    # ══ FEEDBACK & ERRORS ══

    if has_creds:
        chk, _ = await req_check(
            client, "POST", f"{base}/feedbacks/get", "get_feedbacks",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)

        chk, _ = await req_check(
            client, "POST", f"{base}/errors/get", "get_errors",
            json_body=creds_body,
            accept_statuses=(200, 401, 502),
        )
        results.append(chk)
    else:
        results.append(result("get_feedbacks", "SKIP", 0, error="No credentials available"))
        results.append(result("get_errors", "SKIP", 0, error="No credentials available"))

    return results

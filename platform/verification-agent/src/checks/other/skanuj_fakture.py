"""Tier 3 functional checks — SkanujFakture connector.

Exercises all endpoints: accounts, companies, entities, documents (list,
simple list, upload v1/v2, file, image, update, delete), attributes
(edit, delete), dictionaries (list, add), and KSeF (xml, qr).
Uploaded test documents are cleaned up after each cycle.
"""

import io
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
    account = (target.credentials or {}).get("account_name", "verification-agent")
    p = {"account_name": account}

    # --- Accounts ---
    results.append(await get_check(client, f"{base}/accounts", "list_accounts"))

    # --- Companies ---
    check, resp = await req_check(
        client, "GET", f"{base}/companies", "list_companies", params=p,
    )
    results.append(check)

    company_id: int | None = None
    if resp and resp.status_code == 200:
        companies = resp.json()
        if isinstance(companies, list) and companies:
            first = companies[0]
            nested = first.get("company", {})
            company_id = (
                nested.get("id")
                or first.get("companyId")
                or first.get("id")
            )

    if not company_id:
        results.append(result(
            "company_resolution", "FAIL", 0,
            error="No company found — cannot test document endpoints",
        ))
        return results

    cid = str(company_id)

    # --- Company entities ---
    results.append(await get_check(
        client, f"{base}/companies/{cid}/entities", "list_company_entities", params=p,
    ))

    # --- Documents list ---
    check, _ = await req_check(
        client, "GET", f"{base}/companies/{cid}/documents", "list_documents", params=p,
    )
    results.append(check)

    # --- Documents list (simple) ---
    results.append(await get_check(
        client, f"{base}/companies/{cid}/documents/simple", "list_documents_simple", params=p,
    ))

    # --- Dictionaries (all types) ---
    for dict_type in ("COST_TYPE", "COST_CENTER", "ATTRIBUTE"):
        dp = {**p, "type": dict_type}
        results.append(await get_check(
            client,
            f"{base}/companies/{cid}/dictionaries",
            f"list_dictionaries_{dict_type}",
            params=dp,
        ))

    # --- CRUD cycle v1: upload → file → image → update → attrs → ksef → delete ---
    results.extend(await _crud_cycle_v1(client, base, cid, p))

    # --- Upload v2 (quick cycle) ---
    results.extend(await _upload_v2_cycle(client, base, cid, p))

    # --- Dictionary add ---
    dict_add_check, _ = await req_check(
        client, "POST", f"{base}/companies/{cid}/dictionaries", "add_dictionary_item",
        params={**p, "type": "ATTRIBUTE"},
        json_body={"items": [{"name": "VerificationAgentTest"}]},
        accept_statuses=(200, 201),
    )
    results.append(dict_add_check)

    return results


async def _crud_cycle_v1(
    client: httpx.AsyncClient,
    base: str,
    cid: str,
    p: dict[str, str],
) -> list[dict[str, Any]]:
    """Upload a document, exercise per-document endpoints, then delete it."""
    results: list[dict[str, Any]] = []

    upload_check, upload_resp = await req_check(
        client, "POST", f"{base}/companies/{cid}/documents", "upload_document",
        params={**p, "single_document": "true", "sale": "false"},
        files={"file": ("verification_test.pdf", io.BytesIO(PDF_STUB), "application/pdf")},
        accept_statuses=(200, 201),
    )
    results.append(upload_check)

    uploaded_doc_id = _extract_doc_id(upload_resp)

    if uploaded_doc_id:
        did = str(uploaded_doc_id)

        results.append(await get_check(
            client, f"{base}/companies/{cid}/documents/{did}/file",
            "get_document_file", params=p,
        ))
        img_check, _ = await req_check(
            client, "GET", f"{base}/companies/{cid}/documents/{did}/image",
            "get_document_image", params=p, accept_statuses=(200, 406),
        )
        results.append(img_check)

        upd, _ = await req_check(
            client, "PUT", f"{base}/companies/{cid}/documents/{did}",
            "update_document", params=p,
            json_body={"data": {"notes": "verification-agent test"}},
        )
        results.append(upd)

        attr_edit, _ = await req_check(
            client, "PUT", f"{base}/companies/{cid}/documents/{did}/attributes",
            "edit_attributes", params=p, json_body={"attributes": []},
        )
        results.append(attr_edit)

        attr_del, _ = await req_check(
            client, "DELETE", f"{base}/companies/{cid}/documents/{did}/attributes",
            "delete_attributes", params=p,
        )
        results.append(attr_del)

        ksef_xml, _ = await req_check(
            client, "GET", f"{base}/companies/{cid}/documents/{did}/ksef-xml",
            "get_ksef_xml", params=p, accept_statuses=(200, 404),
        )
        results.append(ksef_xml)

        ksef_qr, _ = await req_check(
            client, "GET", f"{base}/companies/{cid}/documents/{did}/ksef-qr",
            "get_ksef_qr", params=p, accept_statuses=(200, 404),
        )
        results.append(ksef_qr)

        cleanup, _ = await req_check(
            client, "DELETE", f"{base}/companies/{cid}/documents",
            "delete_documents_cleanup", params=p,
            json_body={"checkDocumentIds": [uploaded_doc_id]},
        )
        results.append(cleanup)
    else:
        for skip_name in (
            "get_document_file", "get_document_image", "update_document",
            "edit_attributes", "delete_attributes", "get_ksef_xml",
            "get_ksef_qr", "delete_documents_cleanup",
        ):
            results.append(result(
                skip_name, "SKIP", 0,
                error="No uploaded document ID — upload may have failed",
            ))

    return results


async def _upload_v2_cycle(
    client: httpx.AsyncClient,
    base: str,
    cid: str,
    p: dict[str, str],
) -> list[dict[str, Any]]:
    """Upload via v2 endpoint and clean up."""
    results: list[dict[str, Any]] = []

    v2_check, v2_resp = await req_check(
        client, "POST", f"{base}/companies/{cid}/documents/v2", "upload_document_v2",
        params={**p, "single_document": "true", "invoice": "PURCHASE"},
        files={"file": ("verification_v2.pdf", io.BytesIO(PDF_STUB), "application/pdf")},
        accept_statuses=(200, 201),
    )
    results.append(v2_check)

    if v2_resp and v2_resp.status_code in (200, 201):
        v2_ids = _extract_doc_ids(v2_resp)
        if v2_ids:
            cleanup, _ = await req_check(
                client, "DELETE", f"{base}/companies/{cid}/documents",
                "delete_v2_cleanup", params=p,
                json_body={"checkDocumentIds": v2_ids},
            )
            results.append(cleanup)

    return results


def _extract_doc_id(resp: httpx.Response | None) -> int | None:
    if not resp or resp.status_code not in (200, 201):
        return None
    try:
        data = resp.json()
        id_list = (
            data.get("documentIdList")
            or data.get("documentsIdList")
            or data.get("documents_id_list")
            or []
        )
        return id_list[0] if id_list else None
    except Exception:
        return None


def _extract_doc_ids(resp: httpx.Response | None) -> list[int]:
    if not resp or resp.status_code not in (200, 201):
        return []
    try:
        data = resp.json()
        return (
            data.get("documentIdList")
            or data.get("documentsIdList")
            or data.get("documents_id_list")
            or []
        )
    except Exception:
        return []

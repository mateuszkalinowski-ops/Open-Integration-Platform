"""FastAPI routes for SkanujFakture integrator."""

import base64
import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

from src.api.dependencies import app_state
from src.config import SkanujFaktureAccountConfig, settings
from src.skanuj_fakture.schemas import (
    AuthStatusResponse,
    ConnectionStatus,
    DictionaryType,
    InvoiceType,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _forward_http_error(exc: httpx.HTTPStatusError) -> HTTPException:
    """Convert an external API HTTP error into an appropriate FastAPI HTTPException."""
    status = exc.response.status_code
    try:
        detail = exc.response.json()
    except Exception:
        detail = exc.response.text[:500] or f"External API returned {status}"
    return HTTPException(status_code=status, detail=detail)


@router.get("/health")
async def health() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        return result.model_dump() if hasattr(result, "model_dump") else result
    return {"status": "healthy"}


@router.get("/readiness")
async def readiness() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        data = result.model_dump() if hasattr(result, "model_dump") else result
        status = result.status if hasattr(result, "status") else data.get("status")
        if status != "healthy":
            raise HTTPException(status_code=503, detail=data)
        return data
    return {"status": "ready"}


# -- Debug / Diagnostics -------------------------------------------------------


@router.get("/debug/poller")
async def debug_poller() -> dict[str, Any]:
    accounts = app_state.account_manager.list_accounts()
    account_info = [
        {"name": a.name, "company_id": a.company_id, "api_url": a.api_url}
        for a in accounts
    ]
    poller_running = app_state.poller is not None and app_state.poller._running
    known_docs: dict[str, int] = {}
    if app_state.state_store:
        for a in accounts:
            ids = await app_state.state_store.load_known_document_ids(a.name)
            known_docs[a.name] = len(ids)
    return {
        "poller_running": poller_running,
        "polling_enabled": settings.polling_enabled,
        "polling_interval_seconds": settings.polling_interval_seconds,
        "polling_status_filter": settings.polling_status_filter,
        "platform_api_url": settings.platform_api_url,
        "platform_event_notify": settings.platform_event_notify,
        "accounts_count": len(accounts),
        "accounts": account_info,
        "known_document_counts": known_docs,
    }


@router.post("/debug/poll-now")
async def debug_poll_now() -> dict[str, Any]:
    """Manually trigger an immediate poll cycle for diagnostics."""
    if not app_state.poller:
        return {"error": "Poller not initialized"}
    accounts = app_state.account_manager.list_accounts()
    if not accounts:
        return {"error": "No accounts configured", "accounts": []}
    try:
        await app_state.poller._poll_all_accounts()
        return {
            "status": "poll_completed",
            "accounts_polled": [a.name for a in accounts],
        }
    except Exception as exc:
        return {"error": str(exc)}


# -- Auth / Connection ---------------------------------------------------------


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str) -> AuthStatusResponse:
    _require_account(account_name)
    return app_state.integration.get_auth_status(account_name)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses() -> list[AuthStatusResponse]:
    accounts = app_state.account_manager.list_accounts()
    return [app_state.integration.get_auth_status(a.name) for a in accounts]


@router.get("/connection/{account_name}/status", response_model=ConnectionStatus)
async def connection_status(account_name: str) -> ConnectionStatus:
    _require_account(account_name)
    return await app_state.integration.get_connection_status(account_name)


# -- Accounts ------------------------------------------------------------------


class AccountCreateRequest(BaseModel):
    name: str
    login: str
    password: str
    api_url: str = "https://skanujfakture.pl:8443/SFApi"
    company_id: int | None = None
    environment: str = "production"
    polling_interval_seconds: int | None = None
    polling_status_filter: str | None = None


@router.get("/accounts")
async def list_accounts() -> list[dict[str, Any]]:
    accounts = app_state.account_manager.list_accounts()
    return [
        {"name": a.name, "environment": a.environment, "api_url": a.api_url}
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    data = {k: v for k, v in req.model_dump().items() if k not in ("polling_interval_seconds", "polling_status_filter") or v is not None}
    account = SkanujFaktureAccountConfig(**{k: v for k, v in data.items() if k not in ("polling_interval_seconds", "polling_status_filter")})
    app_state.account_manager.add_account(account)
    _apply_polling_settings(req)
    return {"status": "created", "name": account.name}


@router.put("/accounts/{account_name}")
async def update_account(account_name: str, req: AccountCreateRequest) -> dict[str, str]:
    app_state.account_manager.remove_account(account_name)
    app_state.integration.reset_client(account_name)
    account = SkanujFaktureAccountConfig(**{k: v for k, v in req.model_dump().items() if k not in ("polling_interval_seconds", "polling_status_filter")})
    app_state.account_manager.add_account(account)
    _apply_polling_settings(req)
    return {"status": "updated", "name": account.name}


def _apply_polling_settings(req: AccountCreateRequest) -> None:
    if req.polling_interval_seconds is not None and req.polling_interval_seconds > 0:
        settings.polling_interval_seconds = req.polling_interval_seconds
        logger.info("Polling interval updated to %ds", req.polling_interval_seconds)
    if req.polling_status_filter is not None:
        settings.polling_status_filter = req.polling_status_filter
        logger.info("Polling status filter updated to '%s'", req.polling_status_filter)


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    app_state.integration.reset_client(account_name)
    return {"status": "removed"}


# -- Companies -----------------------------------------------------------------


@router.get("/companies")
async def list_companies(
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> list[dict[str, Any]]:
    _require_account(account_name)
    try:
        return await app_state.integration.get_companies(account_name)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


@router.get("/companies/{company_id}/entities")
async def list_company_entities(
    company_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> list[dict[str, Any]]:
    _require_account(account_name)
    try:
        return await app_state.integration.get_company_entities(account_name, company_id)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


# -- Documents -----------------------------------------------------------------


@router.post("/companies/{company_id}/documents")
async def upload_document(
    company_id: int,
    file: UploadFile = File(...),
    account_name: str = Query(..., description="SkanujFakture account name"),
    single_document: bool = Query(True, description="True if one file = one invoice"),
    sale: bool = Query(False, description="True for sale invoice, false for purchase"),
) -> dict[str, Any]:
    _require_account(account_name)
    content = await file.read()
    try:
        return await app_state.integration.upload_document(
            account_name, company_id, content, file.filename or "document.pdf",
            single_document=single_document, sale=sale,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


@router.post("/companies/{company_id}/documents/v2")
async def upload_document_v2(
    company_id: int,
    file: UploadFile = File(...),
    account_name: str = Query(..., description="SkanujFakture account name"),
    single_document: bool = Query(True),
    invoice_type: InvoiceType = Query(InvoiceType.PURCHASE, alias="invoice"),
    company_entity_id: int | None = Query(None, description="Required when invoice=OTHER"),
) -> dict[str, Any]:
    _require_account(account_name)
    content = await file.read()
    try:
        return await app_state.integration.upload_document_v2(
            account_name, company_id, content, file.filename or "document.pdf",
            single_document=single_document, invoice_type=invoice_type.value,
            company_entity_id=company_entity_id,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


@router.get("/companies/{company_id}/documents")
async def list_documents(
    company_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
    document_statuses: list[str] | None = Query(None, description="Filter by statuses"),
    is_sale: bool | None = Query(None, description="Filter purchase/sale"),
    check_document_ids: list[int] | None = Query(None, description="Filter by document IDs"),
    contractor: list[str] | None = Query(None, description="Filter by contractor NIP"),
) -> list[dict[str, Any]]:
    _require_account(account_name)
    try:
        return await app_state.integration.get_documents(
            account_name, company_id, document_statuses=document_statuses,
            is_sale=is_sale, check_document_ids=check_document_ids,
            contractor=contractor,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


@router.get("/companies/{company_id}/documents/simple")
async def list_documents_simple(
    company_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
    document_statuses: list[str] | None = Query(None),
) -> list[dict[str, Any]]:
    _require_account(account_name)
    try:
        return await app_state.integration.get_documents_simple(
            account_name, company_id, document_statuses=document_statuses,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


class DocumentUpdateRequest(BaseModel):
    data: dict[str, Any]


@router.put("/companies/{company_id}/documents/{document_id}")
async def update_document(
    company_id: int,
    document_id: int,
    body: DocumentUpdateRequest,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.update_document(
            account_name, company_id, document_id, body.data,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


class DeleteDocumentsRequest(BaseModel):
    check_document_ids: list[int] = Field(default_factory=list, alias="checkDocumentIds")

    model_config = {"populate_by_name": True}


@router.delete("/companies/{company_id}/documents")
async def delete_documents(
    company_id: int,
    body: DeleteDocumentsRequest,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.delete_documents(
            account_name, company_id, check_document_ids=body.check_document_ids,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


@router.get("/companies/{company_id}/documents/{document_id}/file")
async def get_document_file(
    company_id: int,
    document_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, str]:
    _require_account(account_name)
    try:
        file_bytes = await app_state.integration.get_document_file(account_name, company_id, document_id)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)
    return {"content_base64": base64.b64encode(file_bytes).decode(), "document_id": str(document_id)}


@router.get("/companies/{company_id}/documents/{document_id}/image")
async def get_document_image(
    company_id: int,
    document_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, str]:
    _require_account(account_name)
    try:
        image_bytes = await app_state.integration.get_document_image(account_name, company_id, document_id)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)
    return {"content_base64": base64.b64encode(image_bytes).decode(), "document_id": str(document_id)}


# -- Attributes ----------------------------------------------------------------


class AttributeEditRequest(BaseModel):
    status_id: int | None = Field(default=None, alias="statusId")
    attributes: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


@router.put("/companies/{company_id}/documents/{document_id}/attributes")
async def edit_attributes(
    company_id: int,
    document_id: int,
    body: AttributeEditRequest,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.edit_attributes(
            account_name, company_id, document_id, body.attributes, status_id=body.status_id,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


@router.delete("/companies/{company_id}/documents/{document_id}/attributes")
async def delete_attributes(
    company_id: int,
    document_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.delete_attributes(account_name, company_id, document_id)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


# -- Dictionaries (dekretacja) -------------------------------------------------


@router.get("/companies/{company_id}/dictionaries")
async def list_dictionaries(
    company_id: int,
    dict_type: DictionaryType = Query(..., alias="type", description="Dictionary type"),
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> list[dict[str, Any]]:
    _require_account(account_name)
    try:
        return await app_state.integration.get_dictionaries(account_name, company_id, dict_type.value)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


class DictionaryItemsRequest(BaseModel):
    items: list[dict[str, str]]


@router.post("/companies/{company_id}/dictionaries")
async def add_dictionary_items(
    company_id: int,
    body: DictionaryItemsRequest,
    dict_type: DictionaryType = Query(..., alias="type"),
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.add_dictionary_items(
            account_name, company_id, dict_type.value, body.items,
        )
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


# -- KSeF ----------------------------------------------------------------------


@router.get("/companies/{company_id}/documents/{document_id}/ksef-xml")
async def get_ksef_xml(
    company_id: int,
    document_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
    as_json: bool = Query(False, description="Return as JSON instead of XML"),
) -> Any:
    _require_account(account_name)
    try:
        return await app_state.integration.get_ksef_xml(account_name, company_id, document_id, as_json=as_json)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


@router.get("/companies/{company_id}/documents/{document_id}/ksef-qr")
async def get_ksef_qr(
    company_id: int,
    document_id: int,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, str]:
    _require_account(account_name)
    try:
        qr_bytes = await app_state.integration.get_ksef_qr(account_name, company_id, document_id)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)
    return {"content_base64": base64.b64encode(qr_bytes).decode(), "document_id": str(document_id)}


class KsefInvoiceRequest(BaseModel):
    invoice_data: dict[str, Any]


@router.put("/companies/{company_id}/ksef/invoice")
async def send_ksef_invoice(
    company_id: int,
    body: KsefInvoiceRequest,
    account_name: str = Query(..., description="SkanujFakture account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.send_ksef_invoice(account_name, company_id, body.invoice_data)
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc)


# -- Helpers -------------------------------------------------------------------


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )

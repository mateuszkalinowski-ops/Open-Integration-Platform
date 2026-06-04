"""FastAPI routes for KSeF integrator."""

import base64
import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import settings
from src.ksef.schemas import (
    AuthenticateRequest,
    AuthenticateResponse,
    ConnectionStatus,
    OpenSessionApiRequest,
    OpenSessionApiResponse,
    QueryInvoicesApiRequest,
    QueryInvoicesApiResponse,
    SendInvoiceApiRequest,
    SendInvoiceApiResponse,
)
from src.ksef.test_data_generator import generate_test_credentials
from src.ksef.xml_builder import (
    build_invoice_xml,
    build_invoice_xml_from_raw_ksef,
    is_raw_ksef_format,
    validate_invoice_xml,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _forward_http_error(exc: httpx.HTTPStatusError) -> HTTPException:
    status = exc.response.status_code
    try:
        detail = exc.response.json()
    except Exception:
        detail = exc.response.text[:500]
    return HTTPException(status_code=status, detail=detail)


@router.get("/health")
async def health() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        return result.model_dump() if hasattr(result, "model_dump") else result
    return {"status": "healthy", "version": settings.app_version}


@router.get("/readiness")
async def readiness() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        data = result.model_dump() if hasattr(result, "model_dump") else result
        status = result.status if hasattr(result, "status") else data.get("status")
        if status != "healthy":
            raise HTTPException(status_code=503, detail=data)
        return data
    return {"status": "ready", "version": settings.app_version}


# -- Accounts --


class AccountCreateRequest(BaseModel):
    name: str
    nip: str
    ksef_token: str = ""
    environment: str = "demo"
    certificate_path: str = ""
    certificate_password: str = ""


@router.get("/accounts")
async def list_accounts() -> list[dict[str, Any]]:
    accounts = app_state.account_manager.list_accounts()
    return [
        {
            "name": a.name,
            "nip": f"{a.nip[:6]}****",
            "environment": a.environment.value,
            "api_url": a.api_url,
        }
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def create_account(req: AccountCreateRequest) -> dict[str, Any]:
    account = app_state.account_manager.add_account(req.model_dump())
    return {
        "name": account.name,
        "nip": f"{account.nip[:6]}****",
        "environment": account.environment.value,
    }


@router.delete("/accounts/{account_name}")
async def delete_account(account_name: str) -> dict[str, str]:
    app_state.account_manager.remove_account(account_name)
    return {"status": "deleted", "account": account_name}


# -- Authentication --


@router.post("/auth/token")
async def authenticate(req: AuthenticateRequest) -> AuthenticateResponse:
    """Authenticate with KSeF and obtain JWT tokens."""
    try:
        client = app_state.account_manager.get_client(req.account_name)
        session = await client.authenticate()
        return AuthenticateResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            access_valid_until=session.access_valid_until.isoformat(),
            refresh_valid_until=session.refresh_valid_until.isoformat(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{req.account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Authentication failed for account '%s'", req.account_name)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# -- Sessions --


@router.post("/sessions")
async def open_session(req: OpenSessionApiRequest) -> OpenSessionApiResponse:
    """Open an interactive or batch session for invoice sending."""
    try:
        client = app_state.account_manager.get_client(req.account_name)
        result = await client.open_session(
            session_type=req.session_type.value,
        )
        return OpenSessionApiResponse(
            reference_number=result.reference_number,
            status=f"open (valid until {result.valid_until})",
            session_type=req.session_type.value,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{req.account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to open session for '%s'", req.account_name)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sessions/{reference_number}/close")
async def close_session(
    reference_number: str,
    account_name: str = Query(...),
) -> dict[str, Any]:
    """Close an active session."""
    try:
        client = app_state.account_manager.get_client(account_name)
        result = await client.close_session(reference_number=reference_number)
        return {"status": "closed", "reference_number": reference_number, "result": result}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to close session %s", reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{reference_number}")
async def get_session_status(
    reference_number: str,
    account_name: str = Query(...),
) -> dict[str, Any]:
    """Get session status."""
    try:
        client = app_state.account_manager.get_client(account_name)
        result = await client.get_session_status(reference_number=reference_number)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to get session status %s", reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# -- Invoices --


@router.post("/invoices")
async def send_invoice(req: SendInvoiceApiRequest) -> SendInvoiceApiResponse:
    """Encrypt and send an invoice in an active session.

    Provide either invoice_xml (raw FA(3) XML) or invoice_data (structured dict
    that will be converted to XML automatically).

    invoice_data accepts two formats:
    - Simplified: {seller, buyer, items, ...}
    - Raw KSeF: {fa, podmiot1, podmiot2} — native KSeF structure
    """
    try:
        client = app_state.account_manager.get_client(req.account_name)

        if req.invoice_xml:
            xml_bytes = req.invoice_xml.encode("utf-8")
        elif req.invoice_data:
            if is_raw_ksef_format(req.invoice_data):
                xml_bytes = build_invoice_xml_from_raw_ksef(req.invoice_data)
            else:
                account = app_state.account_manager.get_account(req.account_name)
                if account:
                    seller = req.invoice_data.setdefault("seller", {})
                    if "nip" not in seller:
                        seller["nip"] = account.nip
                    if not seller.get("name"):
                        seller["name"] = account.company_name or f"Podmiot NIP {account.nip}"
                xml_bytes = build_invoice_xml(req.invoice_data)
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'invoice_xml' or 'invoice_data'",
            )

        errors = validate_invoice_xml(xml_bytes)
        if errors:
            raise HTTPException(status_code=400, detail={"validation_errors": errors})

        result = await client.send_invoice(
            invoice_xml=xml_bytes,
            reference_number=req.reference_number,
        )
        return SendInvoiceApiResponse(
            reference_number=result.reference_number,
            status="sent",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{req.account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to send invoice")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class BatchInvoicesRequest(BaseModel):
    account_name: str
    reference_number: str
    invoices: list[dict[str, Any]]


@router.post("/invoices/batch")
async def send_invoices_batch(req: BatchInvoicesRequest) -> dict[str, Any]:
    """Send multiple invoices in a batch session."""
    try:
        client = app_state.account_manager.get_client(req.account_name)
        results = []
        send_errors = []

        for idx, inv in enumerate(req.invoices):
            try:
                xml_bytes = build_invoice_xml(inv)
                result = await client.send_invoice(
                    invoice_xml=xml_bytes,
                    reference_number=req.reference_number,
                    session_type="batch",
                )
                results.append(
                    {
                        "index": idx,
                        "reference_number": result.reference_number,
                        "status": "sent",
                    }
                )
            except Exception as inv_exc:
                send_errors.append({"index": idx, "error": str(inv_exc)})

        return {
            "total": len(req.invoices),
            "sent": len(results),
            "failed": len(send_errors),
            "results": results,
            "errors": send_errors,
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{req.account_name}' not found") from exc
    except Exception as exc:
        logger.exception("Batch send failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/invoices/{ksef_reference_number}")
async def get_invoice(
    ksef_reference_number: str,
    account_name: str = Query(...),
) -> dict[str, Any]:
    """Retrieve an invoice by KSeF reference number."""
    try:
        client = app_state.account_manager.get_client(account_name)
        result = await client.get_invoice(ksef_reference_number)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to get invoice %s", ksef_reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/invoices/{ksef_reference_number}/pdf",
    summary="Pobierz fakturę jako PDF",
    description=(
        "Pobiera fakturę XML z KSeF i renderuje ją do PDF w formacie "
        "wizualizacji KSeF (z kodem QR).\n\n"
        "**Przykład:**\n\n"
        "```\n"
        "GET /invoices/6697932376-20260329-56406EC00000-75/pdf?account_name=default\n"
        "```\n\n"
        "```bash\n"
        'curl -o faktura.pdf "http://localhost:8000/invoices/{numer_ksef}/pdf?account_name=default"\n'
        "```"
    ),
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Plik PDF faktury"},
        404: {"description": "Faktura lub konto nie znalezione"},
    },
)
async def get_invoice_pdf(
    ksef_reference_number: str = ...,
    account_name: str = Query(..., description="Nazwa konta KSeF", example="default"),
) -> Response:
    """Pobierz fakturę jako PDF (renderowaną z KSeF XML)."""
    from src.ksef.pdf_renderer import render_invoice_pdf

    try:
        client = app_state.account_manager.get_client(account_name)
        account = app_state.account_manager.get_account(account_name)
        result = await client.get_invoice(ksef_reference_number)
        invoice_xml = result.get("invoice_xml", "")
        if not invoice_xml:
            raise HTTPException(status_code=404, detail="Invoice XML not available")

        pdf_bytes = render_invoice_pdf(
            invoice_xml,
            ksef_number=ksef_reference_number,
            environment=account.environment.value,
        )
        filename = f"faktura_{ksef_reference_number}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to generate PDF for %s", ksef_reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{reference_number}/invoices")
async def get_session_invoices(
    reference_number: str,
    account_name: str = Query(...),
) -> dict[str, Any]:
    """List invoices in a KSeF session."""
    try:
        client = app_state.account_manager.get_client(account_name)
        return await client.get_session_invoices(reference_number=reference_number)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to get session invoices %s", reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{reference_number}/invoices/failed")
async def get_session_failed_invoices(
    reference_number: str,
    account_name: str = Query(...),
) -> dict[str, Any]:
    """List failed invoices in a KSeF session."""
    try:
        client = app_state.account_manager.get_client(account_name)
        return await client.get_session_failed_invoices(reference_number=reference_number)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to get session failed invoices %s", reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{reference_number}/invoices/{invoice_reference_number}")
async def get_invoice_in_session(
    reference_number: str,
    invoice_reference_number: str,
    account_name: str = Query(...),
) -> dict[str, Any]:
    """Get single invoice status within a KSeF session."""
    try:
        client = app_state.account_manager.get_client(account_name)
        return await client.get_invoice_in_session(
            invoice_reference_number=invoice_reference_number,
            session_reference_number=reference_number,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to get invoice %s in session %s", invoice_reference_number, reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/invoices/query")
async def query_invoices(req: QueryInvoicesApiRequest) -> QueryInvoicesApiResponse:
    """Query invoice metadata with filters."""
    try:
        client = app_state.account_manager.get_client(req.account_name)
        result = await client.query_invoices(
            date_from=req.date_from,
            date_to=req.date_to,
            subject_nip=req.subject_nip,
            page_size=req.page_size,
            page_offset=req.page_offset,
            subject_type=req.subject_type,
            date_type=req.date_type,
        )
        return QueryInvoicesApiResponse(
            invoices=[item.model_dump(by_alias=True) for item in result.invoices],
            has_more=result.has_more,
            is_truncated=result.is_truncated,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{req.account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to query invoices")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# -- UPO --


@router.get("/sessions/{reference_number}/upo")
async def get_upo(
    reference_number: str,
    account_name: str = Query(...),
) -> dict[str, Any]:
    """Download UPO (Urzędowe Poświadczenie Odbioru) for a closed session."""
    try:
        client = app_state.account_manager.get_client(account_name)
        upo_bytes = await client.get_upo(reference_number=reference_number)
        upo_b64 = base64.b64encode(upo_bytes).decode("ascii")
        return {
            "reference_number": reference_number,
            "upo_content": upo_b64,
            "content_type": "application/xml",
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except httpx.HTTPStatusError as exc:
        raise _forward_http_error(exc) from exc
    except Exception as exc:
        logger.exception("Failed to get UPO for %s", reference_number)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# -- Connection validation --


@router.post("/generate-test-data")
async def generate_test_data() -> dict[str, Any]:
    """Generate fresh test credentials (NIP + token) on the KSeF TE environment.

    Only works with the test environment (api-test.ksef.mf.gov.pl).
    Disabled in production (requires KSEF_DEBUG=true).
    """
    if settings.default_environment.value == "production" and not settings.debug:
        raise HTTPException(
            status_code=403,
            detail="Test data generation is disabled in production environment",
        )
    try:
        result = await generate_test_credentials()
        return result
    except Exception as exc:
        logger.exception("Failed to generate test data")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/validate-connection")
async def validate_connection(
    account_name: str = Query(...),
) -> ConnectionStatus:
    """Validate KSeF connection by attempting authentication."""
    try:
        client = app_state.account_manager.get_client(account_name)
        account = app_state.account_manager.get_account(account_name)

        ksef_health = await client.check_health()
        if ksef_health["status"] != "healthy":
            return ConnectionStatus(
                status="error",
                environment=account.environment.value,
                nip=f"{account.nip[:6]}****",
                message=f"KSeF API not reachable: {ksef_health.get('error', 'unknown')}",
            )

        await client.authenticate()
        return ConnectionStatus(
            status="connected",
            environment=account.environment.value,
            nip=f"{account.nip[:6]}****",
            message="Authentication successful",
            authenticated=True,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from exc
    except Exception:
        account = app_state.account_manager.get_account(account_name)
        return ConnectionStatus(
            status="error",
            environment=account.environment.value,
            nip=f"{account.nip[:6]}****",
            message="Authentication failed",
        )

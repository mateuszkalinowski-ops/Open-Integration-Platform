"""FastAPI routes for Email Client integrator."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import EmailAccountConfig
from src.email_client.schemas import (
    AuthStatusResponse,
    ConnectionStatus,
    EmailMessage,
    EmailsPage,
    FolderInfo,
    SendEmailRequest,
    SendEmailResponse,
)

router = APIRouter()


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


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str) -> AuthStatusResponse:
    _require_account(account_name)
    return app_state.integration.get_auth_status(account_name)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses() -> list[AuthStatusResponse]:
    accounts = app_state.account_manager.list_accounts()
    return [app_state.integration.get_auth_status(a.name) for a in accounts]


class AccountCreateRequest(BaseModel):
    name: str
    email_address: str
    username: str = ""
    password: str
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    use_ssl: bool = True
    polling_folder: str = "INBOX"
    environment: str = "production"


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [
        {"name": a.name, "environment": a.environment, "email_address": a.email_address}
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = EmailAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return {"status": "removed"}


@router.get("/emails", response_model=EmailsPage)
async def list_emails(
    account_name: str = Query(..., description="Email account name"),
    folder: str = Query("INBOX", description="IMAP folder to fetch from"),
    since: datetime | None = Query(None, description="Fetch emails since this timestamp"),
    max_count: int = Query(50, ge=1, le=200, description="Maximum emails to return"),
    unseen_only: bool = Query(False, description="Only return unread emails"),
) -> EmailsPage:
    _require_account(account_name)
    return await app_state.integration.fetch_emails(
        account_name, folder, since, max_count, unseen_only,
    )


@router.get("/emails/{message_uid}", response_model=EmailMessage)
async def get_email(
    message_uid: str,
    account_name: str = Query(..., description="Email account name"),
    folder: str = Query("INBOX", description="IMAP folder"),
) -> EmailMessage:
    _require_account(account_name)
    email_msg = await app_state.integration.get_email(account_name, message_uid, folder)
    if not email_msg:
        raise HTTPException(status_code=404, detail=f"Email '{message_uid}' not found")
    return email_msg


@router.post("/emails/send", response_model=SendEmailResponse)
async def send_email(
    body: SendEmailRequest,
    account_name: str = Query(..., description="Email account name"),
) -> SendEmailResponse:
    _require_account(account_name)
    return await app_state.integration.send_email(account_name, body)


@router.put("/emails/{message_uid}/read")
async def mark_as_read(
    message_uid: str,
    account_name: str = Query(..., description="Email account name"),
    folder: str = Query("INBOX", description="IMAP folder"),
) -> dict[str, str]:
    _require_account(account_name)
    success = await app_state.integration.mark_as_read(account_name, message_uid, folder)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to mark email as read")
    return {"status": "marked_read", "message_uid": message_uid}


@router.delete("/emails/{message_uid}")
async def delete_email(
    message_uid: str,
    account_name: str = Query(..., description="Email account name"),
    folder: str = Query("INBOX", description="IMAP folder"),
) -> dict[str, str]:
    _require_account(account_name)
    success = await app_state.integration.delete_email(account_name, message_uid, folder)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete email")
    return {"status": "deleted", "message_uid": message_uid}


@router.get("/folders", response_model=list[FolderInfo])
async def list_folders(
    account_name: str = Query(..., description="Email account name"),
) -> list[FolderInfo]:
    _require_account(account_name)
    return await app_state.integration.list_folders(account_name)


@router.get("/connection/{account_name}/status", response_model=ConnectionStatus)
async def connection_status(account_name: str) -> ConnectionStatus:
    _require_account(account_name)
    return await app_state.integration.get_connection_status(account_name)


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )

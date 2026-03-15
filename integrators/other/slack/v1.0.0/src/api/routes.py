"""FastAPI routes for Slack integrator."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import SlackAccountConfig
from src.slack_client.schemas import (
    AddReactionRequest,
    AuthStatusResponse,
    FileUploadRequest,
    FileUploadResponse,
    SendMessageRequest,
    SendMessageResponse,
    SlackChannel,
    SlackMessagesPage,
)

router = APIRouter()


# --- Health ---


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


# --- Auth ---


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str) -> AuthStatusResponse:
    _require_account(account_name)
    return await app_state.integration.get_auth_status(account_name)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses() -> list[AuthStatusResponse]:
    accounts = app_state.account_manager.list_accounts()
    results = []
    for a in accounts:
        results.append(await app_state.integration.get_auth_status(a.name))
    return results


@router.post("/auth/{account_name}/test")
async def test_connection(account_name: str) -> dict[str, Any]:
    _require_account(account_name)
    status = await app_state.integration.get_auth_status(account_name)
    if status.authenticated:
        return {"status": "connected", "team": status.team_name, "bot_user_id": status.bot_user_id}
    raise HTTPException(status_code=502, detail="Connection test failed — check bot_token")


# --- Accounts ---


class AccountCreateRequest(BaseModel):
    name: str
    bot_token: str
    app_token: str = ""
    default_channel: str = "general"
    environment: str = "production"


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [{"name": a.name, "environment": a.environment, "default_channel": a.default_channel} for a in accounts]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = SlackAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return {"status": "removed"}


# --- Channels ---


@router.get("/channels", response_model=list[SlackChannel])
async def list_channels(
    account_name: str = Query(..., description="Slack account name"),
    types: str = Query("public_channel,private_channel", description="Channel types"),
    limit: int = Query(200, ge=1, le=1000),
) -> list[SlackChannel]:
    _require_account(account_name)
    return await app_state.integration.list_channels(account_name, types, limit)


# --- Messages ---


@router.get("/messages", response_model=SlackMessagesPage)
async def get_channel_messages(
    account_name: str = Query(..., description="Slack account name"),
    channel: str = Query(..., description="Channel ID"),
    limit: int = Query(50, ge=1, le=1000),
    oldest: str = Query("", description="Start of time range (ts)"),
    latest: str = Query("", description="End of time range (ts)"),
) -> SlackMessagesPage:
    _require_account(account_name)
    return await app_state.integration.get_channel_history(account_name, channel, limit, oldest, latest)


@router.post("/messages/send", response_model=SendMessageResponse)
async def send_message(
    body: SendMessageRequest,
    account_name: str = Query(..., description="Slack account name"),
) -> SendMessageResponse:
    _require_account(account_name)
    return await app_state.integration.send_message(account_name, body)


# --- Reactions ---


@router.post("/reactions/add")
async def add_reaction(
    body: AddReactionRequest,
    account_name: str = Query(..., description="Slack account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    return await app_state.integration.add_reaction(account_name, body)


# --- Files ---


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    body: FileUploadRequest,
    account_name: str = Query(..., description="Slack account name"),
) -> FileUploadResponse:
    _require_account(account_name)
    return await app_state.integration.upload_file(account_name, body)


# --- Helpers ---


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )

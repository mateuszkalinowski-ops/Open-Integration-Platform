"""FastAPI routes for FTP/SFTP integrator."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import FtpAccountConfig
from src.ftp_client.schemas import (
    ConnectionTestResponse,
    DirectoryCreateRequest,
    DirectoryCreateResponse,
    FileDeleteRequest,
    FileDownloadResponse,
    FileInfo,
    FileMoveRequest,
    FileUploadRequest,
    FileUploadResponse,
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


# --- Auth / Connection Test ---


@router.post("/auth/{account_name}/test", response_model=ConnectionTestResponse)
async def test_connection(account_name: str) -> ConnectionTestResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.test_connection(account_name)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}") from exc


@router.get("/auth/status", response_model=list[dict[str, str]])
async def all_auth_statuses() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    results = []
    for a in accounts:
        try:
            conn = await app_state.integration.test_connection(a.name)
            results.append({"name": a.name, "status": conn.status, "protocol": conn.protocol})
        except Exception:
            results.append({"name": a.name, "status": "disconnected", "protocol": a.protocol})
    return results


# --- Accounts ---


class AccountCreateRequest(BaseModel):
    name: str
    host: str
    protocol: str = "sftp"
    port: int = 0
    username: str = ""
    password: str = ""
    private_key: str = ""
    passive_mode: bool = True
    base_path: str = "/"
    environment: str = "production"


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [
        {
            "name": a.name,
            "host": a.host,
            "protocol": a.protocol,
            "port": str(a.effective_port),
            "environment": a.environment,
        }
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = FtpAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    app_state.integration.remove_client(account_name)
    return {"status": "removed"}


# --- Files ---


@router.get("/files", response_model=list[FileInfo])
async def list_files(
    account_name: str = Query(..., description="FTP/SFTP account name"),
    remote_path: str = Query("/", description="Remote directory path"),
    pattern: str = Query("", description="Glob pattern filter (e.g. *.csv)"),
) -> list[FileInfo]:
    _require_account(account_name)
    return await app_state.integration.list_files(
        account_name,
        remote_path,
        pattern=pattern or None,
    )


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    body: FileUploadRequest,
    account_name: str = Query(..., description="FTP/SFTP account name"),
) -> FileUploadResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.upload_file(account_name, body)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/files/download", response_model=FileDownloadResponse)
async def download_file(
    account_name: str = Query(..., description="FTP/SFTP account name"),
    remote_path: str = Query(..., description="Remote file path to download"),
) -> FileDownloadResponse:
    _require_account(account_name)
    return await app_state.integration.download_file(account_name, remote_path)


@router.delete("/files")
async def delete_file(
    body: FileDeleteRequest,
    account_name: str = Query(..., description="FTP/SFTP account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    return await app_state.integration.delete_file(account_name, body)


@router.post("/files/move")
async def move_file(
    body: FileMoveRequest,
    account_name: str = Query(..., description="FTP/SFTP account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    return await app_state.integration.move_file(account_name, body)


# --- Directories ---


@router.post("/directories", response_model=DirectoryCreateResponse)
async def create_directory(
    body: DirectoryCreateRequest,
    account_name: str = Query(..., description="FTP/SFTP account name"),
) -> DirectoryCreateResponse:
    _require_account(account_name)
    return await app_state.integration.create_directory(account_name, body.remote_path)


@router.get("/directories", response_model=list[FileInfo])
async def list_directories(
    account_name: str = Query(..., description="FTP/SFTP account name"),
    remote_path: str = Query("/", description="Remote directory path"),
) -> list[FileInfo]:
    _require_account(account_name)
    all_entries = await app_state.integration.list_files(account_name, remote_path)
    return [f for f in all_entries if f.is_directory]


# --- Helpers ---


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )

"""FastAPI routes for S3 integrator."""

import binascii
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import S3AccountConfig
from src.s3_client.schemas import (
    BucketCreateRequest,
    BucketCreateResponse,
    BucketInfo,
    ConnectionTestResponse,
    ObjectCopyRequest,
    ObjectCopyResponse,
    ObjectDeleteRequest,
    ObjectDownloadResponse,
    ObjectInfo,
    ObjectUploadRequest,
    ObjectUploadResponse,
    PresignRequest,
    PresignResponse,
)
from src.s3_client.validators import S3ValidationError

_CLIENT_ERRORS = (S3ValidationError, ValueError, binascii.Error)

logger = logging.getLogger(__name__)
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
            logger.error("S3 readiness check failed: %s", data)
            raise HTTPException(status_code=503, detail="Service unavailable")
        return data
    return {"status": "ready"}


# --- Auth / Connection Test ---


@router.get("/auth/{account_name}/test", response_model=ConnectionTestResponse)
@router.post("/auth/{account_name}/test", response_model=ConnectionTestResponse)
async def test_connection(account_name: str) -> ConnectionTestResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.test_connection(account_name)
    except Exception as exc:
        logger.exception("S3 connection test failed")
        raise HTTPException(status_code=502, detail="Connection test failed") from exc


@router.get("/auth/status", response_model=list[dict[str, str]])
async def all_auth_statuses() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    results = []
    for a in accounts:
        try:
            conn = await app_state.integration.test_connection(a.name)
            results.append(
                {
                    "name": a.name,
                    "status": conn.status,
                    "region": conn.region,
                }
            )
        except Exception:
            results.append(
                {
                    "name": a.name,
                    "status": "disconnected",
                    "region": a.region,
                }
            )
    return results


# --- Accounts ---


class AccountCreateRequest(BaseModel):
    name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region: str = "us-east-1"
    endpoint_url: str = ""
    default_bucket: str = ""
    use_path_style: bool = False
    environment: str = "production"
    polling_enabled: bool | None = None
    polling_bucket: str = ""
    polling_prefix: str = ""
    polling_interval_seconds: int | None = None


def _normalize_account(data: dict) -> dict:
    url = data.get("endpoint_url", "")
    if url and not url.startswith(("http://", "https://")):
        data["endpoint_url"] = f"https://{url}"
    return data


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [
        {
            "name": a.name,
            "region": a.region,
            "endpoint": a.endpoint_url or "aws",
            "default_bucket": a.default_bucket,
            "environment": a.environment,
        }
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = S3AccountConfig(**_normalize_account(req.model_dump()))
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.put("/accounts/{account_name}")
async def update_account(account_name: str, req: AccountCreateRequest) -> dict[str, str]:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    app_state.integration.remove_client(account_name)
    app_state.account_manager.remove_account(account_name)
    data = req.model_dump()
    data["name"] = account_name
    account = S3AccountConfig(**_normalize_account(data))
    app_state.account_manager.add_account(account)
    return {"status": "updated", "name": account_name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    app_state.integration.remove_client(account_name)
    return {"status": "removed"}


# --- Objects ---


@router.get("/objects", response_model=list[ObjectInfo])
async def list_objects(
    account_name: str = Query(..., description="S3 account name"),
    bucket: str = Query("", description="Bucket name (uses default if empty)"),
    prefix: str = Query("", description="Key prefix filter"),
    max_keys: int = Query(1000, description="Max objects to return", ge=1, le=10000),
) -> list[ObjectInfo]:
    _require_account(account_name)
    try:
        return await app_state.integration.list_objects(
            account_name,
            bucket,
            prefix=prefix,
            max_keys=max_keys,
        )
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 list_objects failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


@router.post("/objects/upload", response_model=ObjectUploadResponse)
async def upload_object(
    body: ObjectUploadRequest,
    account_name: str = Query(..., description="S3 account name"),
) -> ObjectUploadResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.upload_object(account_name, body)
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 upload_object failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


@router.get("/objects/download", response_model=ObjectDownloadResponse)
async def download_object(
    account_name: str = Query(..., description="S3 account name"),
    bucket: str = Query("", description="Bucket name"),
    key: str = Query(..., description="Object key to download"),
) -> ObjectDownloadResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.download_object(account_name, bucket, key)
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 download_object failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


@router.delete("/objects")
async def delete_object(
    body: ObjectDeleteRequest,
    account_name: str = Query(..., description="S3 account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.delete_object(account_name, body)
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 delete_object failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


@router.post("/objects/copy", response_model=ObjectCopyResponse)
async def copy_object(
    body: ObjectCopyRequest,
    account_name: str = Query(..., description="S3 account name"),
) -> ObjectCopyResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.copy_object(account_name, body)
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 copy_object failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


@router.post("/objects/presign", response_model=PresignResponse)
async def generate_presigned_url(
    body: PresignRequest,
    account_name: str = Query(..., description="S3 account name"),
) -> PresignResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.generate_presigned_url(account_name, body)
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 generate_presigned_url failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


# --- Buckets ---


@router.get("/buckets", response_model=list[BucketInfo])
async def list_buckets(
    account_name: str = Query(..., description="S3 account name"),
) -> list[BucketInfo]:
    _require_account(account_name)
    return await app_state.integration.list_buckets(account_name)


@router.post("/buckets", response_model=BucketCreateResponse)
async def create_bucket(
    body: BucketCreateRequest,
    account_name: str = Query(..., description="S3 account name"),
) -> BucketCreateResponse:
    _require_account(account_name)
    try:
        return await app_state.integration.create_bucket(
            account_name,
            body.bucket,
            region=body.region,
        )
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 create_bucket failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


@router.delete("/buckets/{bucket}")
async def delete_bucket(
    bucket: str,
    account_name: str = Query(..., description="S3 account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    try:
        return await app_state.integration.delete_bucket(account_name, bucket)
    except _CLIENT_ERRORS as exc:
        logger.exception("S3 delete_bucket failed")
        raise HTTPException(status_code=400, detail="Request failed") from exc


# --- Helpers ---


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )

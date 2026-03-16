"""Authentication and tenant context middleware.

Supports API key authentication (pk_live_xxx / pk_test_xxx) and
credential token authentication (ctok_xxx) for public-facing endpoints
like workflow /call.

Sets PostgreSQL session variable ``app.current_tenant_id`` so that
Row Level Security policies enforce tenant isolation at the DB level.
"""

import hashlib
import uuid

from db.base import get_db
from db.models import ApiKey, CredentialToken, Tenant
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def _set_rls_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def _resolve_tenant(api_key: str | None, db: AsyncSession) -> Tenant:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    key_hash = hash_api_key(api_key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True)).options())
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == api_key_record.tenant_id, Tenant.is_active.is_(True))
    )
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=403, detail="Tenant is disabled")

    await _set_rls_tenant(db, tenant.id)
    return tenant


async def _resolve_tenant_by_token(token: str, db: AsyncSession) -> Tenant:
    result = await db.execute(
        select(CredentialToken).where(
            CredentialToken.token == token,
            CredentialToken.is_active.is_(True),
        )
    )
    token_row = result.scalar_one_or_none()
    if not token_row:
        raise HTTPException(status_code=401, detail="Invalid or inactive credential token")

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == token_row.tenant_id, Tenant.is_active.is_(True)))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=403, detail="Tenant is disabled")

    await _set_rls_tenant(db, tenant.id)
    return tenant


async def get_current_tenant(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Standard auth — reads API key from X-API-Key header only."""
    return await _resolve_tenant(api_key, db)


async def get_current_tenant_or_query(
    request: Request,
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Auth via X-API-Key header only (query param removed for security)."""
    return await _resolve_tenant(api_key, db)


async def get_current_tenant_or_token(
    request: Request,
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Auth via X-API-Key header or credential token.

    Priority: X-API-Key header > X-Credential-Token header.
    Designed for public-facing endpoints like workflow /call where the
    caller may only have a credential token, not a full API key.
    """
    if api_key:
        return await _resolve_tenant(api_key, db)

    token = request.headers.get("X-Credential-Token", "").strip()

    if token:
        return await _resolve_tenant_by_token(token, db)

    raise HTTPException(
        status_code=401,
        detail="Provide X-API-Key header or X-Credential-Token header",
    )


def generate_api_key(prefix: str = "pk_live") -> tuple[str, str]:
    raw_key = f"{prefix}_{uuid.uuid4().hex}"
    return raw_key, hash_api_key(raw_key)

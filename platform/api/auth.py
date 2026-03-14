"""Authentication and tenant context middleware.

Supports API key authentication (pk_live_xxx / pk_test_xxx).
Sets PostgreSQL session variable ``app.current_tenant_id`` so that
Row Level Security policies enforce tenant isolation at the DB level.
"""

import hashlib
import uuid

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import get_db
from db.models import ApiKey, Tenant

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def _resolve_tenant(api_key: str | None, db: AsyncSession) -> Tenant:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        .options()
    )
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == api_key_record.tenant_id, Tenant.is_active.is_(True))
    )
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=403, detail="Tenant is disabled")

    tid_str = str(tenant.id)
    safe_tid = tid_str.replace("'", "''")
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{safe_tid}'"))

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


def generate_api_key(prefix: str = "pk_live") -> tuple[str, str]:
    raw_key = f"{prefix}_{uuid.uuid4().hex}"
    return raw_key, hash_api_key(raw_key)

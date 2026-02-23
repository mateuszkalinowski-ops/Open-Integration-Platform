"""Authentication and tenant context middleware.

Supports API key authentication (pk_live_xxx / pk_test_xxx).
"""

import hashlib
import uuid

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import get_db
from db.models import ApiKey, Tenant

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def get_current_tenant(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
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

    return tenant


def generate_api_key(prefix: str = "pk_live") -> tuple[str, str]:
    raw_key = f"{prefix}_{uuid.uuid4().hex}"
    return raw_key, hash_api_key(raw_key)

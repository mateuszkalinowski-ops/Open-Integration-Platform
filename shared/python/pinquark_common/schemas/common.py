from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    name: str
    status: str = "ok"
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    uptime_seconds: float
    checks: dict[str, str] = Field(default_factory=dict)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PaginatedResponse(BaseModel):
    items: list[Any]
    page: int
    page_size: int
    total: int
    has_next: bool


class SyncStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SyncResult(BaseModel):
    status: SyncStatus
    total: int
    succeeded: int
    failed: int
    errors: list[dict[str, Any]] = Field(default_factory=list)
    synced_at: datetime = Field(default_factory=datetime.utcnow)

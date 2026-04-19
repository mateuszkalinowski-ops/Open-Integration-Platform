"""Pydantic schemas for COARRI (Container Discharge/Loading Report) messages."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.common import FunctionCode, Location, Transport


class DamageReport(BaseModel):
    code: str = ""
    description: str = ""
    location_on_container: str | None = None


class CoarriContainer(BaseModel):
    container_no: str
    status: Literal["completed", "shortage", "damaged", "rejected"] = "completed"
    actual_position: Location | None = None
    seal_no: str | None = None
    weight_kg: float | None = None
    damages: list[DamageReport] = Field(default_factory=list)


class CoarriMessage(BaseModel):
    document_id: str
    function_code: FunctionCode = FunctionCode.ORIGINAL
    operation_type: Literal["discharge", "loading"] = "discharge"
    transport: Transport | None = None
    completion_time: datetime | None = None
    containers: list[CoarriContainer] = Field(default_factory=list)


class CoarriResponse(BaseModel):
    id: str
    document_id: str
    function_code: str
    operation_type: str = "discharge"
    containers_count: int = 0
    status: str = "received"
    created_at: datetime | None = None

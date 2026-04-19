"""Pydantic schemas for COHAOR (Container Special Handling Order) messages."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.common import FreeText, FunctionCode, Location


class CohaorMessage(BaseModel):
    document_id: str
    function_code: FunctionCode = FunctionCode.ORIGINAL
    operation_code: Literal["load", "discharge", "shift", "inspection", "weighing", "reefer_check"] = "load"
    container_no: str = ""
    location_from: Location | None = None
    location_to: Location | None = None
    requested_time: datetime | None = None
    priority: int = Field(default=5, ge=1, le=10)
    special_instructions: list[FreeText] = Field(default_factory=list)


class CohaorResponse(BaseModel):
    id: str
    document_id: str
    function_code: str
    operation_code: str = "load"
    container_no: str = ""
    status: str = "received"
    created_at: datetime | None = None

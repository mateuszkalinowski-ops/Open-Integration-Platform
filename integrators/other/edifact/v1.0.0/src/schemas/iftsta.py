"""Pydantic schemas for IFTSTA (Multimodal Status Report) messages."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.common import FreeText, FunctionCode, Location, Reference, Transport


class IftstaMessage(BaseModel):
    document_id: str
    function_code: FunctionCode = FunctionCode.ORIGINAL
    status_code: str = Field(default="", description="SMDG status code (e.g. GTI, GTO, DIS, LOA)")
    status_time: datetime | None = None
    container_no: str | None = None
    transport: Transport | None = None
    location: Location | None = None
    references: list[Reference] = Field(default_factory=list)
    free_text: list[FreeText] = Field(default_factory=list)
    tos_status: str | None = Field(
        default=None,
        description="TOS event_type (auto-mapped to SMDG code if status_code empty)",
    )


class IftstaResponse(BaseModel):
    id: str
    document_id: str
    status_code: str = ""
    container_no: str | None = None
    status: str = "sent"
    created_at: datetime | None = None

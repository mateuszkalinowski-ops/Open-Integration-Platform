"""Pydantic schemas for APERAK (Application Error and Acknowledgement) messages."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AperakError(BaseModel):
    error_code: str = ""
    segment_position: int | None = None
    free_text: str = ""


class AperakMessage(BaseModel):
    document_id: str = ""
    referenced_message_ref: str = ""
    referenced_interchange_ref: str = ""
    response_type: Literal["accepted", "rejected", "accepted_with_errors"] = "accepted"
    errors: list[AperakError] = Field(default_factory=list)


class AperakResponse(BaseModel):
    id: str
    document_id: str
    response_type: str = "accepted"
    referenced_message_ref: str = ""
    content_base64: str = ""
    status: str = "sent"
    created_at: datetime | None = None

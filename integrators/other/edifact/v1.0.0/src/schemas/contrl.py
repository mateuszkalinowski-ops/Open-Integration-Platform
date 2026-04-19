"""Pydantic schemas for CONTRL (Syntax Acknowledgement) messages."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ContrlError(BaseModel):
    message_ref: str = ""
    action_code: str = ""
    status: str = ""


class ContrlMessage(BaseModel):
    referenced_interchange_ref: str = ""
    sender_id: str = ""
    receiver_id: str = ""
    syntax_status: Literal["ok", "error"] = "ok"
    errors: list[ContrlError] = Field(default_factory=list)


class ContrlResponse(BaseModel):
    id: str
    syntax_status: str = "ok"
    referenced_interchange_ref: str = ""
    content_base64: str = ""
    status: str = "sent"
    created_at: datetime | None = None

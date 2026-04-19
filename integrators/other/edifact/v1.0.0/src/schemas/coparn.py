"""Pydantic schemas for COPARN (Container Release/Reservation Order) messages."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.common import FunctionCode, Location, Party, Reference


class CoparnMessage(BaseModel):
    document_id: str
    function_code: FunctionCode = FunctionCode.ORIGINAL
    operation_type: Literal["release", "reservation", "drop_off", "pick_up"] = "release"
    container_no: str | None = None
    iso_size_type: str = ""
    is_empty: bool = True
    booking_ref: str | None = None
    bl_ref: str | None = None
    pickup_window_from: datetime | None = None
    pickup_window_to: datetime | None = None
    haulier: Party | None = None
    carrier: Party | None = None
    truck_plate: str | None = None
    driver_name: str | None = None
    pol: Location | None = None
    pod: Location | None = None
    references: list[Reference] = Field(default_factory=list)


class CoparnResponse(BaseModel):
    id: str
    document_id: str
    function_code: str
    operation_type: str = "release"
    container_no: str | None = None
    status: str = "received"
    created_at: datetime | None = None

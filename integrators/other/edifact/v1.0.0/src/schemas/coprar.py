"""Pydantic schemas for COPRAR (Container Pre-Advice) messages."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.common import DangerousGoods, FunctionCode, Location, Party


class ContainerOnWagon(BaseModel):
    container_no: str = Field(..., description="ISO 6346 container number")
    iso_size_type: str = Field(default="", description="ISO size/type code (e.g. 22G1, 45G1)")
    seal_no: str | None = None
    weight_kg: float = 0.0
    is_empty: bool = True
    dangerous_goods: list[DangerousGoods] = Field(default_factory=list)
    booking_ref: str | None = None
    bl_ref: str | None = None
    shipper: Party | None = None
    consignee: Party | None = None
    pol: Location | None = None
    pod: Location | None = None


class WagonGroup(BaseModel):
    wagon_no: str
    wagon_type: str | None = None
    sequence_no: int = 1
    containers: list[ContainerOnWagon] = Field(default_factory=list)


class CoprarMessage(BaseModel):
    document_id: str
    function_code: FunctionCode = FunctionCode.ORIGINAL
    train_no: str = ""
    eta: datetime | None = None
    etd: datetime | None = None
    carrier: Party | None = None
    pol: Location | None = None
    pod: Location | None = None
    wagons: list[WagonGroup] = Field(default_factory=list)
    booking_ref: str | None = None


class CoprarResponse(BaseModel):
    id: str
    document_id: str
    function_code: str
    train_no: str = ""
    wagons_count: int = 0
    containers_count: int = 0
    status: str = "received"
    created_at: datetime | None = None


class CoprarFilter(BaseModel):
    account_name: str | None = None
    train_no: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    function_code: FunctionCode | None = None

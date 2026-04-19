"""CODECO — Container Gate-in/Gate-out Report (UN/EDIFACT D.95B+)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.schemas.common import (
    DangerousGoods,
    DateTimePeriod,
    Dimensions,
    Equipment,
    FreeText,
    FunctionCode,
    Location,
    Party,
    Reference,
    Seal,
    Transport,
    Weight,
)


class GateEventType(str, Enum):
    """Type of container gate event."""

    GATE_IN = "gate_in"
    GATE_OUT = "gate_out"
    INTERNAL_MOVE = "internal_move"
    STATUS_CHANGE = "status_change"
    REDELIVERY = "redelivery"
    OFF_HIRE = "off_hire"


class ContainerMovement(BaseModel):
    """Single container within a CODECO message (EQD segment group)."""

    equipment: Equipment
    transport: Transport | None = None
    locations: list[Location] = Field(default_factory=list)
    seals: list[Seal] = Field(default_factory=list)
    weights: list[Weight] = Field(default_factory=list)
    dimensions: Dimensions | None = None
    dangerous_goods: list[DangerousGoods] = Field(default_factory=list)
    parties: list[Party] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    timestamps: list[DateTimePeriod] = Field(default_factory=list)
    remarks: list[FreeText] = Field(default_factory=list)
    attached_equipment: list[Equipment] = Field(default_factory=list)


class GateEvent(BaseModel):
    """Full CODECO message — gate-in/out report or status change."""

    document_id: str = Field(description="BGM document/message number")
    event_type: GateEventType
    function_code: FunctionCode = FunctionCode.ORIGINAL
    event_timestamp: datetime
    transport: Transport = Field(description="Main transport (TDT): vessel/truck/train")
    locations: list[Location] = Field(default_factory=list, description="Terminal, port, depot")
    parties: list[Party] = Field(default_factory=list, description="Carrier, haulier, agent")
    references: list[Reference] = Field(default_factory=list, description="Booking, B/L, voyage refs")
    containers: list[ContainerMovement] = Field(min_length=1)
    free_text: list[FreeText] = Field(default_factory=list)
    account_name: str = ""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_id": "CODECO-2026-0001",
                    "event_type": "gate_in",
                    "function_code": "original",
                    "event_timestamp": "2026-04-15T08:30:00Z",
                    "transport": {
                        "mode": "road",
                        "carrier": "TRUCKING-CO",
                        "conveyance_id": "WGM12345",
                    },
                    "locations": [{"qualifier": "terminal", "un_locode": "PLGDY", "name": "BCT Gdynia"}],
                    "containers": [
                        {
                            "equipment": {
                                "container_id": "MSKU1234567",
                                "iso_size_type": "22G1",
                                "full_empty": "full",
                            },
                            "weights": [{"value": 28500.0, "unit": "KGM", "qualifier": "VGM"}],
                            "seals": [{"number": "SL-001", "type": "carrier"}],
                        }
                    ],
                }
            ]
        }
    }


class GateEventResponse(BaseModel):
    """Response after creating/updating a gate event."""

    event_id: str
    document_id: str
    status: str
    message: str = ""
    created_at: datetime | None = None


class GateEventFilter(BaseModel):
    """Query parameters for listing gate events."""

    event_type: GateEventType | None = None
    container_id: str | None = None
    vessel_name: str | None = None
    un_locode: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)

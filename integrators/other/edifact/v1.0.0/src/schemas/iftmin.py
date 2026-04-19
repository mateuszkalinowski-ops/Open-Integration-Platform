"""IFTMIN — Instruction Message / Transport Booking (UN/EDIFACT D.10B+)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.schemas.common import (
    DangerousGoods,
    Equipment,
    FreeText,
    Location,
    Party,
    Reference,
    TransportMode,
    Weight,
)


class InstructionFunction(str, Enum):
    ORIGINAL = "original"
    AMENDMENT = "amendment"
    CANCELLATION = "cancellation"
    CONFIRMATION = "confirmation"


class DeliveryTerms(str, Enum):
    """Common Incoterms used in transport instructions."""

    CIF = "CIF"
    FOB = "FOB"
    CFR = "CFR"
    EXW = "EXW"
    FCA = "FCA"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"
    CPT = "CPT"
    CIP = "CIP"


class TransportStage(BaseModel):
    """Single transport leg / stage within an IFTMIN (TDT segment group)."""

    stage_number: int = Field(ge=1)
    mode: TransportMode
    carrier: str = ""
    conveyance: str = ""
    vessel_name: str = ""
    vessel_imo: str = ""
    voyage_number: str = ""
    departure_location: Location | None = None
    arrival_location: Location | None = None
    departure_date: datetime | None = None
    arrival_date: datetime | None = None


class GoodsLine(BaseModel):
    """Single goods item within an IFTMIN (GID segment group)."""

    line_number: int = Field(ge=1)
    description: str = ""
    packages_count: int = Field(0, ge=0)
    package_type: str = ""
    gross_weight: Weight | None = None
    net_weight: Weight | None = None
    volume: float | None = Field(None, ge=0, description="Volume in m3")
    equipment: Equipment | None = None
    dangerous_goods: list[DangerousGoods] = Field(default_factory=list)
    marks_and_numbers: str = ""
    handling_instructions: list[str] = Field(default_factory=list)
    hs_code: str = Field("", description="Harmonized System commodity code")


class InstructionParties(BaseModel):
    """Named parties for transport instruction (NAD segments with roles)."""

    shipper: Party | None = None
    consignee: Party | None = None
    forwarder: Party | None = None
    notify: Party | None = None
    carrier: Party | None = None
    additional: list[Party] = Field(default_factory=list)


class InstructionLocations(BaseModel):
    """Key locations for the transport instruction (LOC segments)."""

    place_of_receipt: Location | None = None
    port_of_loading: Location | None = None
    port_of_discharge: Location | None = None
    place_of_delivery: Location | None = None
    additional: list[Location] = Field(default_factory=list)


class TransportInstruction(BaseModel):
    """Full IFTMIN message — forwarding/transport instruction."""

    instruction_id: str = Field(description="BGM instruction identifier")
    function_code: InstructionFunction = InstructionFunction.ORIGINAL
    issue_date: datetime | None = None
    parties: InstructionParties = Field(default_factory=InstructionParties)
    locations: InstructionLocations = Field(default_factory=InstructionLocations)
    transport_stages: list[TransportStage] = Field(default_factory=list)
    goods_lines: list[GoodsLine] = Field(default_factory=list, min_length=1)
    delivery_terms: DeliveryTerms | None = None
    delivery_terms_location: Location | None = None
    references: list[Reference] = Field(default_factory=list)
    free_text: list[FreeText] = Field(default_factory=list)
    total_packages: int | None = None
    total_gross_weight: Weight | None = None
    account_name: str = ""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "instruction_id": "IFTMIN-2026-0001",
                    "function_code": "original",
                    "issue_date": "2026-04-15T10:00:00Z",
                    "parties": {
                        "shipper": {"role": "shipper", "name": "ABC Export Ltd", "identifier": "PL1234567890"},
                        "consignee": {"role": "consignee", "name": "XYZ Import GmbH", "identifier": "DE987654321"},
                    },
                    "locations": {
                        "port_of_loading": {"qualifier": "place_of_loading", "un_locode": "PLGDY"},
                        "port_of_discharge": {"qualifier": "place_of_discharge", "un_locode": "DEHAM"},
                    },
                    "transport_stages": [
                        {
                            "stage_number": 1,
                            "mode": "sea",
                            "carrier": "MAEU",
                            "vessel_name": "MAERSK EDINBURGH",
                            "voyage_number": "426E",
                        }
                    ],
                    "goods_lines": [
                        {
                            "line_number": 1,
                            "description": "Industrial machinery parts",
                            "packages_count": 120,
                            "package_type": "CT",
                            "gross_weight": {"value": 24000.0, "unit": "KGM", "qualifier": "G"},
                            "equipment": {
                                "container_id": "MSKU1234567",
                                "iso_size_type": "22G1",
                                "full_empty": "full",
                            },
                        }
                    ],
                    "delivery_terms": "FOB",
                }
            ]
        }
    }


class TransportInstructionResponse(BaseModel):
    """Response after creating/updating a transport instruction."""

    instruction_id: str
    status: str
    message: str = ""
    created_at: datetime | None = None


class TransportInstructionFilter(BaseModel):
    """Query parameters for listing transport instructions."""

    shipper_id: str | None = None
    consignee_id: str | None = None
    port_of_loading: str | None = None
    port_of_discharge: str | None = None
    vessel_name: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    function_code: InstructionFunction | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)

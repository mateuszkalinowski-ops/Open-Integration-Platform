"""BAPLIE — Bay Plan / Stowage Plan (UN/EDIFACT D.13B+)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.schemas.common import (
    DangerousGoods,
    Equipment,
    FreeText,
    FunctionCode,
    Location,
    Party,
    ReeferSettings,
    Reference,
    Transport,
    Weight,
)


class PlanType(str, Enum):
    PROVISIONAL = "provisional"
    FINAL = "final"
    ACTUAL = "actual"


class StowedEquipment(BaseModel):
    """Container/equipment placed at a stowage location (EQD segment group)."""

    equipment: Equipment
    weight: Weight | None = None
    reefer_settings: ReeferSettings | None = None
    dangerous_goods: list[DangerousGoods] = Field(default_factory=list)
    port_of_loading: Location | None = None
    port_of_discharge: Location | None = None
    final_destination: Location | None = None
    references: list[Reference] = Field(default_factory=list)
    parties: list[Party] = Field(default_factory=list)
    over_dimensional: bool = False


class StowageLocation(BaseModel):
    """Single stowage position on the vessel (LOC segment group)."""

    bay: str = Field(description="Bay number e.g. 01, 02")
    row: str = Field(description="Row number e.g. 01, 02")
    tier: str = Field(description="Tier number e.g. 02, 82")
    position_code: str = Field("", description="Full position code e.g. 010282")
    cell_type: str = Field("standard", description="standard, reefer_plug, hatch_cover")
    equipment: StowedEquipment | None = None
    is_empty: bool = True


class BayPlan(BaseModel):
    """Full BAPLIE message — vessel bay plan / stowage plan."""

    document_id: str = Field(description="BGM document number")
    function_code: FunctionCode = FunctionCode.ORIGINAL
    plan_type: PlanType = PlanType.PROVISIONAL
    vessel: Transport = Field(description="Vessel transport details (TDT)")
    voyage_ref: str = ""
    preparation_date: datetime | None = None
    ports_of_call: list[Location] = Field(default_factory=list)
    locations: list[StowageLocation] = Field(default_factory=list)
    parties: list[Party] = Field(default_factory=list, description="Liner, agent, planner")
    references: list[Reference] = Field(default_factory=list)
    free_text: list[FreeText] = Field(default_factory=list)
    total_containers: int | None = None
    account_name: str = ""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_id": "BAPLIE-2026-0001",
                    "function_code": "original",
                    "plan_type": "provisional",
                    "vessel": {
                        "mode": "sea",
                        "carrier": "MAEU",
                        "vessel_name": "MAERSK EDINBURGH",
                        "vessel_imo": "9458100",
                        "voyage_number": "426E",
                    },
                    "ports_of_call": [{"qualifier": "port", "un_locode": "PLGDY", "name": "Gdynia"}],
                    "locations": [
                        {
                            "bay": "01",
                            "row": "02",
                            "tier": "82",
                            "position_code": "010282",
                            "is_empty": False,
                            "equipment": {
                                "equipment": {
                                    "container_id": "MSKU1234567",
                                    "iso_size_type": "22G1",
                                    "full_empty": "full",
                                },
                                "weight": {"value": 28500.0, "unit": "KGM", "qualifier": "G"},
                                "port_of_loading": {"qualifier": "port", "un_locode": "DEHAM"},
                                "port_of_discharge": {"qualifier": "port", "un_locode": "PLGDY"},
                            },
                        }
                    ],
                }
            ]
        }
    }


class BayPlanResponse(BaseModel):
    """Response after creating/updating a bay plan."""

    plan_id: str
    document_id: str
    status: str
    message: str = ""
    total_locations: int = 0
    created_at: datetime | None = None


class BayPlanFilter(BaseModel):
    """Query parameters for listing bay plans."""

    vessel_imo: str | None = None
    vessel_name: str | None = None
    voyage_number: str | None = None
    plan_type: PlanType | None = None
    port_un_locode: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)

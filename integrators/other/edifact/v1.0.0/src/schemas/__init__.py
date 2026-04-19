"""Pydantic v2 schemas for all EDIFACT message types."""

from src.schemas.aperak import AperakError, AperakMessage, AperakResponse
from src.schemas.baplie import BayPlan, BayPlanResponse, StowageLocation, StowedEquipment
from src.schemas.coarri import CoarriContainer, CoarriMessage, CoarriResponse, DamageReport
from src.schemas.codeco import ContainerMovement, GateEvent, GateEventResponse
from src.schemas.cohaor import CohaorMessage, CohaorResponse
from src.schemas.common import (
    DangerousGoods,
    Equipment,
    FunctionCode,
    Location,
    Party,
    Reference,
    Seal,
    Transport,
    TransportMode,
    Weight,
)
from src.schemas.contrl import ContrlError, ContrlMessage, ContrlResponse
from src.schemas.coparn import CoparnMessage, CoparnResponse
from src.schemas.coprar import ContainerOnWagon, CoprarMessage, CoprarResponse, WagonGroup
from src.schemas.iftmin import (
    GoodsLine,
    TransportInstruction,
    TransportInstructionResponse,
    TransportStage,
)
from src.schemas.iftsta import IftstaMessage, IftstaResponse

__all__ = [
    "AperakError",
    "AperakMessage",
    "AperakResponse",
    "BayPlan",
    "BayPlanResponse",
    "CoarriContainer",
    "CoarriMessage",
    "CoarriResponse",
    "CohaorMessage",
    "CohaorResponse",
    "ContainerMovement",
    "ContainerOnWagon",
    "ContrlError",
    "ContrlMessage",
    "ContrlResponse",
    "CoparnMessage",
    "CoparnResponse",
    "CoprarMessage",
    "CoprarResponse",
    "DamageReport",
    "DangerousGoods",
    "Equipment",
    "FunctionCode",
    "GateEvent",
    "GateEventResponse",
    "GoodsLine",
    "IftstaMessage",
    "IftstaResponse",
    "Location",
    "Party",
    "Reference",
    "Seal",
    "StowageLocation",
    "StowedEquipment",
    "Transport",
    "TransportInstruction",
    "TransportInstructionResponse",
    "TransportMode",
    "TransportStage",
    "WagonGroup",
    "Weight",
]

"""Shared Pydantic models mapping UN/EDIFACT segments to JSON."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TransportMode(str, Enum):
    SEA = "sea"
    ROAD = "road"
    RAIL = "rail"
    BARGE = "barge"
    AIR = "air"
    MULTIMODAL = "multimodal"


class FunctionCode(str, Enum):
    """BGM function code — purpose of the message."""

    ORIGINAL = "original"
    UPDATE = "update"
    CANCEL = "cancel"
    REPLACE = "replace"


class FullEmpty(str, Enum):
    FULL = "full"
    EMPTY = "empty"


class PartyRole(str, Enum):
    CARRIER = "carrier"
    HAULIER = "haulier"
    SHIPPER = "shipper"
    CONSIGNEE = "consignee"
    FORWARDER = "forwarder"
    NOTIFY = "notify"
    TERMINAL_OPERATOR = "terminal_operator"
    AGENT = "agent"
    ORDERING_PARTY = "ordering_party"


class LocationQualifier(str, Enum):
    PORT = "port"
    TERMINAL = "terminal"
    PLACE_OF_LOADING = "place_of_loading"
    PLACE_OF_DISCHARGE = "place_of_discharge"
    PLACE_OF_DELIVERY = "place_of_delivery"
    PLACE_OF_ACCEPTANCE = "place_of_acceptance"
    ORIGIN = "origin"
    DESTINATION = "destination"


class ReferenceType(str, Enum):
    BOOKING = "booking"
    BILL_OF_LADING = "bill_of_lading"
    VOYAGE = "voyage"
    CONTAINER_RELEASE_ORDER = "container_release_order"
    CUSTOMS_DECLARATION = "customs_declaration"
    TRANSPORT_ORDER = "transport_order"
    WAYBILL = "waybill"


class SealType(str, Enum):
    CARRIER = "carrier"
    SHIPPER = "shipper"
    CUSTOMS = "customs"
    TERMINAL = "terminal"
    QUARANTINE = "quarantine"


class WeightUnit(str, Enum):
    KGM = "KGM"
    LBR = "LBR"
    TNE = "TNE"


class DimensionUnit(str, Enum):
    CMT = "CMT"
    MTR = "MTR"
    FOT = "FOT"


class Party(BaseModel):
    """NAD segment — party identification."""

    role: PartyRole
    name: str = ""
    identifier: str = ""
    code_list: str = ""
    contact_name: str = ""
    communication: str = ""

    model_config = {
        "json_schema_extra": {"examples": [{"role": "carrier", "name": "Maersk Line", "identifier": "MAEU"}]}
    }


class Location(BaseModel):
    """LOC segment — place/port identification."""

    qualifier: LocationQualifier
    un_locode: str = Field("", max_length=5, description="UN/LOCODE e.g. PLGDY")
    name: str = ""
    terminal_code: str = ""

    model_config = {"json_schema_extra": {"examples": [{"qualifier": "port", "un_locode": "PLGDY", "name": "Gdynia"}]}}


class Reference(BaseModel):
    """RFF segment — reference information."""

    type: ReferenceType
    value: str

    model_config = {"json_schema_extra": {"examples": [{"type": "booking", "value": "BKG-2026-001"}]}}


class Transport(BaseModel):
    """TDT segment — details of transport."""

    mode: TransportMode
    carrier: str = ""
    vessel_name: str = ""
    vessel_imo: str = ""
    voyage_number: str = ""
    conveyance_id: str = ""
    nationality: str = ""


class Seal(BaseModel):
    """SEL segment — seal number."""

    number: str
    issuer: str = ""
    type: SealType = SealType.CARRIER


class Weight(BaseModel):
    """MEA segment — measurement/weight."""

    value: float = Field(ge=0)
    unit: WeightUnit = WeightUnit.KGM
    qualifier: str = Field("G", description="G=gross, N=net, T=tare, VGM=verified gross mass")


class Dimensions(BaseModel):
    """DIM segment — physical dimensions."""

    length: float | None = None
    width: float | None = None
    height: float | None = None
    unit: DimensionUnit = DimensionUnit.CMT


class DangerousGoods(BaseModel):
    """DGS segment — dangerous goods details (IMO/IMDG)."""

    imdg_class: str = Field(description="IMDG class e.g. 3, 6.1, 8")
    un_number: str = Field("", description="UN number e.g. UN1993")
    proper_shipping_name: str = ""
    flash_point: float | None = None
    packing_group: str = ""
    ems_number: str = ""


class ReeferSettings(BaseModel):
    """TMP/RNG segments — reefer container temperature settings."""

    set_temperature: float
    unit: str = Field("CEL", description="CEL or FAH")
    min_temperature: float | None = None
    max_temperature: float | None = None
    ventilation: float | None = Field(None, description="Ventilation percentage 0-100")
    humidity: float | None = Field(None, description="Humidity percentage 0-100")


class Equipment(BaseModel):
    """EQD segment — equipment (container) details."""

    container_id: str = Field(description="Container number e.g. MSKU1234567")
    iso_size_type: str = Field("", description="ISO 6346 size/type code e.g. 22G1")
    full_empty: FullEmpty = FullEmpty.FULL
    tare_weight: float | None = Field(None, ge=0, description="Tare weight in KG")
    operator: str = ""


class FreeText(BaseModel):
    """FTX segment — free text information."""

    qualifier: str = Field("AAA", description="FTX qualifier code")
    text: str = ""


class DateTimePeriod(BaseModel):
    """DTM segment — date/time/period."""

    qualifier: str = Field(description="DTM qualifier e.g. 132=arrival, 133=departure")
    value: datetime
    format_code: str = Field("203", description="EDIFACT date format code")


class ErrorDetail(BaseModel):
    """Standard error response."""

    code: str
    message: str
    details: dict = Field(default_factory=dict)
    trace_id: str = ""

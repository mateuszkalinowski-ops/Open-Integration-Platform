"""SDK data models (Pydantic v2)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Connector(BaseModel):
    name: str
    category: str
    version: str
    display_name: str
    description: str
    interface: str
    capabilities: list[str]
    events: list[str]
    actions: list[str]
    config_schema: dict


class ConnectorInstance(BaseModel):
    id: uuid.UUID
    connector_name: str
    connector_version: str
    connector_category: str
    display_name: str
    is_enabled: bool
    config: dict
    created_at: datetime


class Flow(BaseModel):
    id: uuid.UUID
    name: str
    is_enabled: bool
    source_connector: str
    source_event: str
    source_filter: dict | None = None
    destination_connector: str
    destination_action: str
    field_mapping: list[dict] = Field(default_factory=list)
    on_error: str = "retry"
    max_retries: int = 3
    created_at: datetime


class FlowExecution(BaseModel):
    id: uuid.UUID
    flow_id: uuid.UUID
    status: str
    source_event_data: dict
    destination_action_data: dict
    result: dict | None = None
    error: str | None = None
    duration_ms: int | None = None
    started_at: datetime
    completed_at: datetime | None = None


class EventResult(BaseModel):
    event: str
    connector: str
    flows_triggered: int
    executions: list[dict[str, Any]]


class ShipmentParty(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    email: str = ""
    phone: str = ""
    address: dict = Field(default_factory=dict)


class Shipment(BaseModel):
    order_id: str = ""
    waybill_number: str = ""
    status: str = "CREATED"
    tracking: dict = Field(default_factory=dict)
    created_at: datetime | None = None

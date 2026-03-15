"""API request/response schemas (Pydantic v2)."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConnectorHealthSummary(BaseModel):
    status: str = "unknown"
    latency_ms: float | None = None
    last_check: float | None = None
    consecutive_failures: int = 0
    last_error: str | None = None
    error_rate_5m: float | None = None


class ConnectorSchemaField(BaseModel):
    field: str
    label: str
    type: str
    required: bool = False
    description: str | None = None


class ConnectorActionSchemaResponse(BaseModel):
    connector_name: str
    action: str
    source: Literal["static", "dynamic", "merged"]
    cached: bool = False
    input_fields: list[ConnectorSchemaField] = Field(default_factory=list)
    output_fields: list[ConnectorSchemaField] = Field(default_factory=list)


class ConnectorActionMetadata(BaseModel):
    label: str | None = None
    description: str | None = None


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9][a-z0-9_-]*$")


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    name: str = Field(default="", max_length=200)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    key_prefix: str
    name: str
    is_active: bool
    created_at: datetime
    raw_key: str | None = None

    model_config = {"from_attributes": True}


class ConnectorResponse(BaseModel):
    name: str
    category: str
    version: str
    display_name: str
    description: str
    country: str = ""
    logo_url: str = ""
    website_url: str = ""
    interface: str
    capabilities: list[str]
    events: list[str]
    actions: list[str]
    action_metadata: dict[str, ConnectorActionMetadata] = Field(default_factory=dict)
    config_schema: dict
    api_endpoints: list[dict] = Field(default_factory=list)
    event_fields: dict[str, list[dict]] = Field(default_factory=dict)
    action_fields: dict[str, list[dict]] = Field(default_factory=dict)
    output_fields: dict[str, list[dict]] = Field(default_factory=dict)
    auth_type: str = "custom"
    status: str = "stable"
    supports_oauth2: bool = False
    sandbox_available: bool = False
    has_webhooks: bool = False
    health: ConnectorHealthSummary | None = None
    deployment: str = "cloud"
    requires_onpremise_agent: bool = False
    onpremise_agent: dict = Field(default_factory=dict)


class ConnectorInstanceCreate(BaseModel):
    connector_name: str
    connector_version: str
    connector_category: str
    display_name: str = ""
    config: dict = Field(default_factory=dict)


class ConnectorInstanceResponse(BaseModel):
    id: uuid.UUID
    connector_name: str
    connector_version: str
    connector_category: str
    display_name: str
    is_enabled: bool
    config: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class CredentialStore(BaseModel):
    connector_name: str
    credential_name: str = "default"
    old_credential_name: str | None = None
    credentials: dict[str, str]


class CredentialTokenResolve(BaseModel):
    token: str


class FlowCreate(BaseModel):
    name: str = Field(..., max_length=200)
    source_connector: str = Field(..., max_length=100)
    source_event: str = Field(..., max_length=200)
    source_filter: dict | None = None
    destination_connector: str = Field(..., max_length=100)
    destination_connector_version: str | None = Field(default=None, max_length=20)
    destination_action: str = Field(..., max_length=200)
    field_mapping: list[dict] = Field(default_factory=list)
    transform: str | None = None
    on_error: Literal["retry", "stop", "ignore"] = "retry"
    max_retries: int = Field(default=3, ge=0, le=20)


class FlowUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    source_connector: str | None = Field(default=None, max_length=100)
    source_event: str | None = Field(default=None, max_length=200)
    source_filter: dict | None = None
    destination_connector: str | None = Field(default=None, max_length=100)
    destination_connector_version: str | None = Field(default=None, max_length=20)
    destination_action: str | None = Field(default=None, max_length=200)
    field_mapping: list[dict] | None = None
    transform: str | None = None
    on_error: Literal["retry", "stop", "ignore"] | None = None
    max_retries: int | None = Field(default=None, ge=0, le=20)
    is_enabled: bool | None = None


class FlowResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_enabled: bool
    source_connector: str
    source_event: str
    source_filter: dict | None
    destination_connector: str
    destination_connector_version: str | None = None
    destination_action: str
    field_mapping: list[dict]
    on_error: str
    max_retries: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FlowExecutionResponse(BaseModel):
    id: uuid.UUID
    flow_id: uuid.UUID
    status: str
    source_event_data: dict
    destination_action_data: dict
    result: dict | None
    error: str | None
    retry_count: int
    duration_ms: int | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class EventTrigger(BaseModel):
    connector_name: str
    event: str
    data: dict[str, Any]


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    uptime_seconds: float
    checks: dict[str, str]


# --- Workflows ---


class WorkflowNodePosition(BaseModel):
    x: float = 0
    y: float = 0


class WorkflowNode(BaseModel):
    id: str
    type: str  # trigger, action, condition, switch, transform, filter, delay, loop, merge, http_request, set_variable, response
    label: str = ""
    position: WorkflowNodePosition = Field(default_factory=WorkflowNodePosition)
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str = "default"
    label: str = ""


class WorkflowCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = Field(default="", max_length=1000)
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)
    sync_config: dict[str, Any] | None = None
    on_error: Literal["retry", "stop", "ignore"] = "stop"
    max_retries: int = Field(default=3, ge=0, le=20)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


class WorkflowTemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tags: list[str] = Field(default_factory=list)
    source_connector: str | None = None
    source_event: str | None = None
    destination_connector: str | None = None
    destination_action: str | None = None


class WorkflowTemplateDetail(WorkflowTemplateSummary):
    workflow: WorkflowCreate


class WorkflowTemplateInstantiateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    activate: bool = False
    credential_names: dict[str, str] = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    nodes: list[WorkflowNode] | None = None
    edges: list[WorkflowEdge] | None = None
    variables: dict[str, Any] | None = None
    sync_config: dict[str, Any] | None = None
    is_enabled: bool | None = None
    on_error: Literal["retry", "stop", "ignore"] | None = None
    max_retries: int | None = Field(default=None, ge=0, le=20)
    timeout_seconds: int | None = Field(default=None, ge=1, le=3600)


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    is_enabled: bool
    version: int
    trigger_connector: str | None
    trigger_event: str | None
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    variables: dict[str, Any]
    sync_config: dict[str, Any] | None = None
    on_error: str
    max_retries: int
    timeout_seconds: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID | None
    workflow_name: str | None = None
    status: str
    trigger_data: dict[str, Any]
    node_results: list[dict[str, Any]]
    context_snapshot: dict[str, Any]
    error: str | None
    error_node_id: str | None
    duration_ms: int | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class WorkflowTestRequest(BaseModel):
    trigger_data: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


class WorkflowRerunRequest(BaseModel):
    from_node_id: str
    override_data: dict[str, Any] = Field(default_factory=dict)


class AiChatMessage(BaseModel):
    role: Literal["user", "assistant"] = "user"
    content: str


class WorkflowAiGenerateRequest(BaseModel):
    prompt: str
    model: Literal["gemini", "opus"] = "gemini"
    api_key: str
    conversation: list[AiChatMessage] = Field(default_factory=list)
    current_nodes: list[dict[str, Any]] = Field(default_factory=list)
    current_edges: list[dict[str, Any]] = Field(default_factory=list)
    connectors: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowAiGenerateResponse(BaseModel):
    message: str
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None
    name: str | None = None
    description: str | None = None


class AiFieldMappingSuggestRequest(BaseModel):
    model: Literal["gemini", "opus"] = "gemini"
    api_key: str
    prompt: str | None = None
    source_fields: list[dict[str, Any]] = Field(default_factory=list)
    destination_fields: list[dict[str, Any]] = Field(default_factory=list)
    existing_mappings: list[dict[str, Any]] = Field(default_factory=list)


class AiFieldMappingSuggestResponse(BaseModel):
    message: str
    mappings: list[dict[str, Any]] = Field(default_factory=list)


class AiExplainErrorRequest(BaseModel):
    model: Literal["gemini", "opus"] = "gemini"
    api_key: str
    workflow_name: str | None = None
    node_label: str | None = None
    node_type: str | None = None
    error: str
    trigger_data: dict[str, Any] = Field(default_factory=dict)
    node_results: list[dict[str, Any]] = Field(default_factory=list)


class AiExplainErrorResponse(BaseModel):
    summary: str
    likely_causes: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)


# --- Execution Detail (GDPR-aware) ---


# --- Demo Gate ---


class DemoRegisterRequest(BaseModel):
    workspace_name: str = Field(..., min_length=1, max_length=100)


class DemoRegisterResponse(BaseModel):
    api_key: str
    tenant_name: str
    tenant_slug: str


class DemoValidateKeyRequest(BaseModel):
    api_key: str


class DemoValidateKeyResponse(BaseModel):
    valid: bool
    tenant_name: str | None = None


# --- Execution Detail (GDPR-aware) ---


class FlowExecutionDetailResponse(BaseModel):
    id: uuid.UUID
    flow_id: uuid.UUID
    status: str
    source_event_data: dict[str, Any]
    destination_action_data: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    retry_count: int
    duration_ms: int | None
    started_at: datetime
    completed_at: datetime | None
    flow_name: str | None = None
    source_connector: str | None = None
    destination_connector: str | None = None
    gdpr: dict[str, Any] = Field(default_factory=dict, alias="gdpr_meta")

    model_config = {"from_attributes": True, "populate_by_name": True}


class WorkflowExecutionDetailResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID | None
    status: str
    trigger_data: dict[str, Any]
    node_results: list[dict[str, Any]]
    context_snapshot: dict[str, Any]
    workflow_nodes_snapshot: list[dict[str, Any]] | None = None
    workflow_edges_snapshot: list[dict[str, Any]] | None = None
    error: str | None
    error_node_id: str | None
    duration_ms: int | None
    started_at: datetime
    completed_at: datetime | None
    workflow_name: str | None = None
    workflow_description: str | None = None
    trigger_connector: str | None = None
    trigger_event: str | None = None
    gdpr: dict[str, Any] = Field(default_factory=dict, alias="gdpr_meta")

    model_config = {"from_attributes": True, "populate_by_name": True}

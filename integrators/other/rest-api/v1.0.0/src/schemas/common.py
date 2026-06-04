"""Request/response models for REST API Gateway connector."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RestCallRequest(BaseModel):
    account: str
    endpoint: str = ""
    named_action: str = ""
    method: str = ""
    body: dict[str, Any] | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    timeout_s: int | None = None


class RestCallResponse(BaseModel):
    status: str
    http_status: int
    response_status: str = ""
    message: str = ""
    data: Any = None
    raw_response: Any = None
    elapsed_ms: int = 0
    account: str = ""
    endpoint: str = ""


class RestPollRequest(BaseModel):
    account: str
    endpoint: str = ""
    named_action: str = ""
    cursor_field: str = "last_id"
    cursor_response_field: str = "max_id"
    items_field: str = "items"
    limit: int = 1000
    method: str = ""
    cursor_value: Any = None


class RestPollResponse(BaseModel):
    status: str
    items: list[Any] = Field(default_factory=list)
    cursor_value: Any = None
    count: int = 0
    http_status: int = 200
    elapsed_ms: int = 0
    account: str = ""
    endpoint: str = ""


class BatchCallItem(BaseModel):
    endpoint: str = ""
    named_action: str = ""
    method: str = ""
    body: dict[str, Any] | None = None


class RestBatchRequest(BaseModel):
    account: str
    calls: list[BatchCallItem]
    parallel: bool = False
    stop_on_error: bool = True


class BatchResultItem(BaseModel):
    index: int
    status: str
    http_status: int = 0
    data: Any = None
    error: str = ""
    endpoint: str = ""
    elapsed_ms: int = 0


class RestBatchResponse(BaseModel):
    status: str
    results: list[BatchResultItem] = Field(default_factory=list)
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    elapsed_ms: int = 0


class RestDiscoverRequest(BaseModel):
    account: str
    openapi_url: str = ""
    generate_aliases: bool = True


class DiscoveredEndpoint(BaseModel):
    endpoint: str
    method: str = "POST"
    description: str = ""
    alias: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class RestDiscoverResponse(BaseModel):
    status: str
    found: bool = False
    openapi_url: str = ""
    openapi_version: str = ""
    endpoints: list[DiscoveredEndpoint] = Field(default_factory=list)
    count: int = 0
    message: str = ""


class HealthResponse(BaseModel):
    status: str
    account: str = ""
    base_url: str = ""
    http_status: int | None = None
    elapsed_ms: int = 0
    error: str = ""

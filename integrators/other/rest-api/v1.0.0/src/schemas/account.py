"""Account configuration models for REST API Gateway connector."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuthType(str, Enum):
    NONE = "none"
    BEARER = "bearer"
    BEARER_WITH_CUSTOM_HEADERS = "bearer_with_custom_headers"
    BASIC = "basic"
    API_KEY_HEADER = "api_key_header"
    API_KEY_QUERY = "api_key_query"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"


class AuthConfig(BaseModel):
    type: AuthType = AuthType.NONE
    bearer_token: str = ""
    username: str = ""
    password: str = ""
    api_key: str = ""
    api_key_header_name: str = "X-API-Key"
    api_key_param_name: str = "api_key"
    token_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    scope: str = ""
    custom_headers: dict[str, str] = Field(default_factory=dict)


class TimeoutConfig(BaseModel):
    connect_s: float = 30.0
    read_s: float = 60.0


class RetryConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_initial_s: float = 2.0
    backoff_multiplier: float = 2.0
    retryable_status_codes: list[int] = Field(default_factory=lambda: [429, 502, 503, 504])


class ResponseMappingConfig(BaseModel):
    """How to interpret the response JSON from the target system."""

    use_http_status: bool = False
    status_field: str = ""
    status_ok_values: list[str] = Field(default_factory=lambda: ["OK"])
    status_error_values: list[str] = Field(default_factory=lambda: ["ERROR"])
    message_field: str = ""
    data_field: str | None = None
    error_code_field: str = ""


class ActionDefinition(BaseModel):
    endpoint: str
    method: str = ""
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"


class DiscoveryInfo(BaseModel):
    openapi_url: str = ""
    last_discovered_at: str = ""
    endpoints_count: int = 0
    openapi_version: str = ""


class AccountConfig(BaseModel):
    name: str
    description: str = ""
    profile: str = "auto"

    base_url: str
    path_prefix: str = ""
    default_method: str = "POST"
    default_content_type: str = "application/json"

    auth: AuthConfig = Field(default_factory=AuthConfig)
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    response_mapping: ResponseMappingConfig = Field(default_factory=ResponseMappingConfig)

    rate_limit: str = ""
    action_registry: dict[str, ActionDefinition] = Field(default_factory=dict)
    discovery: DiscoveryInfo = Field(default_factory=DiscoveryInfo)

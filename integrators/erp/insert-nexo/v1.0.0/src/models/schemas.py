"""Pydantic schemas for the InsERT Nexo cloud connector."""

from pydantic import BaseModel, Field


class AgentAccount(BaseModel):
    name: str
    agent_url: str
    agent_api_key: str = ""
    environment: str = "production"
    sync_enabled: bool = True


class AgentHeartbeat(BaseModel):
    agent_id: str
    agent_version: str
    timestamp: str
    erp: dict = Field(default_factory=dict)
    queue: dict = Field(default_factory=dict)
    system: dict = Field(default_factory=dict)


class SyncPayload(BaseModel):
    agent_id: str
    entity_type: str
    operation: str
    payload: dict = Field(default_factory=dict)

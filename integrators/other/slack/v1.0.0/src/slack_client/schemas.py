"""Slack Web API Pydantic models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SlackChannel(BaseModel):
    id: str
    name: str = ""
    is_channel: bool = Field(default=False, alias="is_channel")
    is_private: bool = Field(default=False, alias="is_private")
    is_im: bool = Field(default=False, alias="is_im")
    is_mpim: bool = Field(default=False, alias="is_mpim")
    is_archived: bool = Field(default=False, alias="is_archived")
    is_member: bool = Field(default=False, alias="is_member")
    num_members: int = Field(default=0, alias="num_members")
    topic: dict[str, Any] = Field(default_factory=dict)
    purpose: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class SlackMessage(BaseModel):
    channel_id: str = ""
    channel_name: str = ""
    user_id: str = ""
    user_name: str = ""
    text: str = ""
    ts: str = ""
    thread_ts: str = ""
    reply_count: int = 0
    bot_id: str = ""
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    files: list[dict[str, Any]] = Field(default_factory=list)
    account_name: str = ""


class SlackMessagesPage(BaseModel):
    messages: list[SlackMessage] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False
    channel_id: str = ""


class SendMessageRequest(BaseModel):
    channel: str
    text: str
    thread_ts: str = ""
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    unfurl_links: bool = True
    unfurl_media: bool = True


class SendMessageResponse(BaseModel):
    ok: bool = True
    channel: str = ""
    ts: str = ""
    message_text: str = ""
    account_name: str = ""


class AddReactionRequest(BaseModel):
    channel: str
    timestamp: str
    name: str


class FileUploadRequest(BaseModel):
    channels: list[str]
    filename: str
    content_base64: str
    title: str = ""
    initial_comment: str = ""


class FileUploadResponse(BaseModel):
    ok: bool = True
    file_id: str = ""
    file_url: str = ""


class AuthStatusResponse(BaseModel):
    account_name: str
    authenticated: bool = False
    bot_user_id: str = ""
    team_name: str = ""
    team_id: str = ""

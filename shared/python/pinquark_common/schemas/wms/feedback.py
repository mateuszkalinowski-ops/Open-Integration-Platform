"""Pinquark WMS Feedback DTO.

Represents operation results returned by the WMS after processing
articles, documents, contractors, etc.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FeedbackAction(str, Enum):
    SAVE = "SAVE"
    DELETE = "DELETE"


class FeedbackEntity(str, Enum):
    ARTICLE = "ARTICLE"
    CONTRACTOR = "CONTRACTOR"
    DOCUMENT = "DOCUMENT"
    POSITION = "POSITION"


class Feedback(BaseModel):
    id: int | None = None
    action: FeedbackAction
    entity: FeedbackEntity
    success: bool = False
    errors: dict[str, Any] = Field(default_factory=dict)
    response_messages: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_api_dict(cls, data: dict) -> "Feedback":
        return cls(
            id=data.get("id"),
            action=FeedbackAction(data["action"]),
            entity=FeedbackEntity(data["entity"]),
            success=data.get("success", False),
            errors=data.get("errors", {}),
            response_messages=data.get("responseMessages", {}),
        )

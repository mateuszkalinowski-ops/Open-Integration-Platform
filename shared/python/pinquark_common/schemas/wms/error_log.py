"""Pinquark WMS Error Log DTO.

Represents JSON parsing errors stored by the integration layer.
"""

from datetime import datetime

from pydantic import BaseModel


class ErrorLog(BaseModel):
    body: str = ""
    created_date: datetime | None = None
    topic: str = ""

    @classmethod
    def from_api_dict(cls, data: dict) -> "ErrorLog":
        return cls(
            body=data.get("body", ""),
            created_date=datetime.fromisoformat(data["createdDate"]) if data.get("createdDate") else None,
            topic=data.get("topic", ""),
        )

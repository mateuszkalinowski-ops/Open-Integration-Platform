"""Pinquark WMS Attribute DTO.

Universal attribute model used across all WMS entities:
articles, documents, positions, contractors, article batches.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class AttributeType(str, Enum):
    DATE = "DATE"
    DECIMAL = "DECIMAL"
    INTEGER = "INTEGER"
    TEXT = "TEXT"
    TIME = "TIME"


class Attribute(BaseModel):
    """Single key-value attribute attached to any WMS entity.

    The value is stored in the field matching `type`:
    TEXT -> valueText, INTEGER -> valueInt, DECIMAL -> valueDecimal,
    DATE -> valueDate, TIME -> valueTime.
    """

    symbol: str
    type: AttributeType
    value_text: str | None = None
    value_int: int | None = None
    value_decimal: Decimal | None = None
    value_date: date | None = None
    value_time: datetime | None = None
    value_date_to: date | None = None
    created_date: datetime | None = None
    filename: str | None = None
    status: int = 1

    class Config:
        populate_by_name = True
        alias_generator = None

    def to_api_dict(self) -> dict:
        """Serialize to Pinquark REST API format (camelCase)."""
        return {
            "symbol": self.symbol,
            "type": self.type.value,
            "valueText": self.value_text,
            "valueInt": self.value_int,
            "valueDecimal": float(self.value_decimal) if self.value_decimal is not None else None,
            "valueDate": self.value_date.isoformat() if self.value_date else None,
            "valueTime": self.value_time.isoformat() if self.value_time else None,
            "valueDateTo": self.value_date_to.isoformat() if self.value_date_to else None,
            "createdDate": self.created_date.isoformat() if self.created_date else None,
            "filename": self.filename,
            "status": self.status,
        }

    @classmethod
    def from_api_dict(cls, data: dict) -> "Attribute":
        """Deserialize from Pinquark REST API format (camelCase)."""
        return cls(
            symbol=data["symbol"],
            type=AttributeType(data["type"]),
            value_text=data.get("valueText"),
            value_int=data.get("valueInt"),
            value_decimal=Decimal(str(data["valueDecimal"])) if data.get("valueDecimal") is not None else None,
            value_date=date.fromisoformat(data["valueDate"]) if data.get("valueDate") else None,
            value_time=datetime.fromisoformat(data["valueTime"]) if data.get("valueTime") else None,
            value_date_to=date.fromisoformat(data["valueDateTo"]) if data.get("valueDateTo") else None,
            created_date=datetime.fromisoformat(data["createdDate"]) if data.get("createdDate") else None,
            filename=data.get("filename"),
            status=data.get("status", 1),
        )

"""Payload validators for Pinquark WMS connector actions.

Pydantic models that enforce field types and constraints before the
request reaches the WMS Integration REST API. Catches malformed payloads
early with clear 422 errors.

Validation constants (SOURCES, DOCUMENT_TYPES) are the canonical source
of truth and are imported by schemas.py for inline field_validators.
"""

from pydantic import BaseModel, Field, field_validator

DOCUMENT_TYPES = {
    "PZ", "WZ", "PW", "RW", "MM", "ZK", "ZW",
    "PZ_K", "WZ_K", "INW", "PRZEM",
}

SOURCES = {"ERP", "WMS"}


class ArticleCreatePayload(BaseModel):
    erpId: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=500)
    symbol: str = Field(..., min_length=1, max_length=100)
    ean: str | None = Field(None, max_length=50)
    group: str | None = Field(None, max_length=100)
    type: str | None = Field(None, max_length=50)
    unit: str | None = Field(None, max_length=20)
    source: str | None = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        if v is not None and v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


class ArticleBatchCreatePayload(BaseModel):
    batchNumber: str = Field(..., min_length=1, max_length=100)
    erpArticleId: int = Field(..., ge=1)
    eanCode: str | None = Field(None, max_length=50)
    batchOwner: str | None = Field(None, max_length=200)
    batchOwnerId: int | None = Field(None, ge=1)
    termValidity: str | None = None


class DocumentCreatePayload(BaseModel):
    erpId: int = Field(..., ge=1)
    documentType: str = Field(..., min_length=1, max_length=20)
    source: str = Field(..., min_length=1)
    symbol: str | None = Field(None, max_length=100)
    date: str | None = None
    dueDate: str | None = None

    @field_validator("documentType")
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        if v not in DOCUMENT_TYPES:
            raise ValueError(
                f"Invalid documentType '{v}', must be one of: {', '.join(sorted(DOCUMENT_TYPES))}"
            )
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        if v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


class ContractorCreatePayload(BaseModel):
    erpId: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=500)
    symbol: str = Field(..., min_length=1, max_length=100)
    source: str | None = None
    email: str | None = Field(None, max_length=254)
    phone: str | None = Field(None, max_length=30)
    taxNumber: str | None = Field(None, max_length=30)

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        if v is not None and v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


class PositionCreatePayload(BaseModel):
    documentId: int = Field(..., ge=1)
    documentSource: str = Field(default="ERP")

    @field_validator("documentSource")
    @classmethod
    def validate_source(cls, v: str) -> str:
        if v not in SOURCES:
            raise ValueError(f"Invalid documentSource '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


class DeleteCommandPayload(BaseModel):
    uniqueCode: str = Field(..., min_length=1, max_length=200)
    source: str | None = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        if v is not None and v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


class PositionDeleteCommandPayload(BaseModel):
    documentId: int = Field(..., ge=1)
    source: str = Field(default="ERP")
    uniqueCode: str = Field(..., min_length=1, max_length=200)

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        if v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


class DocumentWrapperPayload(BaseModel):
    continueOnFail: bool = True
    documents: list[DocumentCreatePayload] = Field(..., min_length=1)

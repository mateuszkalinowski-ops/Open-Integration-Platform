"""Pydantic models matching the Pinquark WMS Integration REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from src.validators import DOCUMENT_TYPES, SOURCES

# --- Auth ---


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    accessToken: str
    accessTokenExpirationDate: str
    refreshToken: str


class RefreshTokenRequest(BaseModel):
    refreshToken: str


# --- Shared / Generic ---


class Attribute(BaseModel):
    createdDate: str | None = None
    filename: str | None = None
    status: int | None = None
    symbol: str | None = None
    type: str | None = None
    valueDate: str | None = None
    valueDateTo: str | None = None
    valueDecimal: float | None = None
    valueInt: int | None = None
    valueText: str | None = None
    valueTime: str | None = None


class Address(BaseModel):
    active: bool | None = None
    apartmentNo: str | None = None
    city: str | None = None
    code: str | None = None
    commune: str | None = None
    contractorId: int | None = None
    contractorSource: str | None = None
    country: str | None = None
    county: str | None = None
    dateFrom: str | None = None
    dateTo: str | None = None
    description: str | None = None
    district: str | None = None
    houseNo: str | None = None
    name: str | None = None
    postCity: str | None = None
    province: str | None = None
    street: str | None = None


class Image(BaseModel):
    createdDate: str | None = None
    default: bool | None = None
    path: str | None = None


class UnitOfMeasure(BaseModel):
    converterToMainUnit: float | None = None
    default: bool | None = None
    eans: list[str] = Field(default_factory=list)
    height: float | None = None
    length: float | None = None
    unit: str | None = None
    weight: float | None = None
    width: float | None = None


class Provider(BaseModel):
    code: str | None = None
    contractorId: int | None = None
    contractorSource: str | None = None
    createdDate: str | None = None
    eanCode: str | None = None
    name: str | None = None
    symbol: str | None = None
    unit: str | None = None


class DeleteCommand(BaseModel):
    uniqueCode: str
    source: str | None = None


class Contact(BaseModel):
    contractorId: int | None = None
    contractorSource: str | None = None
    description: str | None = None
    email: str | None = None
    emailAlternative: str | None = None
    fax: str | None = None
    internetMessenger1: str | None = None
    internetMessenger2: str | None = None
    internetMessenger3: str | None = None
    name: str | None = None
    phone: str | None = None
    phoneAlternative: str | None = None
    www: str | None = None


# --- Articles ---


class Article(BaseModel):
    attributes: list[Attribute] = Field(default_factory=list)
    ean: str | None = None
    erpId: int | None = None
    wmsId: int | None = None
    group: str | None = None
    images: list[Image] = Field(default_factory=list)
    name: str | None = None
    providers: list[Provider] = Field(default_factory=list)
    source: str | None = None
    state: int | None = None
    symbol: str | None = None
    type: str | None = None
    unit: str | None = None
    unitsOfMeasure: list[UnitOfMeasure] = Field(default_factory=list)

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        if v is not None and v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


# --- Article Batches ---


class ArticleBatch(BaseModel):
    attributes: list[Attribute] = Field(default_factory=list)
    batchNumber: str | None = None
    eanCode: str | None = None
    batchOwner: str | None = None
    batchOwnerId: int | None = None
    erpArticleId: int | None = None
    termValidity: str | None = None


# --- Contractors ---


class Contractor(BaseModel):
    address: Address | None = None
    addresses: list[Address] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    description: str | None = None
    email: str | None = None
    erpId: int | None = None
    isSupplier: bool | None = None
    name: str | None = None
    phone: str | None = None
    source: str | None = None
    supplierSymbol: str | None = None
    symbol: str | None = None
    taxNumber: str | None = None
    wmsId: int | None = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        if v is not None and v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


# --- Document Positions ---


class Position(BaseModel):
    article: Article | None = None
    articleBatch: ArticleBatch | None = None
    attributes: list[Attribute] = Field(default_factory=list)
    no: int | None = None
    erpId: int | None = None
    note: str | None = None
    quantity: float | None = None
    statusSymbol: str | None = None


class PositionWrapper(BaseModel):
    documentId: int
    documentSource: str = "ERP"
    positions: list[Position] = Field(default_factory=list)


class PositionDeleteCommand(BaseModel):
    documentId: int
    source: str = "ERP"
    uniqueCode: str


# --- Documents ---


class ContractorRef(BaseModel):
    erpId: int | None = None
    wmsId: int | None = None
    source: str = "ERP"


class Document(BaseModel):
    additionalCourierInfo: str | None = None
    attributes: list[Attribute] = Field(default_factory=list)
    commissionSymbol: str | None = None
    connectZK: bool | None = None
    contact: Contact | None = None
    contractor: ContractorRef | Contractor | None = None
    date: str | None = None
    deleteAllPositions: bool | None = None
    deliveryAddress: Address | None = None
    deliveryMethodSymbol: str | None = None
    documentType: str | None = None
    dueDate: str | None = None
    erpCode: str | None = None
    erpId: int | None = None
    erpStatusSymbol: str | None = None
    inputDocumentNumber: str | None = None
    new: bool | None = None
    note: str | None = None
    orderType: str | None = None
    ownCode: str | None = None
    positions: list[Position] = Field(default_factory=list)
    positionsChanged: bool | None = None
    priority: int | None = None
    procedures: list[str] = Field(default_factory=list)
    recipientId: int | None = None
    recipientSource: str | None = None
    route: str | None = None
    source: str | None = None
    symbol: str | None = None
    warehouseSymbol: str | None = None
    wmsId: int | None = None

    @field_validator("documentType")
    @classmethod
    def validate_document_type(cls, v: str | None) -> str | None:
        if v is not None and v not in DOCUMENT_TYPES:
            raise ValueError(f"Invalid documentType '{v}', must be one of: {', '.join(sorted(DOCUMENT_TYPES))}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        if v is not None and v not in SOURCES:
            raise ValueError(f"Invalid source '{v}', must be one of: {', '.join(sorted(SOURCES))}")
        return v


class DocumentWrapper(BaseModel):
    continueOnFail: bool = True
    documents: list[Document] = Field(default_factory=list)


# --- Feedback ---


class Feedback(BaseModel):
    action: str | None = None
    entity: str | None = None
    errors: dict[str, str] = Field(default_factory=dict)
    responseMessages: dict[str, str] = Field(default_factory=dict)
    id: int | None = None
    success: bool | None = None


# --- JSON Errors ---


class JsonError(BaseModel):
    body: str | None = None
    createdDate: str | None = None
    topic: str | None = None


# --- Credentials (used by integrator routes) ---


class WmsCredentials(BaseModel):
    api_url: str
    username: str
    password: str
    polling_interval_seconds: int | None = None

    @field_validator("api_url")
    @classmethod
    def _validate_api_url(cls, v: str) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("api_url must use http or https scheme")
        host = parsed.hostname or ""
        if host in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
            raise ValueError("api_url must not target localhost or metadata endpoints")
        _private_prefixes = ("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                             "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                             "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                             "172.30.", "172.31.", "192.168.", "169.254.")
        if any(host.startswith(p) for p in _private_prefixes):
            raise ValueError("api_url must not target private network addresses")
        return v

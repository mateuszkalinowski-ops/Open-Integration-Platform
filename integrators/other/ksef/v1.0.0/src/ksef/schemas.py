"""Pydantic schemas for KSeF connector request/response models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class KSeFEnvironmentEnum(str, Enum):
    TEST = "test"
    DEMO = "demo"
    PRODUCTION = "production"


class ContextIdentifierType(str, Enum):
    NIP = "Nip"
    INTERNAL_ID = "InternalId"
    NIP_VAT_UE = "NipVatUe"


class SessionType(str, Enum):
    ONLINE = "online"
    BATCH = "batch"


# -- Auth schemas --


class AuthChallengeResponse(BaseModel):
    challenge: str
    timestamp: str
    timestamp_ms: int = Field(alias="timestampMs")
    client_ip: str = Field(alias="clientIp")

    model_config = {"populate_by_name": True}


class ContextIdentifier(BaseModel):
    type: ContextIdentifierType = ContextIdentifierType.NIP
    value: str


class TokenAuthRequest(BaseModel):
    challenge: str
    context_identifier: ContextIdentifier = Field(alias="contextIdentifier")
    encrypted_token: str = Field(alias="encryptedToken")

    model_config = {"populate_by_name": True}


class AuthToken(BaseModel):
    token: str
    valid_until: str = Field(alias="validUntil")

    model_config = {"populate_by_name": True}


class AuthInitResponse(BaseModel):
    reference_number: str = Field(alias="referenceNumber")
    authentication_token: AuthToken = Field(alias="authenticationToken")

    model_config = {"populate_by_name": True}


class AuthStatusCode(BaseModel):
    code: int
    description: str
    details: list[str] = Field(default_factory=list)


class AuthStatusResponse(BaseModel):
    start_date: str = Field(alias="startDate")
    authentication_method: str = Field(alias="authenticationMethod")
    status: AuthStatusCode

    model_config = {"populate_by_name": True}


class AuthTokensResponse(BaseModel):
    access_token: AuthToken = Field(alias="accessToken")
    refresh_token: AuthToken = Field(alias="refreshToken")

    model_config = {"populate_by_name": True}


class AuthTokenRefreshResponse(BaseModel):
    access_token: AuthToken = Field(alias="accessToken")

    model_config = {"populate_by_name": True}


# -- Session schemas --


class EncryptionInfo(BaseModel):
    encryption_key: str = Field(alias="encryptionKey")
    encryption_key_algorithm: str = Field(
        default="RSA-OAEP",
        alias="encryptionKeyAlgorithm",
    )
    encryption_algorithm: str = Field(
        default="AES-256-CBC",
        alias="encryptionAlgorithm",
    )
    public_key_serial_number: str = Field(alias="publicKeySerialNumber")

    model_config = {"populate_by_name": True}


class FormCode(BaseModel):
    system_code: str = Field(alias="systemCode")
    schema_version: str = Field(alias="schemaVersion")
    target_namespace: str = Field(alias="targetNamespace")
    value: str

    model_config = {"populate_by_name": True}


class OpenSessionRequest(BaseModel):
    form_code: FormCode = Field(alias="formCode")
    encryption: EncryptionInfo

    model_config = {"populate_by_name": True}


class SessionStatusCode(BaseModel):
    code: int
    description: str


class SessionOpenResponse(BaseModel):
    reference_number: str = Field(alias="referenceNumber")
    valid_until: str = Field(default="", alias="validUntil")

    model_config = {"populate_by_name": True}


class SessionStatusResponse(BaseModel):
    reference_number: str = Field(alias="referenceNumber")
    status: SessionStatusCode
    invoices_count: int = Field(default=0, alias="invoicesCount")
    start_date: str = Field(default="", alias="startDate")

    model_config = {"populate_by_name": True}


# -- Invoice schemas --


class InvoiceHashInfo(BaseModel):
    hash_sha256: str = Field(alias="hashSHA256")
    file_size: int = Field(alias="fileSize")

    model_config = {"populate_by_name": True}


class SendInvoiceRequest(BaseModel):
    encrypted_invoice: str = Field(alias="encryptedInvoice")
    plain_hash: InvoiceHashInfo = Field(alias="plainHash")
    encrypted_hash: InvoiceHashInfo = Field(alias="encryptedHash")

    model_config = {"populate_by_name": True}


class InvoiceStatusCode(BaseModel):
    code: int
    description: str


class SendInvoiceResponse(BaseModel):
    reference_number: str = Field(alias="referenceNumber")
    timestamp: str = ""

    model_config = {"populate_by_name": True}


class InvoiceStatusResponse(BaseModel):
    ksef_reference_number: str = Field(default="", alias="ksefReferenceNumber")
    status: InvoiceStatusCode
    invoice_number: str = Field(default="", alias="invoiceNumber")

    model_config = {"populate_by_name": True}


class InvoiceQueryItem(BaseModel):
    ksef_number: str = Field(default="", alias="ksefNumber")
    invoice_number: str = Field(default="", alias="invoiceNumber")
    issue_date: str = Field(default="", alias="issueDate")
    invoicing_date: str = Field(default="", alias="invoicingDate")
    net_amount: float = Field(default=0.0, alias="netAmount")
    gross_amount: float = Field(default=0.0, alias="grossAmount")
    vat_amount: float = Field(default=0.0, alias="vatAmount")
    currency: str = Field(default="PLN")
    invoice_type: str = Field(default="", alias="invoiceType")
    seller: dict[str, Any] = Field(default_factory=dict)
    buyer: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class InvoiceQueryResponse(BaseModel):
    has_more: bool = Field(default=False, alias="hasMore")
    is_truncated: bool = Field(default=False, alias="isTruncated")
    invoices: list[InvoiceQueryItem] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# -- Public key schemas --


class PublicKeyInfo(BaseModel):
    serial_number: str = Field(alias="serialNumber")
    certificate: str
    valid_from: str = Field(default="", alias="validFrom")
    valid_to: str = Field(default="", alias="validTo")

    model_config = {"populate_by_name": True}


class PublicKeyCertificatesResponse(BaseModel):
    items: list[PublicKeyInfo] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# -- API route request/response models --


class AuthenticateRequest(BaseModel):
    account_name: str
    nip: str | None = None


class AuthenticateResponse(BaseModel):
    access_token: str
    refresh_token: str
    access_valid_until: str
    refresh_valid_until: str


class OpenSessionApiRequest(BaseModel):
    account_name: str
    session_type: SessionType = SessionType.ONLINE
    form_code: str = "FA3"


class OpenSessionApiResponse(BaseModel):
    reference_number: str
    status: str
    session_type: str


class SendInvoiceApiRequest(BaseModel):
    account_name: str
    reference_number: str
    invoice_xml: str | None = None
    invoice_data: dict[str, Any] | None = None


class SendInvoiceApiResponse(BaseModel):
    reference_number: str
    status: str


class CloseSessionApiRequest(BaseModel):
    account_name: str


class GetInvoiceStatusApiResponse(BaseModel):
    ksef_reference_number: str
    status_code: int
    status_description: str
    invoice_number: str = ""


class QueryInvoicesApiRequest(BaseModel):
    account_name: str
    date_from: str | None = None
    date_to: str | None = None
    subject_nip: str | None = None
    page_size: int = 10
    page_offset: int = 0
    date_type: str = "Issue"
    subject_type: str = "Subject1"


class QueryInvoicesApiResponse(BaseModel):
    invoices: list[dict[str, Any]] = Field(default_factory=list)
    has_more: bool = False
    is_truncated: bool = False


class ConnectionStatus(BaseModel):
    status: str
    environment: str
    nip: str
    message: str = ""
    authenticated: bool = False
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class KSeFExceptionResponse(BaseModel):
    exception_code: int = Field(alias="exceptionCode")
    exception_description: str = Field(alias="exceptionDescription")
    details: str = ""

    model_config = {"populate_by_name": True}

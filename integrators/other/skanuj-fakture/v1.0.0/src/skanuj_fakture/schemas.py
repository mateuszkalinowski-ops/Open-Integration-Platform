"""Pydantic models for SkanujFakture connector — API request/response schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InvoiceType(str, Enum):
    PURCHASE = "PURCHASE"
    SELL = "SELL"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    SCANNING = "skanuje"
    TO_VERIFY = "do weryfikacji"
    SCANNED = "zeskanowany"
    EXPORTED = "wyeksportowany"


class DictionaryType(str, Enum):
    COST_TYPE = "COST_TYPE"
    COST_CENTER = "COST_CENTER"
    ATTRIBUTE = "ATTRIBUTE"


class Address(BaseModel):
    id: int | None = None
    city: dict | None = None
    community: dict | None = None
    province: dict | None = None
    voivodeship: dict | None = None
    state: dict | None = None
    post_code: dict | None = Field(default=None, alias="postCode")
    street: dict | None = None
    house_number: str | None = Field(default=None, alias="houseNumber")
    apartment_number: str | None = Field(default=None, alias="apartmentNumber")
    post: dict | None = None

    model_config = {"populate_by_name": True}


class Contractor(BaseModel):
    id: int | None = None
    name: str | None = None
    nip: str | None = None
    address: Address | None = None
    vat_payer: bool | None = Field(default=None, alias="vatPayer")
    company_entity_id: int | None = Field(default=None, alias="companyEntityId")

    model_config = {"populate_by_name": True}


class CompanyEntity(BaseModel):
    id: int | None = None
    number_scanned_documents: int | None = Field(default=None, alias="numberScannedDocuments")
    contractor_dto: Contractor | None = Field(default=None, alias="contractorDTO")
    company: dict | None = None
    status: str | None = None

    model_config = {"populate_by_name": True}


class DocumentType(BaseModel):
    id: int | None = None
    symbol: str | None = None
    name: str | None = None


class Currency(BaseModel):
    id: int | None = None
    symbol: str | None = None
    name: str | None = None


class VatRate(BaseModel):
    id: int | None = None
    symbol: str | None = None
    rate: float | None = None


class DocumentVat(BaseModel):
    id: int | None = None
    document_id: int | None = Field(default=None, alias="documentId")
    ordinal_number: int | None = Field(default=None, alias="ordinalNumber")
    is_vat: bool | None = Field(default=None, alias="isVat")
    vat_year: int | None = Field(default=None, alias="vatYear")
    vat_month: int | None = Field(default=None, alias="vatMonth")
    rate: VatRate | None = None
    net: float | None = None
    vat: float | None = None
    brutto: float | None = None
    count_vat: int | None = Field(default=None, alias="countVat")

    model_config = {"populate_by_name": True}


class DocumentItem(BaseModel):
    id: int | None = None
    ordinal_number: int | None = Field(default=None, alias="ordinalNumber")
    name: str | None = None
    units: str | None = None
    quantity: float | None = None
    net_price: float | None = Field(default=None, alias="netPrice")
    vat_rate: VatRate | None = Field(default=None, alias="vatRate")
    net: float | None = None
    vat: float | None = None
    gross: float | None = None

    model_config = {"populate_by_name": True}


class OcrField(BaseModel):
    id: int | None = None
    document_id: int | None = Field(default=None, alias="documentId")
    name: str | None = None
    pos_x: int | None = Field(default=None, alias="posX")
    pos_y: int | None = Field(default=None, alias="posY")
    height: int | None = None
    width: int | None = None
    page: int | None = None
    document_class: int | None = Field(default=None, alias="documentClass")

    model_config = {"populate_by_name": True}


class DocumentAttribute(BaseModel):
    id: int | None = None
    name: str
    value: str
    pos_x: int | None = Field(default=None, alias="posX")
    pos_y: int | None = Field(default=None, alias="posY")
    height: int | None = None
    width: int | None = None
    page: int | None = None
    document_class: int | None = Field(default=None, alias="documentClass")

    model_config = {"populate_by_name": True}


class DocumentDecret(BaseModel):
    id: int | None = None
    dict_type: str | None = Field(default=None, alias="type")
    symbol: str | None = None
    description: str | None = None
    value: str | None = None
    amount: float | None = None
    dict_item_id: int | None = Field(default=None, alias="dictItemId")
    ordinal_number: int | None = Field(default=None, alias="ordinalNumber")

    model_config = {"populate_by_name": True}


class PaymentType(BaseModel):
    id: int | None = None
    name: str | None = None


class User(BaseModel):
    id: int | None = None
    email: str | None = None
    name: str | None = None
    surname: str | None = None


class KsefData(BaseModel):
    ksef_number: str | None = Field(default=None, alias="ksefNumber")
    invoice_number: str | None = Field(default=None, alias="invoiceNumber")
    issue_date: str | None = Field(default=None, alias="issueDate")
    invoicing_date: str | None = Field(default=None, alias="invoicingDate")
    acquisition_date: str | None = Field(default=None, alias="acquisitionDate")
    seller_nip: str | None = Field(default=None, alias="sellerNip")
    seller_name: str | None = Field(default=None, alias="sellerName")
    buyer_nip: str | None = Field(default=None, alias="buyerNip")
    buyer_name: str | None = Field(default=None, alias="buyerName")
    net_amount: float | None = Field(default=None, alias="netAmount")
    gross_amount: float | None = Field(default=None, alias="grossAmount")
    vat_amount: float | None = Field(default=None, alias="vatAmount")
    currency: str | None = None
    invoicing_mode: str | None = Field(default=None, alias="invoicingMode")
    invoice_type: str | None = Field(default=None, alias="invoiceType")
    schema_system_code: str | None = Field(default=None, alias="schemaSystemCode")
    schema_version: str | None = Field(default=None, alias="schemaVersion")
    schema_value: str | None = Field(default=None, alias="schemaValue")

    model_config = {"populate_by_name": True}


class Document(BaseModel):
    id: int | None = None
    create_date: str | None = Field(default=None, alias="createDate")
    document_type: DocumentType | None = Field(default=None, alias="documentType")
    number: str | None = None
    date: str | None = None
    operation_date: str | None = Field(default=None, alias="operationDate")
    input_date: str | None = Field(default=None, alias="inputDate")
    posting_date: str | None = Field(default=None, alias="postingDate")
    payment_date: str | None = Field(default=None, alias="paymentDate")
    netto: float | None = None
    vat: float | None = None
    brutto: float | None = None
    amount_to_pay: float | None = Field(default=None, alias="amountToPay")
    contractor: Contractor | None = None
    receiver: Contractor | None = None
    company_entity: CompanyEntity | None = Field(default=None, alias="companyEntity")
    description: str | None = None
    document_status: dict | None = Field(default=None, alias="documentStatus")
    currency: Currency | None = None
    exchange: float | None = None
    exchange_date: str | None = Field(default=None, alias="exchangeDate")
    edit_user: User | None = Field(default=None, alias="editUser")
    create_user: User | None = Field(default=None, alias="createUser")
    company: dict | None = None
    scan: str | None = None
    payment_type: PaymentType | None = Field(default=None, alias="paymentType")
    attributes: list[DocumentAttribute] = Field(default_factory=list)
    decrets: list[DocumentDecret] = Field(default_factory=list)
    document_vats: list[DocumentVat] = Field(default_factory=list, alias="documentVats")
    document_items: list[DocumentItem] = Field(default_factory=list, alias="documentItems")
    ocrs: list[OcrField] = Field(default_factory=list)
    invoice_type: str | None = Field(default=None, alias="invoiceType")
    account_number: str | None = Field(default=None, alias="accountNumber")
    payments: list[dict] = Field(default_factory=list)
    ksef: KsefData | None = None

    model_config = {"populate_by_name": True}


class SimpleDocument(BaseModel):
    id: int | None = None
    create_date: str | None = Field(default=None, alias="createDate")
    document_type: DocumentType | None = Field(default=None, alias="documentType")
    number: str | None = None
    date: str | None = None

    model_config = {"populate_by_name": True}


class Company(BaseModel):
    id: int | None = None
    contractor: Contractor | None = None
    date_to: str | None = Field(default=None, alias="dateTo")
    number_scanned_documents: int | None = Field(default=None, alias="numberScannedDocuments")
    payment: dict | None = None
    last_payment: dict | None = Field(default=None, alias="lastPayment")
    email: str | None = None

    model_config = {"populate_by_name": True}


class CompanyResponse(BaseModel):
    company: Company
    is_guest: bool = Field(default=False, alias="isGuest")

    model_config = {"populate_by_name": True}


class UploadResult(BaseModel):
    documents: int = 0
    uploaded_documents: int = Field(default=0, alias="uploadedDocuments")
    documents_id_list: list[int] = Field(default_factory=list, alias="documentIdList")

    model_config = {"populate_by_name": True}


class DictionaryItem(BaseModel):
    id: int | None = None
    symbol: str
    description: str


class DictionaryItemCreate(BaseModel):
    symbol: str
    description: str


class AttributeEditRequest(BaseModel):
    status_id: int | None = Field(default=None, alias="statusId")
    attributes: list[DocumentAttribute] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class BulkEditRequest(BaseModel):
    criteria: dict = Field(default_factory=dict)
    description: str | None = None
    attribute: DocumentAttribute | None = None


class KsefSendResult(BaseModel):
    document_id: int | None = Field(default=None, alias="documentId")
    ksef_number: str | None = Field(default=None, alias="ksefNumber")

    model_config = {"populate_by_name": True}


class ConnectionStatus(BaseModel):
    account_name: str
    connected: bool = False
    companies_count: int = 0
    last_checked: datetime | None = None
    error: str | None = None


class AuthStatusResponse(BaseModel):
    account_name: str
    authenticated: bool = False
    companies: list[dict] = Field(default_factory=list)
    last_checked: datetime | None = None

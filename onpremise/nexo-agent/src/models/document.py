"""Pydantic models for InsERT Nexo documents (sales & warehouse)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    SALES_INVOICE = "sales_invoice"
    SALES_RECEIPT = "sales_receipt"
    PROFORMA = "proforma"
    CORRECTION = "correction"
    WAREHOUSE_ISSUE = "warehouse_issue"
    WAREHOUSE_RECEIPT = "warehouse_receipt"
    INTERNAL_ISSUE = "internal_issue"
    INTERNAL_RECEIPT = "internal_receipt"
    TRANSFER = "transfer"
    PURCHASE_INVOICE = "purchase_invoice"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REALIZED = "realized"


class DocumentParty(BaseModel):
    contractor_symbol: str
    role: str = "buyer"
    name: str = ""
    nip: str = ""
    address: str = ""


class DocumentPosition(BaseModel):
    product_id: int | None = None
    product_symbol: str
    product_name: str = ""
    quantity: float = 1.0
    unit: str = "szt"
    net_price: float = 0.0
    gross_price: float = 0.0
    vat_rate: str = "23%"
    discount_percent: float = 0.0
    warehouse_symbol: str = ""
    description: str = ""


class DocumentPayment(BaseModel):
    payment_form: str = "przelew"
    amount: float = 0.0
    currency: str = "PLN"
    deadline_days: int = 14
    is_paid: bool = False
    paid_amount: float = 0.0


class DocumentCreate(BaseModel):
    document_type: DocumentType
    buyer_symbol: str
    receiver_symbol: str = ""
    warehouse_symbol: str = ""
    positions: list[DocumentPosition] = Field(default_factory=list)
    payments: list[DocumentPayment] = Field(default_factory=list)
    issue_date: datetime | None = None
    sale_date: datetime | None = None
    notes: str = ""
    external_number: str = ""


class DocumentResponse(BaseModel):
    id: int
    document_type: DocumentType
    number: str
    status: DocumentStatus = DocumentStatus.DRAFT
    buyer: DocumentParty | None = None
    receiver: DocumentParty | None = None
    positions: list[DocumentPosition] = Field(default_factory=list)
    payments: list[DocumentPayment] = Field(default_factory=list)
    net_total: float = 0.0
    gross_total: float = 0.0
    vat_total: float = 0.0
    currency: str = "PLN"
    issue_date: datetime | None = None
    sale_date: datetime | None = None
    warehouse_symbol: str = ""
    notes: str = ""
    external_number: str = ""
    created_at: datetime | None = None

"""Apilo REST API Pydantic models for parsing API responses.

Covers Order, Warehouse/Product, Shipment, Finance Document, and Media APIs.
"""

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------

class ApiloListMeta(BaseModel):
    totalCount: int = 0
    currentOffset: int = 0
    pageResultCount: int = 0


class ApiloErrorResponse(BaseModel):
    message: str = ""
    code: int = 0
    description: str = ""
    errors: list[dict[str, Any]] = Field(default_factory=list)
    field: str = ""


# ---------------------------------------------------------------------------
# Orders API
# ---------------------------------------------------------------------------

class ApiloOrderAddress(BaseModel):
    id: int | None = None
    name: str = ""
    phone: str = ""
    email: str = ""
    streetName: str = ""
    streetNumber: str = ""
    city: str = ""
    zipCode: str = ""
    country: str = "PL"
    department: str = ""
    parcelIdExternal: str = ""
    parcelName: str = ""
    companyTaxNumber: str = ""
    companyName: str = ""


class ApiloOrderItem(BaseModel):
    id: int | None = None
    idExternal: str | None = None
    ean: str | None = None
    sku: str | None = None
    originalName: str = ""
    originalCode: str | None = None
    originalPriceWithTax: str = "0"
    originalPriceWithoutTax: str = "0"
    media: str | None = None
    quantity: int = 1
    tax: str | None = None
    productSet: Any = None
    status: int = 1
    unit: str | None = None
    type: int = 1
    productId: int | None = None


class ApiloOrderPayment(BaseModel):
    idExternal: str = ""
    amount: float = 0.0
    paymentDate: str | None = None
    type: int = 1
    comment: str = ""


class ApiloOrderNote(BaseModel):
    id: int | None = None
    type: int = 1
    createdAt: str = ""
    comment: str = ""


class ApiloOrder(BaseModel):
    id: str = ""
    status: int = 0
    idExternal: str | None = None
    isInvoice: bool = False
    customerLogin: str = ""
    paymentStatus: int = 0
    paymentType: int = 0
    originalCurrency: str = "PLN"
    originalAmountTotalWithoutTax: float | None = None
    originalAmountTotalWithTax: float | None = None
    originalAmountTotalPaid: float | None = None
    isEncrypted: bool = False
    createdAt: str = ""
    updatedAt: str = ""
    orderedAt: str = ""
    sendDateMin: str | None = None
    sendDateMax: str | None = None
    orderItems: list[ApiloOrderItem] = Field(default_factory=list)
    orderPayments: list[ApiloOrderPayment] = Field(default_factory=list)
    addressCustomer: ApiloOrderAddress | None = None
    addressDelivery: ApiloOrderAddress | None = None
    addressInvoice: ApiloOrderAddress | None = None
    carrierAccount: int | None = None
    orderNotes: list[ApiloOrderNote] = Field(default_factory=list)
    platformId: int | None = None
    isCanceledByBuyer: bool = False
    carrierId: int | None = None
    platformAccountId: int | None = None


class ApiloOrdersResponse(BaseModel):
    orders: list[ApiloOrder] = Field(default_factory=list)
    totalCount: int = 0
    currentOffset: int = 0
    pageResultCount: int = 0


# ---------------------------------------------------------------------------
# Warehouse / Product API
# ---------------------------------------------------------------------------

class ApiloProduct(BaseModel):
    id: int | None = None
    name: str = ""
    groupName: str = ""
    productGroupId: int | None = None
    sku: str = ""
    ean: str = ""
    originalCode: str = ""
    quantity: int = 0
    priceWithTax: float = 0.0
    priceWithoutTax: float = 0.0
    tax: str = "0"
    status: int = 1
    unit: str = ""
    weight: float | None = None
    categories: list[int] = Field(default_factory=list)
    description: str = ""
    shortDescription: str = ""


class ApiloProductsResponse(BaseModel):
    products: list[ApiloProduct] = Field(default_factory=list)
    totalCount: int = 0


class ApiloCategory(BaseModel):
    id: str = ""
    name: str = ""
    parentIds: list[int] = Field(default_factory=list)


class ApiloCategoriesResponse(BaseModel):
    categories: list[ApiloCategory] = Field(default_factory=list)
    totalCount: int = 0
    currentOffset: int = 0
    pageResultCount: int = 0


# ---------------------------------------------------------------------------
# Shipment API
# ---------------------------------------------------------------------------

class ApiloShipment(BaseModel):
    id: str = ""
    carrierAccountId: str = ""
    carrierBrokerId: str = ""
    externalId: str = ""
    orderId: str = ""
    createdAt: str = ""
    postDate: str = ""
    status: int = 0
    method: str = ""
    media: str = ""
    statusDate: str = ""
    statusDescription: str = ""
    statusCheckTimestamp: str = ""
    receivedDate: str = ""
    receivedDays: int | None = None


class ApiloShipmentsResponse(BaseModel):
    shipments: list[ApiloShipment] = Field(default_factory=list)
    totalCount: int = 0
    currentOffset: int = 0
    pageResultCount: int = 0


class ApiloOrderShipment(BaseModel):
    id: int | None = None
    idExternal: str = ""
    tracking: str = ""
    carrierProviderId: int = 0
    postDate: str = ""
    media: str = ""
    status: int = 0


# ---------------------------------------------------------------------------
# Finance Document API
# ---------------------------------------------------------------------------

class ApiloFinanceDocumentItem(BaseModel):
    id: int | None = None
    originalPriceWithTax: float = 0.0
    originalPriceWithoutTax: float = 0.0
    tax: float = 0.0
    quantity: int = 1
    originalAmountTotalWithTax: float = 0.0
    originalAmountTotalWithoutTax: float = 0.0
    originalAmountTotalTax: float = 0.0
    gtu: int | None = None
    name: str = ""
    sku: str = ""
    ean: str = ""
    unit: str = ""
    type: int = 1


class ApiloFinanceDocumentReceiver(BaseModel):
    id: int | None = None
    name: str = ""
    companyName: str = ""
    companyTaxNumber: str = ""
    streetName: str = ""
    streetNumber: str = ""
    city: str = ""
    zipCode: str = ""
    country: str = ""
    type: str = ""


class ApiloFinanceDocument(BaseModel):
    id: int | None = None
    documentNumber: str = ""
    originalAmountTotalWithTax: str = "0"
    originalAmountTotalWithoutTax: str = "0"
    originalCurrencyExchangeValue: str = "1.0000"
    originalCurrency: str = "PLN"
    currency: str = "PLN"
    createdAt: str = ""
    invoicedAt: str = ""
    soldAt: str = ""
    type: int = 0
    documentReceiver: ApiloFinanceDocumentReceiver | None = None
    documentIssuer: ApiloFinanceDocumentReceiver | None = None
    documentItems: list[ApiloFinanceDocumentItem] = Field(default_factory=list)
    paymentType: int = 0
    orderId: str = ""


class ApiloFinanceDocumentsResponse(BaseModel):
    documents: list[ApiloFinanceDocument] = Field(default_factory=list)
    totalCount: int = 0
    currentOffset: int = 0
    pageResultCount: int = 0


# ---------------------------------------------------------------------------
# Media API
# ---------------------------------------------------------------------------

class ApiloMedia(BaseModel):
    uuid: str = ""
    name: str = ""
    type: str = ""
    expiresAt: str = ""


# ---------------------------------------------------------------------------
# Order Document
# ---------------------------------------------------------------------------

class ApiloOrderDocument(BaseModel):
    id: int | None = None
    idExternal: str = ""
    number: str = ""
    priceWithTax: str = "0"
    priceWithoutTax: str = "0"
    currency: str = "PLN"
    currencyValue: str = "1.000"
    type: int = 0
    media: str = ""
    createdAt: str = ""


class ApiloOrderDocumentsResponse(BaseModel):
    documents: list[ApiloOrderDocument] = Field(default_factory=list)
    totalCount: int = 0
    currentOffset: int = 0
    pageResultCount: int = 0


# ---------------------------------------------------------------------------
# Map / Enum objects
# ---------------------------------------------------------------------------

class ApiloStatusType(BaseModel):
    id: int = 0
    key: str = ""
    name: str = ""
    description: str = ""


class ApiloTag(BaseModel):
    id: str = ""
    alias: str = ""
    name: str = ""
    color: str = ""


class ApiloOrderTag(BaseModel):
    id: str = ""
    key: str = ""
    name: str = ""
    description: str = ""


class ApiloCarrierAccount(BaseModel):
    id: str = ""
    key: str = ""
    name: str = ""
    description: str = ""

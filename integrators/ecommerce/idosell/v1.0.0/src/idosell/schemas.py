"""IdoSell Admin API Pydantic models.

Based on IdoSell REST Admin API v6/v7 response structures.
Field names follow the camelCase convention used by the API.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class IdoSellAuthStatus(BaseModel):
    account_name: str
    authenticated: bool
    api_version: str = ""


# ---------------------------------------------------------------------------
# Common response wrappers
# ---------------------------------------------------------------------------

class IdoSellError(BaseModel):
    faultCode: int = 0
    faultString: str = ""


class IdoSellPagedResponse(BaseModel):
    """Generic paged response wrapper."""
    resultsNumberAll: int = 0
    resultsNumberPage: int = 0
    resultsPage: int = 0
    resultsLimit: int = 0
    errors: IdoSellError | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Order statuses
# ---------------------------------------------------------------------------

class IdoSellOrderStatus(str, Enum):
    """IdoSell order status symbols (from Java IdoOrderStatus enum)."""
    FINISHED_EXT = "finished_ext"
    FINISHED = "finished"
    NEW = "new"
    COMPLAINED = "complainted"
    PAYMENT_WAITING = "payment_waiting"
    DELIVERY_WAITING = "delivery_waiting"
    ON_ORDER = "on_order"
    PACKED = "packed"
    PACKED_FULFILLMENT = "packed_fulfillment"
    PACKED_READY = "packed_ready"
    READY = "ready"
    RETURNED = "returned"
    WAIT_FOR_DISPATCH = "wait_for_dispatch"
    WAIT_FOR_PACKAGING = "wait_for_packaging"
    SUSPENDED = "suspended"
    JOINED = "joined"
    MISSING = "missing"
    LOST = "lost"
    FALSE = "false"
    CANCELED = "canceled"
    ALL_CANCELED = "all_canceled"
    BLOCKED = "blocked"
    HANDLED = "handled"
    WAIT_FOR_RECEIVE = "wait_for_receive"


# ---------------------------------------------------------------------------
# Order models
# ---------------------------------------------------------------------------

class IdoSellOrderClientAccount(BaseModel):
    clientId: int | None = None
    clientEmail: str = ""
    clientLogin: str = ""


class IdoSellBillingAddress(BaseModel):
    clientFirstName: str = ""
    clientLastName: str = ""
    clientFirm: str = ""
    clientStreet: str = ""
    clientZipCode: str = ""
    clientCity: str = ""
    clientCountryName: str = ""
    clientPhone1: str = ""
    clientPhone2: str = ""
    clientProvince: str = ""


class IdoSellDeliveryAddress(BaseModel):
    clientDeliveryAddressFirstName: str = ""
    clientDeliveryAddressLastName: str = ""
    clientDeliveryAddressFirm: str = ""
    clientDeliveryAddressStreet: str = ""
    clientDeliveryAddressZipCode: str = ""
    clientDeliveryAddressCity: str = ""
    clientDeliveryAddressCountry: str = ""
    clientDeliveryAddressPhone1: str = ""
    clientDeliveryAddressPhone2: str = ""
    clientDeliveryAddressProvince: str = ""


class IdoSellPickupPointAddress(BaseModel):
    pickupPointId: str = ""
    name: str = ""
    city: str = ""
    street: str = ""
    zipCode: str = ""
    description: str = ""


class IdoSellOrderClient(BaseModel):
    clientAccount: IdoSellOrderClientAccount | None = None
    clientBillingAddress: IdoSellBillingAddress | None = None
    clientDeliveryAddress: IdoSellDeliveryAddress | None = None
    clientPickupPointAddress: IdoSellPickupPointAddress | None = None


class IdoSellProductResult(BaseModel):
    productId: int | None = None
    stockId: int | None = None
    basketPosition: int | None = None
    productName: str = ""
    remarksToProduct: str = ""
    productCode: str = ""
    productQuantity: float = 0.0
    productOrderPrice: float = 0.0
    productOrderPriceNet: float = 0.0
    productOrderPriceBaseCurrency: float = 0.0
    productOrderPriceNetBaseCurrency: float = 0.0


class IdoSellOrderBaseCurrency(BaseModel):
    billingCurrency: str = ""
    orderProductsCost: float = 0.0
    orderDeliveryCost: float = 0.0
    orderDeliveryVat: float = 0.0
    orderPayformCost: float = 0.0


class IdoSellOrderCurrency(BaseModel):
    currencyId: str = ""
    orderCurrencyValue: float = 0.0
    orderProductsCost: float = 0.0
    orderDeliveryCost: float = 0.0


class IdoSellPayment(BaseModel):
    orderPaymentType: str = ""
    orderBaseCurrency: IdoSellOrderBaseCurrency | None = None
    orderCurrency: IdoSellOrderCurrency | None = None


class IdoSellOrderDispatch(BaseModel):
    courierId: int | None = None
    courierName: str = ""
    deliveryPackageId: str = ""


class IdoSellOrderPrepaid(BaseModel):
    prepaidId: int | None = None
    paymentStatus: str = ""
    paymentType: str = ""
    currencyId: str = ""
    paymentValue: float = 0.0


class IdoSellOrderStatus_(BaseModel):
    orderStatus: str = ""


class IdoSellOrderSourceDetails(BaseModel):
    orderSourceType: str = ""
    orderSourceName: str = ""
    orderSourceTypeId: int | None = None
    orderSourceId: int | None = None


class IdoSellOrderSourceResults(BaseModel):
    orderSourceType: str = ""
    shopId: int | None = None
    auctionsServiceName: str = ""
    orderSourceDetails: IdoSellOrderSourceDetails | None = None


class IdoSellOrderDetails(BaseModel):
    stockId: int | None = None
    orderNote: str = ""
    orderStatus: IdoSellOrderStatus_ | None = None
    dispatch: IdoSellOrderDispatch | None = None
    payments: IdoSellPayment | None = None
    orderSourceResults: IdoSellOrderSourceResults | None = None
    prepaids: list[IdoSellOrderPrepaid] = Field(default_factory=list)
    productsResults: list[IdoSellProductResult] = Field(default_factory=list)
    clientNoteToOrder: str = ""
    orderAddDate: str = ""
    orderChangeDate: str = ""


class IdoSellOrder(BaseModel):
    orderId: str = ""
    orderSerialNumber: int | None = None
    orderType: str = ""
    order: IdoSellOrderDetails | None = None
    client: IdoSellOrderClient | None = None
    errors: list[IdoSellError] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class IdoSellOrdersSearchResponse(BaseModel):
    resultsNumberAll: int = 0
    resultsNumberPage: int = 0
    resultsPage: int = 0
    resultsLimit: int = 0
    errors: IdoSellError | None = None
    results: list[IdoSellOrder] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Product models
# ---------------------------------------------------------------------------

class IdoSellDescriptionLangData(BaseModel):
    langId: str = ""
    productName: str = ""
    productDescription: str = ""


class IdoSellProductUnit(BaseModel):
    unitId: int = 0
    unitName: str = ""
    unitPrecision: int = 0


class IdoSellProductSizeData(BaseModel):
    sizeId: str = ""
    sizePanelName: str = ""
    productSizeCodeExternal: str = ""
    productSizeQuantity: float = 0.0


class IdoSellProductStocksQuantities(BaseModel):
    stockId: int | None = None
    productSizesData: list[IdoSellProductSizeData] = Field(default_factory=list)


class IdoSellProductStocksData(BaseModel):
    productStocksQuantities: list[IdoSellProductStocksQuantities] = Field(default_factory=list)


class IdoSellProductImage(BaseModel):
    productImageLargeUrl: str = ""
    productImageMediumUrl: str = ""
    productImageSmallUrl: str = ""


class IdoSellSizeAttribute(BaseModel):
    sizeId: str = ""
    productSizeCodeExternal: str = ""
    productSizeCodeProducer: str = ""
    productRetailPrice: float = 0.0
    productWholesalePrice: float = 0.0
    productPosPrice: float = 0.0
    productSizeWeight: int = 0


class IdoSellProduct(BaseModel):
    productId: int | None = None
    productDisplayedCode: str = ""
    productDescriptionsLangData: list[IdoSellDescriptionLangData] = Field(default_factory=list)
    categoryId: int | None = None
    categoryName: str = ""
    currencyId: str = ""
    delivererId: int | None = None
    productPosPrice: float = 0.0
    productUnit: IdoSellProductUnit | None = None
    productImages: list[IdoSellProductImage] = Field(default_factory=list)
    productSizesAttributes: list[IdoSellSizeAttribute] = Field(default_factory=list)
    productStocksData: IdoSellProductStocksData | None = None
    productAddingTime: str = ""
    productModificationTime: str = ""
    productIsDeleted: bool = False
    productIsVisible: bool = True


class IdoSellProductsSearchResponse(BaseModel):
    resultsNumberAll: int = 0
    resultsNumberPage: int = 0
    resultsPage: int = 0
    resultsLimit: int = 0
    errors: IdoSellError | None = None
    results: list[IdoSellProduct] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Order update models
# ---------------------------------------------------------------------------

class IdoSellOrderUpdateSingleResult(BaseModel):
    faultCode: int = 0
    faultString: str = ""
    orderId: list[str] = Field(default_factory=list)
    orderSerialNumber: list[str] = Field(default_factory=list)
    orderStatus: list[str] = Field(default_factory=list)


class IdoSellOrderUpdateResults(BaseModel):
    ordersResults: list[IdoSellOrderUpdateSingleResult] = Field(default_factory=list)


class IdoSellOrderUpdateResponse(BaseModel):
    errors: IdoSellError | None = None
    results: IdoSellOrderUpdateResults | None = None


# ---------------------------------------------------------------------------
# Package models
# ---------------------------------------------------------------------------

class IdoSellPackageResult(BaseModel):
    deliveryPackageId: int | None = None


class IdoSellPackageInsertResult(BaseModel):
    eventId: str = ""
    packagesResults: list[IdoSellPackageResult] = Field(default_factory=list)


class IdoSellPackageInsertResponse(BaseModel):
    errors: IdoSellError | None = None
    results: list[IdoSellPackageInsertResult] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Stock quantity update
# ---------------------------------------------------------------------------

class IdoSellStockQuantityProduct(BaseModel):
    productIndex: str = ""
    productSizeCodeExternal: str = ""
    stockId: int = 1
    productSizeQuantity: float = 0.0


class IdoSellStockQuantityResponse(BaseModel):
    errors: IdoSellError | None = None

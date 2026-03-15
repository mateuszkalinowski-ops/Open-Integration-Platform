"""Amazon SP-API Pydantic models for parsing API responses.

Covers Orders API (v0), Catalog Items API (2022-04-01), Feeds API (2021-06-30),
and Reports API (2021-06-30).
"""

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Orders API
# ---------------------------------------------------------------------------


class AmazonMoney(BaseModel):
    CurrencyCode: str = ""
    Amount: str = "0"


class AmazonAddress(BaseModel):
    Name: str = ""
    AddressLine1: str = ""
    AddressLine2: str = ""
    AddressLine3: str = ""
    City: str = ""
    County: str = ""
    District: str = ""
    StateOrRegion: str = ""
    PostalCode: str = ""
    CountryCode: str = ""
    Phone: str = ""


class AmazonOrderItem(BaseModel):
    ASIN: str = ""
    SellerSKU: str = ""
    OrderItemId: str = ""
    Title: str = ""
    QuantityOrdered: int = 0
    QuantityShipped: int = 0
    ItemPrice: AmazonMoney | None = None
    ItemTax: AmazonMoney | None = None
    ShippingPrice: AmazonMoney | None = None
    ShippingTax: AmazonMoney | None = None
    PromotionDiscount: AmazonMoney | None = None
    IsGift: bool | None = None
    ConditionId: str = ""
    ConditionSubtypeId: str = ""


class AmazonOrder(BaseModel):
    AmazonOrderId: str = ""
    SellerOrderId: str = ""
    PurchaseDate: str = ""
    LastUpdateDate: str = ""
    OrderStatus: str = ""
    FulfillmentChannel: str = ""
    SalesChannel: str = ""
    ShipServiceLevel: str = ""
    OrderTotal: AmazonMoney | None = None
    NumberOfItemsShipped: int = 0
    NumberOfItemsUnshipped: int = 0
    PaymentMethod: str = ""
    PaymentMethodDetails: list[str] = Field(default_factory=list)
    MarketplaceId: str = ""
    ShipmentServiceLevelCategory: str = ""
    OrderType: str = ""
    EarliestShipDate: str = ""
    LatestShipDate: str = ""
    EarliestDeliveryDate: str = ""
    LatestDeliveryDate: str = ""
    IsBusinessOrder: bool = False
    IsPrime: bool = False
    IsGlobalExpressEnabled: bool = False
    IsPremiumOrder: bool = False
    IsSoldByAB: bool = False
    IsISPU: bool = False
    IsAccessPointOrder: bool = False
    BuyerInfo: dict[str, Any] = Field(default_factory=dict)
    ShippingAddress: AmazonAddress | None = None
    DefaultShipFromLocationAddress: AmazonAddress | None = None


class AmazonOrdersResponse(BaseModel):
    Orders: list[AmazonOrder] = Field(default_factory=list)
    NextToken: str | None = None
    CreatedBefore: str | None = None
    LastUpdatedBefore: str | None = None


class AmazonOrderItemsResponse(BaseModel):
    OrderItems: list[AmazonOrderItem] = Field(default_factory=list)
    NextToken: str | None = None
    AmazonOrderId: str = ""


# ---------------------------------------------------------------------------
# Catalog Items API
# ---------------------------------------------------------------------------


class CatalogItemSummary(BaseModel):
    marketplaceId: str = ""
    brandName: str = ""
    itemName: str = ""
    manufacturer: str = ""
    modelNumber: str = ""


class CatalogItemImage(BaseModel):
    variant: str = ""
    link: str = ""
    height: int = 0
    width: int = 0


class CatalogItemIdentifier(BaseModel):
    identifierType: str = ""
    identifier: str = ""


class CatalogItem(BaseModel):
    asin: str = ""
    summaries: list[CatalogItemSummary] = Field(default_factory=list)
    images: list[dict[str, Any]] = Field(default_factory=list)
    identifiers: list[dict[str, Any]] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    salesRanks: list[dict[str, Any]] = Field(default_factory=list)


class CatalogSearchResponse(BaseModel):
    numberOfResults: int = 0
    items: list[CatalogItem] = Field(default_factory=list)
    pagination: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Feeds API
# ---------------------------------------------------------------------------


class AmazonFeed(BaseModel):
    feedId: str = ""
    feedType: str = ""
    marketplaceIds: list[str] = Field(default_factory=list)
    createdTime: str = ""
    processingStatus: str = ""
    processingStartTime: str = ""
    processingEndTime: str = ""
    resultFeedDocumentId: str = ""


class AmazonFeedDocument(BaseModel):
    feedDocumentId: str = ""
    url: str = ""


# ---------------------------------------------------------------------------
# Reports API
# ---------------------------------------------------------------------------


class AmazonReport(BaseModel):
    reportId: str = ""
    reportType: str = ""
    marketplaceIds: list[str] = Field(default_factory=list)
    createdTime: str = ""
    processingStatus: str = ""
    processingStartTime: str = ""
    processingEndTime: str = ""
    reportDocumentId: str = ""
    dataStartTime: str = ""
    dataEndTime: str = ""


class AmazonReportDocument(BaseModel):
    reportDocumentId: str = ""
    url: str = ""
    compressionAlgorithm: str = ""

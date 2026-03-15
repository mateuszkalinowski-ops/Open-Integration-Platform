"""Payload validators for Allegro connector actions."""

from pydantic import BaseModel, Field, field_validator

SELLING_FORMATS = {"BUY_NOW", "AUCTION", "ADVERTISEMENT"}
PUBLICATION_STATUSES = {"ACTIVE", "INACTIVE", "ENDED"}
OFFER_EVENT_TYPES = {
    "OFFER_ACTIVATED",
    "OFFER_CHANGED",
    "OFFER_ENDED",
    "OFFER_STOCK_CHANGED",
    "OFFER_PRICE_CHANGED",
    "OFFER_ARCHIVED",
    "OFFER_BID_PLACED",
    "OFFER_BID_CANCELED",
    "OFFER_TRANSLATION_UPDATED",
    "OFFER_VISIBILITY_CHANGED",
    "OFFER_DELIVERY_COUNTRIES_BLOCKED",
}
ORDER_EVENT_TYPES = {
    "BOUGHT",
    "FILLED_IN",
    "READY_FOR_PROCESSING",
    "BUYER_CANCELLED",
    "AUTO_CANCELLED",
}
ORDER_STATUSES = {
    "NEW",
    "PROCESSING",
    "READY_FOR_SHIPMENT",
    "SENT",
    "DELIVERED",
    "CANCELLED",
    "SUSPENDED",
    "RETURNED",
}
FULFILLMENT_STATUSES = {
    "NEW",
    "PROCESSING",
    "READY_FOR_SHIPMENT",
    "SENT",
    "PICKED_UP",
    "CANCELLED",
}
RETURN_STATUSES = {
    "OPEN",
    "REJECTED",
    "ACCEPTED",
    "CANCELLED",
}
WARRANTY_TYPES = {"SELLER", "MANUFACTURER"}
RETURN_COST_COVERED_BY = {"SELLER", "BUYER"}
POINT_OF_SERVICE_TYPES = {"STORE", "DEPARTMENT", "COLLECTION_POINT"}
REFUND_REASON_CODES = {
    "REFUND",
    "COMPLAINT",
    "PRODUCT_NOT_AVAILABLE",
    "PAID_VALUE_TOO_LARGE",
}


class StockSyncPayload(BaseModel):
    offer_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)


class OfferCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=75)
    selling_mode: dict
    category_id: str | None = None
    product_id: str | None = None

    @field_validator("selling_mode")
    @classmethod
    def validate_selling_mode(cls, v: dict) -> dict:
        fmt = v.get("format")
        if fmt and fmt not in SELLING_FORMATS:
            raise ValueError(f"Invalid selling format '{fmt}', must be one of: {', '.join(sorted(SELLING_FORMATS))}")
        return v


class TrackingPayload(BaseModel):
    carrier_id: str = Field(..., min_length=1)
    tracking_number: str = Field(..., min_length=1)


class InvoiceUploadPayload(BaseModel):
    invoice_base64: str = Field(..., min_length=1)
    filename: str = "invoice.pdf"
    invoice_number: str = ""


class UpdateOrderStatusPayload(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in FULFILLMENT_STATUSES:
            raise ValueError(f"Invalid status '{v}', must be one of: {', '.join(sorted(FULFILLMENT_STATUSES))}")
        return v


class RefundPayload(BaseModel):
    payment_id: str = Field(..., min_length=1)
    reason_code: str

    @field_validator("reason_code")
    @classmethod
    def validate_reason_code(cls, v: str) -> str:
        if v not in REFUND_REASON_CODES:
            raise ValueError(f"Invalid reason code '{v}', must be one of: {', '.join(sorted(REFUND_REASON_CODES))}")
        return v


class WarrantyCreatePayload(BaseModel):
    name: str = Field(..., min_length=1)
    type: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in WARRANTY_TYPES:
            raise ValueError(f"Invalid warranty type '{v}', must be one of: {', '.join(sorted(WARRANTY_TYPES))}")
        return v


class PointOfServiceCreatePayload(BaseModel):
    name: str = Field(..., min_length=1)
    type: str
    address: dict

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in POINT_OF_SERVICE_TYPES:
            raise ValueError(f"Invalid POS type '{v}', must be one of: {', '.join(sorted(POINT_OF_SERVICE_TYPES))}")
        return v


class MessageSendPayload(BaseModel):
    recipient_login: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


class TagCreatePayload(BaseModel):
    name: str = Field(..., min_length=1)
    hidden: bool = False


class ReturnRejectPayload(BaseModel):
    rejection_reason: str = Field(..., min_length=1)

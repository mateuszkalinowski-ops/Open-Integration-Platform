"""Allegro API-specific Pydantic models.

Based on Allegro REST API documentation for order events,
checkout forms, offers, and products.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# --- Enums ---


class CheckoutFormStatus(str, Enum):
    BOUGHT = "BOUGHT"
    FILLED_IN = "FILLED_IN"
    READY_FOR_PROCESSING = "READY_FOR_PROCESSING"
    CANCELLED = "CANCELLED"


class FulfillmentStatus(str, Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    READY_FOR_SHIPMENT = "READY_FOR_SHIPMENT"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    SENT = "SENT"
    PICKED_UP = "PICKED_UP"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class OrderEventType(str, Enum):
    BOUGHT = "BOUGHT"
    FILLED_IN = "FILLED_IN"
    READY_FOR_PROCESSING = "READY_FOR_PROCESSING"
    BUYER_CANCELLED = "BUYER_CANCELLED"
    FULFILLMENT_STATUS_CHANGED = "FULFILLMENT_STATUS_CHANGED"
    BUYER_MODIFIED = "BUYER_MODIFIED"
    AUTO_CANCELLED = "AUTO_CANCELLED"


PROCESSABLE_EVENT_TYPES = {
    OrderEventType.READY_FOR_PROCESSING,
    OrderEventType.BUYER_CANCELLED,
    OrderEventType.AUTO_CANCELLED,
    OrderEventType.BUYER_MODIFIED,
}


# --- Price ---


class AllegroPrice(BaseModel):
    amount: str
    currency: str = "PLN"


# --- Buyer ---


class AllegroBuyerAddress(BaseModel):
    street: str = ""
    city: str = ""
    post_code: str = Field(default="", alias="postCode")
    country_code: str = Field(default="PL", alias="countryCode")

    model_config = {"populate_by_name": True}


class AllegroBuyer(BaseModel):
    id: str
    email: str = ""
    login: str = ""
    first_name: str = Field(default="", alias="firstName")
    last_name: str = Field(default="", alias="lastName")
    company_name: str | None = Field(default=None, alias="companyName")
    guest: bool = False
    phone_number: str = Field(default="", alias="phoneNumber")
    address: AllegroBuyerAddress | None = None

    model_config = {"populate_by_name": True}


# --- Delivery ---


class AllegroDeliveryAddress(BaseModel):
    first_name: str = Field(default="", alias="firstName")
    last_name: str = Field(default="", alias="lastName")
    street: str = ""
    city: str = ""
    zip_code: str = Field(default="", alias="zipCode")
    country_code: str = Field(default="PL", alias="countryCode")
    company_name: str = Field(default="", alias="companyName")
    phone_number: str = Field(default="", alias="phoneNumber")

    model_config = {"populate_by_name": True}


class AllegroDelivery(BaseModel):
    address: AllegroDeliveryAddress | None = None
    method: dict[str, Any] | None = None
    cost: AllegroPrice | None = None
    pickup_point: dict[str, Any] | None = Field(default=None, alias="pickupPoint")

    model_config = {"populate_by_name": True}


# --- Invoice ---


class AllegroInvoiceAddress(BaseModel):
    street: str = ""
    city: str = ""
    zip_code: str = Field(default="", alias="zipCode")
    country_code: str = Field(default="PL", alias="countryCode")
    company: dict[str, Any] | None = None
    natural_person: dict[str, Any] | None = Field(default=None, alias="naturalPerson")

    model_config = {"populate_by_name": True}


class AllegroInvoice(BaseModel):
    required: bool = False
    address: AllegroInvoiceAddress | None = None


# --- Payment ---


class AllegroPayment(BaseModel):
    id: str | None = None
    type: str = ""
    paid_amount: AllegroPrice | None = Field(default=None, alias="paidAmount")

    model_config = {"populate_by_name": True}


# --- Line Items ---


class AllegroOfferRef(BaseModel):
    id: str
    name: str = ""
    external: dict[str, Any] | None = None


class AllegroLineItem(BaseModel):
    id: str
    offer: AllegroOfferRef
    quantity: int = 1
    original_price: AllegroPrice | None = Field(default=None, alias="originalPrice")
    price: AllegroPrice | None = None
    bought_at: datetime | None = Field(default=None, alias="boughtAt")

    model_config = {"populate_by_name": True}


# --- Summary ---


class AllegroSummary(BaseModel):
    total_to_pay: AllegroPrice | None = Field(default=None, alias="totalToPay")

    model_config = {"populate_by_name": True}


# --- Fulfillment ---


class AllegroFulfillment(BaseModel):
    status: FulfillmentStatus | None = None
    shipment_summary: dict[str, Any] | None = Field(default=None, alias="shipmentSummary")

    model_config = {"populate_by_name": True}


# --- Checkout Form (main order entity) ---


class AllegroCheckoutForm(BaseModel):
    id: str
    status: CheckoutFormStatus = CheckoutFormStatus.BOUGHT
    buyer: AllegroBuyer | None = None
    payment: AllegroPayment | None = None
    fulfillment: AllegroFulfillment | None = None
    delivery: AllegroDelivery | None = None
    invoice: AllegroInvoice | None = None
    line_items: list[AllegroLineItem] = Field(default_factory=list, alias="lineItems")
    summary: AllegroSummary | None = None
    updated_at: datetime | None = Field(default=None, alias="updatedAt")

    model_config = {"populate_by_name": True}


# --- Order Events ---


class AllegroOrderRef(BaseModel):
    seller: dict[str, str] | None = None
    buyer: dict[str, str] | None = None
    checkout_form: AllegroCheckoutForm | None = Field(default=None, alias="checkoutForm")

    model_config = {"populate_by_name": True}


class AllegroOrderEvent(BaseModel):
    id: str
    type: OrderEventType
    occurred_at: datetime = Field(alias="occurredAt")
    order: AllegroOrderRef | None = None

    model_config = {"populate_by_name": True}


class AllegroOrderEventsResponse(BaseModel):
    events: list[AllegroOrderEvent] = Field(default_factory=list)


# --- Offer / Product (for EAN extraction) ---


class AllegroParameter(BaseModel):
    id: str
    name: str = ""
    values: list[str] = Field(default_factory=list)
    values_ids: list[str] = Field(default_factory=list, alias="valuesIds")
    values_labels: list[str] = Field(default_factory=list, alias="valuesLabels")
    unit: str | None = None

    model_config = {"populate_by_name": True}


class AllegroProductRef(BaseModel):
    id: str | None = None


class AllegroOffer(BaseModel):
    id: str
    name: str = ""
    product: AllegroProductRef | None = None
    category: dict[str, str] | None = None
    parameters: list[AllegroParameter] = Field(default_factory=list)
    external: dict[str, Any] | None = None


class AllegroProduct(BaseModel):
    id: str
    name: str = ""
    category: dict[str, str] | None = None
    parameters: list[AllegroParameter] = Field(default_factory=list)


# --- Status update command ---


class SetFulfillmentStatusCommand(BaseModel):
    status: FulfillmentStatus


# --- Device auth ---


class AllegroDeviceCodeResponse(BaseModel):
    user_code: str = Field(alias="user_code")
    device_code: str = Field(alias="device_code")
    expires_in: int = Field(alias="expires_in")
    interval: int = 5
    verification_uri: str = Field(default="", alias="verification_uri")
    verification_uri_complete: str = Field(default="", alias="verification_uri_complete")

    model_config = {"populate_by_name": True}


class AllegroTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


class AuthStatusResponse(BaseModel):
    account_name: str
    authenticated: bool
    token_expires_at: datetime | None = None
    verification_uri: str | None = None
    user_code: str | None = None

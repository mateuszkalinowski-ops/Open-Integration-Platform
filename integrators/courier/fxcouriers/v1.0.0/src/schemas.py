"""FX Couriers (KurierSystem) — request/response schemas.

FX Couriers provides domestic and international courier services.
API uses Bearer token authentication and REST endpoints for:
- Order management (create, list, get, delete)
- Label generation (PDF)
- Shipment pickup scheduling
- Order tracking
- Service configuration

Order statuses: NEW, WAITING_APPROVAL, ACCEPTED, RUNNING, PICKUP,
                CLOSED, RETURN, PROBLEM, FAILED, CANCELLED
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


class FxCouriersCredentials(BaseModel):
    api_token: str = Field(description="Bearer API token")
    company_id: int | None = Field(default=None, description="Company ID for multi-company accounts")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OrderStatus(str, Enum):
    NEW = "NEW"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    PICKUP = "PICKUP"
    CLOSED = "CLOSED"
    RETURN = "RETURN"
    PROBLEM = "PROBLEM"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    CASH = "CASH"
    TRANSFER = "TRANSFER"


# ---------------------------------------------------------------------------
# Address DTOs
# ---------------------------------------------------------------------------


class FxAddress(BaseModel):
    name: str = Field(...)
    country: str = Field(default="PL")
    city: str = Field(...)
    postal_code: str = Field(...)
    street: str = Field(...)
    house_number: str = Field(...)
    apartment_number: str | None = Field(default=None)
    contact_person: str | None = Field(default=None)
    contact_phone: str | None = Field(default=None)
    contact_email: str | None = Field(default=None)
    services: list[FxService] | None = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Service / Additional service DTOs
# ---------------------------------------------------------------------------


class FxService(BaseModel):
    code: str = Field(...)
    value: str | None = Field(default=None)
    quantity: int = Field(default=1)


class FxAdditionalServiceConfig(BaseModel):
    id: str
    type: str
    code: str
    name: str
    value_required: int
    value_unit: str
    scope: str


# ---------------------------------------------------------------------------
# Package / Item DTOs
# ---------------------------------------------------------------------------


class FxItem(BaseModel):
    content: str = Field(default="")
    package_type: str = Field(default="BOX")
    quantity: int = Field(default=1)
    weight: float = Field(...)
    width: float | None = Field(default=None)
    height: float | None = Field(default=None)
    length: float | None = Field(default=None)
    comment: str | None = Field(default=None)
    services: list[FxService] | None = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Service configuration DTOs
# ---------------------------------------------------------------------------


class FxPackageConfig(BaseModel):
    code: str
    name: str
    description: str | None = None


class FxServiceConfig(BaseModel):
    packages: dict[str, FxPackageConfig] = Field(default_factory=dict)
    additional_services: dict[str, FxAdditionalServiceConfig] = Field(default_factory=dict)
    providers: list[str] = Field(default_factory=list)


class FxServicesResponse(BaseModel):
    service_cnt: int = 0
    service_list: dict[str, FxServiceConfig] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Order DTOs
# ---------------------------------------------------------------------------


class FxCreateOrderRequest(BaseModel):
    company_id: int
    service_code: str = Field(default="STANDARD")
    payment_method: PaymentMethod = Field(default=PaymentMethod.TRANSFER)
    comment: str | None = Field(default=None)
    sender: FxAddress
    recipient: FxAddress
    items: list[FxItem]
    services: list[FxService] | None = Field(default_factory=list)


class FxOrderResponse(BaseModel):
    order_id: int
    company_id: str | None = None
    order_number: str | None = None
    service_code: str | None = None
    tracking_number: str | None = None
    created: str | None = None
    sent: str | None = None
    received: str | None = None
    status: str | None = None
    payment_method: str | None = None
    comment: str | None = None
    tracking_url_external: str | None = None
    tracking_url_internal: str | None = None
    sender: dict | None = None
    recipient: dict | None = None
    total_price: float | None = None
    gross_price: float | None = None
    items: list[dict] | None = None
    services: list[dict] | None = None


class FxOrdersListResponse(BaseModel):
    order_cnt: int = 0
    order_list: list[FxOrderResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Shipment / Pickup DTOs
# ---------------------------------------------------------------------------


class FxCreateShipmentRequest(BaseModel):
    pickup_date: str = Field(..., description="YYYY-MM-DD")
    pickup_time_from: str = Field(..., description="HH:MM")
    pickup_time_to: str = Field(..., description="HH:MM")
    order_id_list: list[int]


# ---------------------------------------------------------------------------
# Company DTOs
# ---------------------------------------------------------------------------


class FxCompanyAddress(BaseModel):
    name: str | None = None
    country: str | None = None
    city: str | None = None
    postal_code: str | None = None
    street: str | None = None
    house_number: str | None = None
    apartment_number: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    services: list = Field(default_factory=list)


class FxCompany(BaseModel):
    company_id: int
    name: str | None = None
    short_name: str | None = None
    description: str | None = None
    taxno: str | None = None
    taxno_additional: str | None = None
    currency: str | None = None
    www: str | None = None
    is_active: bool | None = None
    address: FxCompanyAddress | None = None


# ---------------------------------------------------------------------------
# FastAPI request wrappers (with credentials)
# ---------------------------------------------------------------------------


class CreateOrderApiRequest(BaseModel):
    credentials: FxCouriersCredentials
    company_id: int
    service_code: str = Field(default="STANDARD")
    payment_method: PaymentMethod = Field(default=PaymentMethod.TRANSFER)
    comment: str | None = Field(default=None)
    sender: FxAddress
    recipient: FxAddress
    items: list[FxItem]
    services: list[FxService] | None = Field(default_factory=list)


class LabelRequest(BaseModel):
    credentials: FxCouriersCredentials
    order_id: int


class CreatePickupApiRequest(BaseModel):
    credentials: FxCouriersCredentials
    pickup_date: str = Field(..., description="YYYY-MM-DD")
    pickup_time_from: str = Field(..., description="HH:MM")
    pickup_time_to: str = Field(..., description="HH:MM")
    order_id_list: list[int]

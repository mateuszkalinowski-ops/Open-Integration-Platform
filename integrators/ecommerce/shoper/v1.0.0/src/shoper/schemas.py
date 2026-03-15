"""Shoper API Pydantic models.

Based on Shoper REST API (/webapi/rest/) response structures.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ShoperAuthResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"


class ShoperPage(BaseModel):
    count: int = 0
    pages: int = 0
    page: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list, alias="list")

    model_config = {"populate_by_name": True}


class ShoperOrderAddress(BaseModel):
    address_id: int | None = None
    order_id: int | None = None
    type: int | None = None
    firstname: str = ""
    lastname: str = ""
    company: str = ""
    tax_identification_number: str = ""
    city: str = ""
    postcode: str = ""
    street1: str = ""
    street2: str = ""
    state: str = ""
    country: str = ""
    phone: str = ""
    country_code: str = ""


class ShoperOrderStatus(BaseModel):
    status_id: int | None = None
    active: int | None = None
    color: str = ""
    type: int | None = None


class ShoperOrderAuction(BaseModel):
    auction_order_id: int | None = None
    auction_id: int | None = None
    real_auction_id: str = ""
    order_id: int | None = None
    buyer_id: int | None = None
    buyer_login: str = ""
    deal_id: str = ""


class ShoperAdditionalField(BaseModel):
    value: str = ""
    field_id: int | None = None
    type: int | None = None
    locate: int | None = None
    req: bool = False
    active: bool = False
    order: int | None = None


class ShoperOrder(BaseModel):
    order_id: int
    user_id: int | None = None
    date: datetime | None = None
    status_id: str = ""
    status: ShoperOrderStatus | None = None
    sum: float | None = None
    payment_id: int | None = None
    shipping_id: int | None = None
    shipping_cost: float | None = None
    email: str = ""
    delivery_code: str = ""
    code: str = ""
    confirm: bool = False
    notes: str = ""
    notes_priv: str = ""
    notes_pub: str = ""
    currency_id: int | None = None
    paid: float | None = None
    billing_address: ShoperOrderAddress | None = None
    delivery_address: ShoperOrderAddress | None = None
    auction: ShoperOrderAuction | None = None
    pickup_point: str = ""
    additional_fields: list[ShoperAdditionalField] = Field(default_factory=list)
    shipping_additional_fields: dict[str, str] = Field(default_factory=dict)


class ShoperOrderProduct(BaseModel):
    id: int | None = None
    order_id: int | None = None
    stock_id: int | None = None
    product_id: int | None = None
    price: float | None = None
    discount_perc: float | None = None
    quantity: float | None = None
    name: str = ""
    code: str = ""
    tax: str = ""
    tax_value: float | None = None
    unit: str = ""
    weight: float | None = None


class ShoperStock(BaseModel):
    stock_id: int | None = None
    product_id: int | None = None
    extended: bool = False
    price: float | None = None
    active: bool = True
    stock: float | None = None
    warn_level: float | None = None
    sold: float | None = None
    code: str = ""
    ean: str = ""
    weight: float | None = None


class ShoperTranslation(BaseModel):
    translation_id: int | None = None
    product_id: int | None = None
    name: str = ""
    short_description: str = ""
    description: str = ""
    active: bool = True
    isdefault: bool = False
    lang_id: int | None = None
    seo_url: str = ""


class ShoperProduct(BaseModel):
    product_id: int | None = None
    type: int | None = None
    producer_id: int | None = None
    category_id: int | None = None
    unit_id: int | None = None
    add_date: datetime | None = None
    edit_date: datetime | None = None
    code: str = ""
    ean: str = ""
    pkwiu: str = ""
    dimension_w: float | None = None
    dimension_h: float | None = None
    dimension_l: float | None = None
    vol_weight: float | None = None
    stock: ShoperStock | None = None
    translations: dict[str, ShoperTranslation] = Field(default_factory=dict)


class ShoperUser(BaseModel):
    user_id: int
    login: str = ""
    date_add: datetime | None = None
    firstname: str = ""
    lastname: str = ""
    email: str = ""
    discount: float | None = None
    active: bool = True
    comment: str = ""
    group_id: int | None = None


class ShoperParcel(BaseModel):
    parcel_id: int | None = None
    shipping_id: int | None = None
    shipping_code: str = ""


class ShoperUnit(BaseModel):
    unit_id: int
    translations: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ShoperCategory(BaseModel):
    category_id: int
    parent_id: int | None = None
    root: bool = False
    translations: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ShoperCategoryNode(BaseModel):
    id: int
    children: list["ShoperCategoryNode"] = Field(default_factory=list)


class ShoperShipping(BaseModel):
    shipping_id: int
    name: str = ""


class ShoperPayment(BaseModel):
    payment_id: int
    name: str = ""
    currencies: list[int] = Field(default_factory=list)


class ShoperCurrency(BaseModel):
    currency_id: int
    name: str = ""
    active: bool = True


class ShoperProductImage(BaseModel):
    gfx_id: int | None = None
    product_id: int | None = None
    unic_name: str = ""
    extension: str = ""


class ShoperBulkRequest(BaseModel):
    id: str
    path: str
    method: str = "GET"
    body: Any | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class ShoperBulkResponseItem(BaseModel):
    id: str
    code: int = 200
    body: ShoperPage | None = None


class ShoperBulkResponse(BaseModel):
    errors: bool = False
    items: list[ShoperBulkResponseItem] = Field(default_factory=list)


class AuthStatusResponse(BaseModel):
    account_name: str
    authenticated: bool
    token_expires_at: datetime | None = None

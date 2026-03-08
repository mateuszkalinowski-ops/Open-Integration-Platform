"""Payload validators for WooCommerce connector actions.

Each validator is a Pydantic model that enforces field types and constraints
before the request reaches the WooCommerce API. This catches malformed
payloads early and returns clear 422 errors instead of opaque upstream failures.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class OrderCreatePayload(BaseModel):
    payment_method: str | None = None
    payment_method_title: str | None = None
    set_paid: bool | None = None
    status: str | None = None
    currency: str | None = Field(None, max_length=3)
    customer_id: int | None = Field(None, ge=0)
    customer_note: str | None = None
    billing: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None
    line_items: list[dict[str, Any]] | None = None
    shipping_lines: list[dict[str, Any]] | None = None
    fee_lines: list[dict[str, Any]] | None = None
    coupon_lines: list[dict[str, Any]] | None = None
    meta_data: list[dict[str, Any]] | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {
            "pending", "processing", "on-hold", "completed",
            "cancelled", "refunded", "failed", "trash",
        }
        if v not in allowed:
            raise ValueError(f"Invalid order status '{v}', must be one of: {', '.join(sorted(allowed))}")
        return v


class OrderStatusUpdatePayload(BaseModel):
    order_id: int = Field(..., ge=1)
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {
            "pending", "processing", "on-hold", "completed",
            "cancelled", "refunded", "failed",
        }
        if v not in allowed:
            raise ValueError(f"Invalid status '{v}', must be one of: {', '.join(sorted(allowed))}")
        return v


class ProductCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    type: str | None = None
    status: str | None = None
    sku: str | None = Field(None, max_length=100)
    regular_price: str | None = None
    sale_price: str | None = None
    description: str | None = None
    short_description: str | None = None
    manage_stock: bool | None = None
    stock_quantity: int | None = None
    stock_status: str | None = None
    weight: str | None = None
    dimensions: dict[str, Any] | None = None
    categories: list[dict[str, Any]] | None = None
    tags: list[dict[str, Any]] | None = None
    images: list[dict[str, Any]] | None = None
    attributes: list[dict[str, Any]] | None = None
    meta_data: list[dict[str, Any]] | None = None
    virtual: bool | None = None
    downloadable: bool | None = None
    tax_status: str | None = None
    tax_class: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"simple", "grouped", "external", "variable"}
        if v not in allowed:
            raise ValueError(f"Invalid product type '{v}', must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"draft", "pending", "private", "publish"}
        if v not in allowed:
            raise ValueError(f"Invalid product status '{v}', must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("stock_status")
    @classmethod
    def validate_stock_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"instock", "outofstock", "onbackorder"}
        if v not in allowed:
            raise ValueError(f"Invalid stock_status '{v}', must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("regular_price", "sale_price")
    @classmethod
    def validate_price(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        try:
            float(v)
        except ValueError:
            raise ValueError(f"Price must be a numeric string, got '{v}'")
        return v


class StockSyncPayload(BaseModel):
    items: list["StockSyncItem"] = Field(..., min_length=1)


class StockSyncItem(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., ge=0)
    product_id: str = ""
    ean: str = ""
    warehouse_id: str = ""


class CustomerCreatePayload(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    first_name: str | None = Field(None, max_length=200)
    last_name: str | None = Field(None, max_length=200)
    username: str | None = Field(None, max_length=100)
    password: str | None = None
    billing: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None
    meta_data: list[dict[str, Any]] | None = None


class CouponCreatePayload(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    discount_type: str | None = None
    amount: str
    description: str | None = None
    date_expires: str | None = None
    individual_use: bool | None = None
    usage_limit: int | None = Field(None, ge=0)
    usage_limit_per_user: int | None = Field(None, ge=0)
    free_shipping: bool | None = None
    minimum_amount: str | None = None
    maximum_amount: str | None = None

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"percent", "fixed_cart", "fixed_product"}
        if v not in allowed:
            raise ValueError(f"Invalid discount_type '{v}', must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("amount", "minimum_amount", "maximum_amount")
    @classmethod
    def validate_amount(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        try:
            float(v)
        except ValueError:
            raise ValueError(f"Amount must be a numeric string, got '{v}'")
        return v


class WebhookCreatePayload(BaseModel):
    topic: str = Field(..., min_length=1)
    delivery_url: str = Field(..., min_length=10)
    name: str | None = None
    secret: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"active", "paused", "disabled"}
        if v not in allowed:
            raise ValueError(f"Invalid webhook status '{v}', must be one of: {', '.join(sorted(allowed))}")
        return v


class InvoiceUploadPayload(BaseModel):
    order_id: int = Field(..., ge=1)
    invoice_base64: str = Field(..., min_length=10)
    filename: str = Field(default="invoice.pdf", max_length=255)
    customer_note: bool = False


class BatchPayload(BaseModel):
    create: list[dict[str, Any]] | None = None
    update: list[dict[str, Any]] | None = None
    delete: list[int] | None = None

    @field_validator("delete")
    @classmethod
    def validate_delete_ids(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        for item_id in v:
            if item_id < 1:
                raise ValueError(f"Invalid ID {item_id} in delete list, must be >= 1")
        return v


StockSyncPayload.model_rebuild()

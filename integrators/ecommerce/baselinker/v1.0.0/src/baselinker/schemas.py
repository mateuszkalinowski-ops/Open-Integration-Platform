"""BaseLinker API Pydantic models.

BaseLinker uses a single POST endpoint (connector.php) with method-based dispatch.
All responses share a common wrapper: { "status": "SUCCESS"|"ERROR", ... }.
"""

from typing import Any

from pydantic import BaseModel, Field


class BLResponse(BaseModel):
    """Common BaseLinker API response wrapper."""
    status: str = ""
    error_code: str = ""
    error_message: str = ""


class BLOrderProduct(BaseModel):
    storage: str = ""
    storage_id: int = 0
    order_product_id: int = 0
    product_id: str = ""
    variant_id: int = 0
    name: str = ""
    sku: str = ""
    ean: str = ""
    location: str = ""
    warehouse_id: int = 0
    attributes: str = ""
    price_brutto: float = 0.0
    tax_rate: float = 0.0
    quantity: int = 1
    weight: float = 0.0
    bundle_id: int = 0


class BLOrder(BaseModel):
    order_id: int = 0
    shop_order_id: int = 0
    external_order_id: str = ""
    order_source: str = ""
    order_source_id: int = 0
    order_source_info: str = ""
    order_status_id: int = 0
    confirmed: bool = False
    date_add: int = 0
    date_confirmed: int = 0
    date_in_status: int = 0
    user_login: str = ""
    phone: str = ""
    email: str = ""
    user_comments: str = ""
    admin_comments: str = ""
    currency: str = "PLN"
    payment_method: str = ""
    payment_method_cod: str = ""
    payment_done: float = 0.0
    delivery_method: str = ""
    delivery_price: float = 0.0
    delivery_fullname: str = ""
    delivery_company: str = ""
    delivery_address: str = ""
    delivery_city: str = ""
    delivery_postcode: str = ""
    delivery_country_code: str = ""
    delivery_point_id: str = ""
    delivery_point_name: str = ""
    delivery_point_address: str = ""
    delivery_point_postcode: str = ""
    delivery_point_city: str = ""
    invoice_fullname: str = ""
    invoice_company: str = ""
    invoice_nip: str = ""
    invoice_address: str = ""
    invoice_city: str = ""
    invoice_postcode: str = ""
    invoice_country_code: str = ""
    want_invoice: str = ""
    extra_field_1: str = ""
    extra_field_2: str = ""
    order_page: str = ""
    pick_state: int = 0
    pack_state: int = 0
    products: list[BLOrderProduct] = Field(default_factory=list)


class BLOrdersResponse(BLResponse):
    orders: list[BLOrder] = Field(default_factory=list)


class BLOrderStatusDef(BaseModel):
    id: int = 0
    name: str = ""
    name_for_customer: str = ""
    color: str = ""


class BLOrderStatusListResponse(BLResponse):
    statuses: list[BLOrderStatusDef] = Field(default_factory=list)


class BLInventoryProduct(BaseModel):
    id: int = 0
    ean: str = ""
    sku: str = ""
    name: str = ""
    prices: dict[str, float] = Field(default_factory=dict)
    stock: dict[str, float] = Field(default_factory=dict)
    category_id: int = 0
    text_fields: dict[str, str] = Field(default_factory=dict)
    images: dict[str, str] = Field(default_factory=dict)
    weight: float = 0.0
    height: float = 0.0
    width: float = 0.0
    length: float = 0.0
    manufacturer_id: int = 0
    tax_rate: float = 0.0


class BLProductsListResponse(BLResponse):
    products: dict[str, dict[str, Any]] = Field(default_factory=dict)


class BLProductsDataResponse(BLResponse):
    products: dict[str, BLInventoryProduct] = Field(default_factory=dict)


class BLProductsStockResponse(BLResponse):
    products: dict[str, dict[str, float]] = Field(default_factory=dict)


class BLCreatePackageResponse(BLResponse):
    package_id: int = 0
    package_number: str = ""
    courier_inner_number: str = ""


class BLInventoryResponse(BLResponse):
    inventories: list[dict[str, Any]] = Field(default_factory=list)


class BLWarehouseResponse(BLResponse):
    warehouses: list[dict[str, Any]] = Field(default_factory=list)


class BLJournalEntry(BaseModel):
    order_id: int = 0
    log_type: int = 0
    log_id: int = 0
    date: int = 0
    type: int = 0
    object_id: int = 0


class BLJournalResponse(BLResponse):
    logs: list[BLJournalEntry] = Field(default_factory=list)

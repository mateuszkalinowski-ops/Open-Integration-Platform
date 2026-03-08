"""FastAPI routes for WooCommerce integrator — full REST API v3 proxy."""

import base64
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, field_validator

from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    StockItem,
)
from src.woocommerce.schemas import AuthStatusResponse
from src.api.dependencies import app_state
from src.config import WooCommerceAccountConfig

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Proxy helpers ──


async def _proxy_get(
    path: str,
    account_name: str,
    params: dict[str, Any] | None = None,
) -> Any:
    _require_auth(account_name)
    resp = await app_state.client.get(path, account_name, params=params)
    resp.raise_for_status()
    return resp.json()


async def _proxy_post(
    path: str,
    account_name: str,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    _require_auth(account_name)
    resp = await app_state.client.post(path, account_name, json_data=json_data, params=params)
    resp.raise_for_status()
    return resp.json()


async def _proxy_put(
    path: str,
    account_name: str,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    _require_auth(account_name)
    resp = await app_state.client.put(path, account_name, json_data=json_data, params=params)
    resp.raise_for_status()
    return resp.json()


async def _proxy_delete(
    path: str,
    account_name: str,
    params: dict[str, Any] | None = None,
) -> Any:
    _require_auth(account_name)
    resp = await app_state.client.delete(path, account_name, params=params)
    resp.raise_for_status()
    return resp.json()


async def _proxy_request(
    method: str,
    path: str,
    account_name: str,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    _require_auth(account_name)
    resp = await app_state.client.request(method, path, account_name, params=params, json_data=json_data)
    resp.raise_for_status()
    return resp.json()


def _strip_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


# ── Health ──


@router.get("/health")
async def health():
    if app_state.health_checker:
        return await app_state.health_checker.run()
    return {"status": "healthy"}


@router.get("/readiness")
async def readiness():
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        if result.status != "healthy":
            raise HTTPException(status_code=503, detail=result.model_dump())
        return result
    return {"status": "ready"}


# ── Auth ──


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str):
    if not app_state.auth:
        raise HTTPException(status_code=503, detail="Auth not initialized")
    return app_state.auth.get_status(account_name)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses():
    accounts = app_state.account_manager.list_accounts()
    return [app_state.auth.get_status(a.name) for a in accounts]


@router.post("/auth/{account_name}/test")
async def test_connection(account_name: str):
    _require_auth(account_name)
    try:
        result = await app_state.client.test_connection(account_name)
        return {"status": "connected", "woocommerce_version": result.get("settings", {}).get("version", "unknown")}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}") from exc


@router.get("/connection/{account_name}/status")
async def connection_status(account_name: str):
    if not app_state.auth or not app_state.auth.is_authenticated(account_name):
        return {"connected": False, "account_name": account_name}
    return {"connected": True, "account_name": account_name}


# ── Accounts ──


class AccountCreateRequest(BaseModel):
    name: str
    store_url: str
    consumer_key: str
    consumer_secret: str
    api_version: str = "wc/v3"
    verify_ssl: bool = True
    environment: str = "production"


@router.get("/accounts")
async def list_accounts():
    accounts = app_state.account_manager.list_accounts()
    return [
        {"name": a.name, "environment": a.environment, "store_url": a.store_url}
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest):
    account = WooCommerceAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    app_state.auth.register_account(
        account.name, account.store_url, account.consumer_key,
        account.consumer_secret, account.api_version,
    )
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str):
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    app_state.auth.remove_account(account_name)
    return {"status": "removed"}


# ══════════════════════════════════════════════════════════════════════
#  ORDERS
# ══════════════════════════════════════════════════════════════════════


@router.get("/orders", response_model=OrdersPage)
async def list_orders(
    account_name: str = Query(...),
    since: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: str | None = Query(None),
    customer: int | None = Query(None),
    product: int | None = Query(None),
    after: str | None = Query(None),
    before: str | None = Query(None),
):
    _require_auth(account_name)
    return await app_state.integration.fetch_orders(
        account_name, since, page, page_size, status,
        customer=customer, product=product, after=after, before=before,
    )


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, account_name: str = Query(...)):
    _require_auth(account_name)
    return await app_state.integration.get_order(account_name, order_id)


_ORDER_STATUSES = {"pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed", "trash"}
_PRODUCT_TYPES = {"simple", "grouped", "external", "variable"}
_PRODUCT_STATUSES = {"draft", "pending", "private", "publish"}
_STOCK_STATUSES = {"instock", "outofstock", "onbackorder"}
_DISCOUNT_TYPES = {"percent", "fixed_cart", "fixed_product"}
_WEBHOOK_STATUSES = {"active", "paused", "disabled"}


class OrderCreateRequest(BaseModel):
    payment_method: str | None = None
    payment_method_title: str | None = None
    set_paid: bool | None = None
    status: str | None = None
    currency: str | None = None
    customer_id: int | None = None
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
        if v is not None and v not in _ORDER_STATUSES:
            raise ValueError(f"Invalid order status '{v}', must be one of: {', '.join(sorted(_ORDER_STATUSES))}")
        return v


@router.post("/orders", status_code=201)
async def create_order(body: OrderCreateRequest, account_name: str = Query(...)):
    return await _proxy_post("orders", account_name, json_data=_strip_none(body.model_dump()))


class OrderUpdateRequest(BaseModel):
    status: str | None = None
    customer_note: str | None = None
    billing: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None
    meta_data: list[dict[str, Any]] | None = None


@router.put("/orders/{order_id}")
async def update_order(order_id: int, body: OrderUpdateRequest, account_name: str = Query(...)):
    return await _proxy_put(f"orders/{order_id}", account_name, json_data=_strip_none(body.model_dump()))


@router.delete("/orders/{order_id}")
async def delete_order(order_id: int, account_name: str = Query(...), force: bool = Query(False)):
    return await _proxy_delete(f"orders/{order_id}", account_name, params={"force": force})


class BatchRequest(BaseModel):
    create: list[dict[str, Any]] | None = None
    update: list[dict[str, Any]] | None = None
    delete: list[int] | None = None


@router.post("/orders/batch")
async def batch_orders(body: BatchRequest, account_name: str = Query(...)):
    return await _proxy_post("orders/batch", account_name, json_data=_strip_none(body.model_dump()))


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, body: UpdateStatusRequest, account_name: str = Query(...)):
    _require_auth(account_name)
    await app_state.integration.update_order_status(account_name, order_id, body.status)
    return {"status": "updated", "order_id": order_id, "new_status": body.status}


# ── Order Notes ──


@router.get("/orders/{order_id}/notes")
async def list_order_notes(
    order_id: int,
    account_name: str = Query(...),
    note_type: str | None = Query(None, alias="type"),
):
    params = _strip_none({"type": note_type})
    return await _proxy_get(f"orders/{order_id}/notes", account_name, params=params or None)


class OrderNoteRequest(BaseModel):
    note: str
    customer_note: bool = False
    added_by_user: bool = False


@router.post("/orders/{order_id}/notes", status_code=201)
async def create_order_note(order_id: int, body: OrderNoteRequest, account_name: str = Query(...)):
    return await _proxy_post(f"orders/{order_id}/notes", account_name, json_data=body.model_dump())


@router.get("/orders/{order_id}/notes/{note_id}")
async def get_order_note(order_id: int, note_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"orders/{order_id}/notes/{note_id}", account_name)


@router.delete("/orders/{order_id}/notes/{note_id}")
async def delete_order_note(order_id: int, note_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"orders/{order_id}/notes/{note_id}", account_name, params={"force": force})


# ── Order Refunds ──


@router.get("/orders/{order_id}/refunds")
async def list_order_refunds(
    order_id: int,
    account_name: str = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    return await _proxy_get(f"orders/{order_id}/refunds", account_name, params={"page": page, "per_page": per_page})


class RefundRequest(BaseModel):
    amount: str | None = None
    reason: str | None = None
    refunded_by: int | None = None
    line_items: list[dict[str, Any]] | None = None
    api_refund: bool = True
    api_restock: bool = True


@router.post("/orders/{order_id}/refunds", status_code=201)
async def create_order_refund(order_id: int, body: RefundRequest, account_name: str = Query(...)):
    return await _proxy_post(f"orders/{order_id}/refunds", account_name, json_data=_strip_none(body.model_dump()))


@router.get("/orders/{order_id}/refunds/{refund_id}")
async def get_order_refund(order_id: int, refund_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"orders/{order_id}/refunds/{refund_id}", account_name)


@router.delete("/orders/{order_id}/refunds/{refund_id}")
async def delete_order_refund(order_id: int, refund_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"orders/{order_id}/refunds/{refund_id}", account_name, params={"force": force})


# ── Invoice ──


class InvoiceUploadJsonRequest(BaseModel):
    invoice_base64: str
    filename: str = "invoice.pdf"
    customer_note: bool = False


@router.put("/orders/{order_id}/invoice")
async def upload_invoice_multipart(
    order_id: str,
    account_name: str = Query(...),
    file: UploadFile = File(...),
    customer_note: bool = Query(False),
):
    _require_auth(account_name)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Invoice file exceeds 10 MB limit")
    result = await app_state.integration.upload_invoice(
        account_name, order_id, contents, file.filename or "invoice.pdf", customer_note,
    )
    return {"status": "uploaded", "order_id": order_id, **result}


@router.post("/orders/{order_id}/invoice")
async def upload_invoice_json(order_id: str, body: InvoiceUploadJsonRequest, account_name: str = Query(...)):
    _require_auth(account_name)
    try:
        contents = base64.b64decode(body.invoice_base64)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {exc}") from exc
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Invoice file exceeds 10 MB limit")
    result = await app_state.integration.upload_invoice(
        account_name, order_id, contents, body.filename, body.customer_note,
    )
    return {"status": "uploaded", "order_id": order_id, **result}


# ══════════════════════════════════════════════════════════════════════
#  PRODUCTS
# ══════════════════════════════════════════════════════════════════════


@router.get("/products")
async def list_products(
    account_name: str = Query(...),
    search: str | None = Query(None),
    sku: str | None = Query(None),
    status: str | None = Query(None),
    product_type: str | None = Query(None, alias="type"),
    category: str | None = Query(None),
    tag: str | None = Query(None),
    featured: bool | None = Query(None),
    on_sale: bool | None = Query(None),
    stock_status: str | None = Query(None),
    after: str | None = Query(None),
    before: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    orderby: str | None = Query(None),
    order: str | None = Query(None),
):
    params = _strip_none({
        "search": search, "sku": sku, "status": status, "type": product_type,
        "category": category, "tag": tag, "featured": featured, "on_sale": on_sale,
        "stock_status": stock_status, "after": after, "before": before,
        "page": page, "per_page": per_page, "orderby": orderby, "order": order,
    })
    return await _proxy_get("products", account_name, params=params)


@router.get("/products/search")
async def search_products(
    query: str = Query(""),
    account_name: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    _require_auth(account_name)
    return await app_state.integration.search_products(account_name, query, page, page_size)


@router.get("/products/{product_id}")
async def get_product(product_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/{product_id}", account_name)


class ProductCreateRequest(BaseModel):
    name: str
    type: str | None = None
    status: str | None = None
    sku: str | None = None
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
        if v is not None and v not in _PRODUCT_TYPES:
            raise ValueError(f"Invalid product type '{v}', must be one of: {', '.join(sorted(_PRODUCT_TYPES))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in _PRODUCT_STATUSES:
            raise ValueError(f"Invalid product status '{v}', must be one of: {', '.join(sorted(_PRODUCT_STATUSES))}")
        return v

    @field_validator("stock_status")
    @classmethod
    def validate_stock_status(cls, v: str | None) -> str | None:
        if v is not None and v not in _STOCK_STATUSES:
            raise ValueError(f"Invalid stock_status '{v}', must be one of: {', '.join(sorted(_STOCK_STATUSES))}")
        return v

    @field_validator("regular_price", "sale_price")
    @classmethod
    def validate_price(cls, v: str | None) -> str | None:
        if v is not None and v != "":
            try:
                float(v)
            except ValueError:
                raise ValueError(f"Price must be a numeric string, got '{v}'")
        return v


@router.post("/products", status_code=201)
async def create_product(body: ProductCreateRequest, account_name: str = Query(...)):
    return await _proxy_post("products", account_name, json_data=_strip_none(body.model_dump()))


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    sku: str | None = None
    regular_price: str | None = None
    sale_price: str | None = None
    status: str | None = None
    description: str | None = None
    short_description: str | None = None
    manage_stock: bool | None = None
    stock_quantity: int | None = None
    stock_status: str | None = None
    weight: str | None = None
    categories: list[dict[str, Any]] | None = None
    tags: list[dict[str, Any]] | None = None
    images: list[dict[str, Any]] | None = None
    meta_data: list[dict[str, Any]] | None = None


@router.put("/products/{product_id}")
async def update_product(product_id: int, body: ProductUpdateRequest, account_name: str = Query(...)):
    return await _proxy_put(f"products/{product_id}", account_name, json_data=_strip_none(body.model_dump()))


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, account_name: str = Query(...), force: bool = Query(False)):
    return await _proxy_delete(f"products/{product_id}", account_name, params={"force": force})


@router.post("/products/batch")
async def batch_products(body: BatchRequest, account_name: str = Query(...)):
    return await _proxy_post("products/batch", account_name, json_data=_strip_none(body.model_dump()))


@router.post("/products/{product_id}/duplicate", status_code=201)
async def duplicate_product(product_id: int, account_name: str = Query(...)):
    return await _proxy_post(f"products/{product_id}/duplicate", account_name)


class ProductSyncRequest(BaseModel):
    products: list[Product]


@router.post("/products/sync")
async def sync_products(body: ProductSyncRequest, account_name: str = Query(...)):
    _require_auth(account_name)
    result = await app_state.integration.sync_products(account_name, body.products)
    return result.model_dump()


# ── Product Variations ──


@router.get("/products/{product_id}/variations")
async def list_variations(
    product_id: int,
    account_name: str = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    return await _proxy_get(f"products/{product_id}/variations", account_name, params={"page": page, "per_page": per_page})


@router.get("/products/{product_id}/variations/{variation_id}")
async def get_variation(product_id: int, variation_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/{product_id}/variations/{variation_id}", account_name)


@router.post("/products/{product_id}/variations", status_code=201)
async def create_variation(product_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post(f"products/{product_id}/variations", account_name, json_data=body)


@router.put("/products/{product_id}/variations/{variation_id}")
async def update_variation(product_id: int, variation_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"products/{product_id}/variations/{variation_id}", account_name, json_data=body)


@router.delete("/products/{product_id}/variations/{variation_id}")
async def delete_variation(product_id: int, variation_id: int, account_name: str = Query(...), force: bool = Query(False)):
    return await _proxy_delete(f"products/{product_id}/variations/{variation_id}", account_name, params={"force": force})


@router.post("/products/{product_id}/variations/batch")
async def batch_variations(product_id: int, body: BatchRequest, account_name: str = Query(...)):
    return await _proxy_post(f"products/{product_id}/variations/batch", account_name, json_data=_strip_none(body.model_dump()))


# ── Product Attributes ──


@router.get("/products/attributes")
async def list_product_attributes(account_name: str = Query(...)):
    return await _proxy_get("products/attributes", account_name)


@router.get("/products/attributes/{attribute_id}")
async def get_product_attribute(attribute_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/attributes/{attribute_id}", account_name)


class AttributeRequest(BaseModel):
    name: str
    slug: str | None = None
    type: str | None = None
    order_by: str | None = None
    has_archives: bool | None = None


@router.post("/products/attributes", status_code=201)
async def create_product_attribute(body: AttributeRequest, account_name: str = Query(...)):
    return await _proxy_post("products/attributes", account_name, json_data=_strip_none(body.model_dump()))


@router.put("/products/attributes/{attribute_id}")
async def update_product_attribute(attribute_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"products/attributes/{attribute_id}", account_name, json_data=body)


@router.delete("/products/attributes/{attribute_id}")
async def delete_product_attribute(attribute_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"products/attributes/{attribute_id}", account_name, params={"force": force})


# ── Attribute Terms ──


@router.get("/products/attributes/{attribute_id}/terms")
async def list_attribute_terms(attribute_id: int, account_name: str = Query(...), page: int = Query(1), per_page: int = Query(50)):
    return await _proxy_get(f"products/attributes/{attribute_id}/terms", account_name, params={"page": page, "per_page": per_page})


@router.get("/products/attributes/{attribute_id}/terms/{term_id}")
async def get_attribute_term(attribute_id: int, term_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/attributes/{attribute_id}/terms/{term_id}", account_name)


@router.post("/products/attributes/{attribute_id}/terms", status_code=201)
async def create_attribute_term(attribute_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post(f"products/attributes/{attribute_id}/terms", account_name, json_data=body)


@router.put("/products/attributes/{attribute_id}/terms/{term_id}")
async def update_attribute_term(attribute_id: int, term_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"products/attributes/{attribute_id}/terms/{term_id}", account_name, json_data=body)


@router.delete("/products/attributes/{attribute_id}/terms/{term_id}")
async def delete_attribute_term(attribute_id: int, term_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"products/attributes/{attribute_id}/terms/{term_id}", account_name, params={"force": force})


# ── Product Categories ──


@router.get("/products/categories")
async def list_product_categories(
    account_name: str = Query(...),
    search: str | None = Query(None),
    parent: int | None = Query(None),
    hide_empty: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    params = _strip_none({"search": search, "parent": parent, "hide_empty": hide_empty, "page": page, "per_page": per_page})
    return await _proxy_get("products/categories", account_name, params=params)


@router.get("/products/categories/{category_id}")
async def get_product_category(category_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/categories/{category_id}", account_name)


class CategoryRequest(BaseModel):
    name: str
    slug: str | None = None
    parent: int | None = None
    description: str | None = None
    display: str | None = None
    image: dict[str, Any] | None = None


@router.post("/products/categories", status_code=201)
async def create_product_category(body: CategoryRequest, account_name: str = Query(...)):
    return await _proxy_post("products/categories", account_name, json_data=_strip_none(body.model_dump()))


@router.put("/products/categories/{category_id}")
async def update_product_category(category_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"products/categories/{category_id}", account_name, json_data=body)


@router.delete("/products/categories/{category_id}")
async def delete_product_category(category_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"products/categories/{category_id}", account_name, params={"force": force})


# ── Product Tags ──


@router.get("/products/tags")
async def list_product_tags(
    account_name: str = Query(...),
    search: str | None = Query(None),
    hide_empty: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    params = _strip_none({"search": search, "hide_empty": hide_empty, "page": page, "per_page": per_page})
    return await _proxy_get("products/tags", account_name, params=params)


@router.get("/products/tags/{tag_id}")
async def get_product_tag(tag_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/tags/{tag_id}", account_name)


@router.post("/products/tags", status_code=201)
async def create_product_tag(body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post("products/tags", account_name, json_data=body)


@router.put("/products/tags/{tag_id}")
async def update_product_tag(tag_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"products/tags/{tag_id}", account_name, json_data=body)


@router.delete("/products/tags/{tag_id}")
async def delete_product_tag(tag_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"products/tags/{tag_id}", account_name, params={"force": force})


# ── Product Reviews ──


@router.get("/products/reviews")
async def list_product_reviews(
    account_name: str = Query(...),
    product: list[int] | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    params = _strip_none({"status": status, "page": page, "per_page": per_page})
    if product:
        params["product"] = product
    return await _proxy_get("products/reviews", account_name, params=params)


@router.get("/products/reviews/{review_id}")
async def get_product_review(review_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/reviews/{review_id}", account_name)


class ReviewRequest(BaseModel):
    product_id: int
    review: str
    reviewer: str
    reviewer_email: str
    rating: int | None = None
    status: str | None = None


@router.post("/products/reviews", status_code=201)
async def create_product_review(body: ReviewRequest, account_name: str = Query(...)):
    return await _proxy_post("products/reviews", account_name, json_data=_strip_none(body.model_dump()))


@router.put("/products/reviews/{review_id}")
async def update_product_review(review_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"products/reviews/{review_id}", account_name, json_data=body)


@router.delete("/products/reviews/{review_id}")
async def delete_product_review(review_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"products/reviews/{review_id}", account_name, params={"force": force})


# ── Product Shipping Classes ──


@router.get("/products/shipping_classes")
async def list_shipping_classes(account_name: str = Query(...), page: int = Query(1), per_page: int = Query(50)):
    return await _proxy_get("products/shipping_classes", account_name, params={"page": page, "per_page": per_page})


@router.get("/products/shipping_classes/{shipping_class_id}")
async def get_shipping_class(shipping_class_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"products/shipping_classes/{shipping_class_id}", account_name)


@router.post("/products/shipping_classes", status_code=201)
async def create_shipping_class(body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post("products/shipping_classes", account_name, json_data=body)


@router.put("/products/shipping_classes/{shipping_class_id}")
async def update_shipping_class(shipping_class_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"products/shipping_classes/{shipping_class_id}", account_name, json_data=body)


@router.delete("/products/shipping_classes/{shipping_class_id}")
async def delete_shipping_class(shipping_class_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"products/shipping_classes/{shipping_class_id}", account_name, params={"force": force})


# ══════════════════════════════════════════════════════════════════════
#  STOCK
# ══════════════════════════════════════════════════════════════════════


class StockSyncRequest(BaseModel):
    items: list[StockItem]


@router.post("/stock/sync")
async def sync_stock(body: StockSyncRequest, account_name: str = Query(...)):
    _require_auth(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


# ══════════════════════════════════════════════════════════════════════
#  CUSTOMERS
# ══════════════════════════════════════════════════════════════════════


@router.get("/customers")
async def list_customers(
    account_name: str = Query(...),
    search: str | None = Query(None),
    email: str | None = Query(None),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    orderby: str | None = Query(None),
    order: str | None = Query(None),
):
    params = _strip_none({
        "search": search, "email": email, "role": role,
        "page": page, "per_page": per_page, "orderby": orderby, "order": order,
    })
    return await _proxy_get("customers", account_name, params=params)


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"customers/{customer_id}", account_name)


class CustomerCreateRequest(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    password: str | None = None
    billing: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None
    meta_data: list[dict[str, Any]] | None = None


@router.post("/customers", status_code=201)
async def create_customer(body: CustomerCreateRequest, account_name: str = Query(...)):
    return await _proxy_post("customers", account_name, json_data=_strip_none(body.model_dump()))


class CustomerUpdateRequest(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    billing: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None
    meta_data: list[dict[str, Any]] | None = None


@router.put("/customers/{customer_id}")
async def update_customer(customer_id: int, body: CustomerUpdateRequest, account_name: str = Query(...)):
    return await _proxy_put(f"customers/{customer_id}", account_name, json_data=_strip_none(body.model_dump()))


@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int, account_name: str = Query(...), force: bool = Query(True), reassign: int | None = Query(None)):
    params = _strip_none({"force": force, "reassign": reassign})
    return await _proxy_delete(f"customers/{customer_id}", account_name, params=params)


@router.post("/customers/batch")
async def batch_customers(body: BatchRequest, account_name: str = Query(...)):
    return await _proxy_post("customers/batch", account_name, json_data=_strip_none(body.model_dump()))


@router.get("/customers/{customer_id}/downloads")
async def list_customer_downloads(customer_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"customers/{customer_id}/downloads", account_name)


# ══════════════════════════════════════════════════════════════════════
#  COUPONS
# ══════════════════════════════════════════════════════════════════════


@router.get("/coupons")
async def list_coupons(
    account_name: str = Query(...),
    search: str | None = Query(None),
    code: str | None = Query(None),
    after: str | None = Query(None),
    before: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    params = _strip_none({"search": search, "code": code, "after": after, "before": before, "page": page, "per_page": per_page})
    return await _proxy_get("coupons", account_name, params=params)


@router.get("/coupons/{coupon_id}")
async def get_coupon(coupon_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"coupons/{coupon_id}", account_name)


class CouponCreateRequest(BaseModel):
    code: str
    discount_type: str | None = None
    amount: str
    description: str | None = None
    date_expires: str | None = None
    individual_use: bool | None = None
    product_ids: list[int] | None = None
    excluded_product_ids: list[int] | None = None
    usage_limit: int | None = None
    usage_limit_per_user: int | None = None
    limit_usage_to_x_items: int | None = None
    free_shipping: bool | None = None
    product_categories: list[int] | None = None
    excluded_product_categories: list[int] | None = None
    minimum_amount: str | None = None
    maximum_amount: str | None = None
    email_restrictions: list[str] | None = None
    meta_data: list[dict[str, Any]] | None = None

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, v: str | None) -> str | None:
        if v is not None and v not in _DISCOUNT_TYPES:
            raise ValueError(f"Invalid discount_type '{v}', must be one of: {', '.join(sorted(_DISCOUNT_TYPES))}")
        return v

    @field_validator("amount", "minimum_amount", "maximum_amount")
    @classmethod
    def validate_amount(cls, v: str | None) -> str | None:
        if v is not None and v != "":
            try:
                float(v)
            except ValueError:
                raise ValueError(f"Amount must be a numeric string, got '{v}'")
        return v


@router.post("/coupons", status_code=201)
async def create_coupon(body: CouponCreateRequest, account_name: str = Query(...)):
    return await _proxy_post("coupons", account_name, json_data=_strip_none(body.model_dump()))


@router.put("/coupons/{coupon_id}")
async def update_coupon(coupon_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"coupons/{coupon_id}", account_name, json_data=body)


@router.delete("/coupons/{coupon_id}")
async def delete_coupon(coupon_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"coupons/{coupon_id}", account_name, params={"force": force})


@router.post("/coupons/batch")
async def batch_coupons(body: BatchRequest, account_name: str = Query(...)):
    return await _proxy_post("coupons/batch", account_name, json_data=_strip_none(body.model_dump()))


# ══════════════════════════════════════════════════════════════════════
#  TAX RATES
# ══════════════════════════════════════════════════════════════════════


@router.get("/taxes")
async def list_tax_rates(
    account_name: str = Query(...),
    tax_class: str | None = Query(None, alias="class"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    params = _strip_none({"class": tax_class, "page": page, "per_page": per_page})
    return await _proxy_get("taxes", account_name, params=params)


@router.get("/taxes/{tax_id}")
async def get_tax_rate(tax_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"taxes/{tax_id}", account_name)


@router.post("/taxes", status_code=201)
async def create_tax_rate(body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post("taxes", account_name, json_data=body)


@router.put("/taxes/{tax_id}")
async def update_tax_rate(tax_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"taxes/{tax_id}", account_name, json_data=body)


@router.delete("/taxes/{tax_id}")
async def delete_tax_rate(tax_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"taxes/{tax_id}", account_name, params={"force": force})


@router.post("/taxes/batch")
async def batch_tax_rates(body: BatchRequest, account_name: str = Query(...)):
    return await _proxy_post("taxes/batch", account_name, json_data=_strip_none(body.model_dump()))


# ── Tax Classes ──


@router.get("/taxes/classes")
async def list_tax_classes(account_name: str = Query(...)):
    return await _proxy_get("taxes/classes", account_name)


@router.post("/taxes/classes", status_code=201)
async def create_tax_class(body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post("taxes/classes", account_name, json_data=body)


@router.delete("/taxes/classes/{slug}")
async def delete_tax_class(slug: str, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"taxes/classes/{slug}", account_name, params={"force": force})


# ══════════════════════════════════════════════════════════════════════
#  REPORTS
# ══════════════════════════════════════════════════════════════════════


@router.get("/reports")
async def list_reports(account_name: str = Query(...)):
    return await _proxy_get("reports", account_name)


@router.get("/reports/sales")
async def get_sales_report(
    account_name: str = Query(...),
    date_min: str | None = Query(None),
    date_max: str | None = Query(None),
    period: str | None = Query(None),
):
    params = _strip_none({"date_min": date_min, "date_max": date_max, "period": period})
    return await _proxy_get("reports/sales", account_name, params=params or None)


@router.get("/reports/top_sellers")
async def get_top_sellers_report(
    account_name: str = Query(...),
    date_min: str | None = Query(None),
    date_max: str | None = Query(None),
    period: str | None = Query(None),
):
    params = _strip_none({"date_min": date_min, "date_max": date_max, "period": period})
    return await _proxy_get("reports/top_sellers", account_name, params=params or None)


@router.get("/reports/coupons/totals")
async def get_coupons_totals(account_name: str = Query(...)):
    return await _proxy_get("reports/coupons/totals", account_name)


@router.get("/reports/customers/totals")
async def get_customers_totals(account_name: str = Query(...)):
    return await _proxy_get("reports/customers/totals", account_name)


@router.get("/reports/orders/totals")
async def get_orders_totals(account_name: str = Query(...)):
    return await _proxy_get("reports/orders/totals", account_name)


@router.get("/reports/products/totals")
async def get_products_totals(account_name: str = Query(...)):
    return await _proxy_get("reports/products/totals", account_name)


@router.get("/reports/reviews/totals")
async def get_reviews_totals(account_name: str = Query(...)):
    return await _proxy_get("reports/reviews/totals", account_name)


# ══════════════════════════════════════════════════════════════════════
#  WEBHOOKS
# ══════════════════════════════════════════════════════════════════════


@router.get("/webhooks")
async def list_webhooks(
    account_name: str = Query(...),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    params = _strip_none({"status": status, "page": page, "per_page": per_page})
    return await _proxy_get("webhooks", account_name, params=params)


@router.get("/webhooks/{webhook_id}")
async def get_webhook(webhook_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"webhooks/{webhook_id}", account_name)


class WebhookCreateRequest(BaseModel):
    name: str | None = None
    topic: str
    delivery_url: str
    secret: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in _WEBHOOK_STATUSES:
            raise ValueError(f"Invalid webhook status '{v}', must be one of: {', '.join(sorted(_WEBHOOK_STATUSES))}")
        return v


@router.post("/webhooks", status_code=201)
async def create_webhook(body: WebhookCreateRequest, account_name: str = Query(...)):
    return await _proxy_post("webhooks", account_name, json_data=_strip_none(body.model_dump()))


@router.put("/webhooks/{webhook_id}")
async def update_webhook(webhook_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"webhooks/{webhook_id}", account_name, json_data=body)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"webhooks/{webhook_id}", account_name, params={"force": force})


@router.post("/webhooks/batch")
async def batch_webhooks(body: BatchRequest, account_name: str = Query(...)):
    return await _proxy_post("webhooks/batch", account_name, json_data=_strip_none(body.model_dump()))


# ══════════════════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════════════════


@router.get("/settings")
async def list_settings_groups(account_name: str = Query(...)):
    return await _proxy_get("settings", account_name)


@router.get("/settings/{group_id}")
async def list_settings_options(group_id: str, account_name: str = Query(...)):
    return await _proxy_get(f"settings/{group_id}", account_name)


@router.get("/settings/{group_id}/{option_id}")
async def get_setting_option(group_id: str, option_id: str, account_name: str = Query(...)):
    return await _proxy_get(f"settings/{group_id}/{option_id}", account_name)


@router.put("/settings/{group_id}/{option_id}")
async def update_setting_option(group_id: str, option_id: str, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"settings/{group_id}/{option_id}", account_name, json_data=body)


# ══════════════════════════════════════════════════════════════════════
#  PAYMENT GATEWAYS
# ══════════════════════════════════════════════════════════════════════


@router.get("/payment_gateways")
async def list_payment_gateways(account_name: str = Query(...)):
    return await _proxy_get("payment_gateways", account_name)


@router.get("/payment_gateways/{gateway_id}")
async def get_payment_gateway(gateway_id: str, account_name: str = Query(...)):
    return await _proxy_get(f"payment_gateways/{gateway_id}", account_name)


@router.put("/payment_gateways/{gateway_id}")
async def update_payment_gateway(gateway_id: str, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"payment_gateways/{gateway_id}", account_name, json_data=body)


# ══════════════════════════════════════════════════════════════════════
#  SHIPPING ZONES
# ══════════════════════════════════════════════════════════════════════


@router.get("/shipping/zones")
async def list_shipping_zones(account_name: str = Query(...)):
    return await _proxy_get("shipping/zones", account_name)


@router.get("/shipping/zones/{zone_id}")
async def get_shipping_zone(zone_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"shipping/zones/{zone_id}", account_name)


@router.post("/shipping/zones", status_code=201)
async def create_shipping_zone(body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post("shipping/zones", account_name, json_data=body)


@router.put("/shipping/zones/{zone_id}")
async def update_shipping_zone(zone_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"shipping/zones/{zone_id}", account_name, json_data=body)


@router.delete("/shipping/zones/{zone_id}")
async def delete_shipping_zone(zone_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"shipping/zones/{zone_id}", account_name, params={"force": force})


# ── Zone Locations ──


@router.get("/shipping/zones/{zone_id}/locations")
async def list_zone_locations(zone_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"shipping/zones/{zone_id}/locations", account_name)


@router.put("/shipping/zones/{zone_id}/locations")
async def update_zone_locations(zone_id: int, body: list[dict[str, Any]], account_name: str = Query(...)):
    _require_auth(account_name)
    resp = await app_state.client.put(f"shipping/zones/{zone_id}/locations", account_name, json_data=body)
    resp.raise_for_status()
    return resp.json()


# ── Zone Methods ──


@router.get("/shipping/zones/{zone_id}/methods")
async def list_zone_methods(zone_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"shipping/zones/{zone_id}/methods", account_name)


@router.get("/shipping/zones/{zone_id}/methods/{instance_id}")
async def get_zone_method(zone_id: int, instance_id: int, account_name: str = Query(...)):
    return await _proxy_get(f"shipping/zones/{zone_id}/methods/{instance_id}", account_name)


@router.post("/shipping/zones/{zone_id}/methods", status_code=201)
async def create_zone_method(zone_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_post(f"shipping/zones/{zone_id}/methods", account_name, json_data=body)


@router.put("/shipping/zones/{zone_id}/methods/{instance_id}")
async def update_zone_method(zone_id: int, instance_id: int, body: dict[str, Any], account_name: str = Query(...)):
    return await _proxy_put(f"shipping/zones/{zone_id}/methods/{instance_id}", account_name, json_data=body)


@router.delete("/shipping/zones/{zone_id}/methods/{instance_id}")
async def delete_zone_method(zone_id: int, instance_id: int, account_name: str = Query(...), force: bool = Query(True)):
    return await _proxy_delete(f"shipping/zones/{zone_id}/methods/{instance_id}", account_name, params={"force": force})


# ── Shipping Methods ──


@router.get("/shipping_methods")
async def list_shipping_methods(account_name: str = Query(...)):
    return await _proxy_get("shipping_methods", account_name)


# ══════════════════════════════════════════════════════════════════════
#  SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════


@router.get("/system_status")
async def get_system_status(account_name: str = Query(...)):
    return await _proxy_get("system_status", account_name)


@router.get("/system_status/tools")
async def list_system_status_tools(account_name: str = Query(...)):
    return await _proxy_get("system_status/tools", account_name)


@router.get("/system_status/tools/{tool_id}")
async def get_system_status_tool(tool_id: str, account_name: str = Query(...)):
    return await _proxy_get(f"system_status/tools/{tool_id}", account_name)


@router.put("/system_status/tools/{tool_id}")
async def run_system_status_tool(tool_id: str, account_name: str = Query(...)):
    return await _proxy_put(f"system_status/tools/{tool_id}", account_name, json_data={})


# ── Helpers ──


def _require_auth(account_name: str) -> None:
    if not app_state.auth or not app_state.auth.is_authenticated(account_name):
        raise HTTPException(
            status_code=401,
            detail=f"Account '{account_name}' not configured. Add it via POST /accounts first.",
        )

"""FastAPI routes for Allegro integrator."""

import base64
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    StockItem,
)
from pydantic import BaseModel

from src.allegro.schemas import AuthStatusResponse
from src.api.dependencies import app_state
from src.config import AllegroAccountConfig

router = APIRouter()


# ── Health ──────────────────────────────────────────────────────────


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


# ── Auth ────────────────────────────────────────────────────────────


@router.post("/auth/{account_name}/device-code", response_model=dict)
async def start_device_flow(account_name: str):
    """Start OAuth2 device flow for a specific account."""
    account = app_state.account_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")

    device_code = await app_state.auth_manager.start_device_flow(
        account.name,
        account.client_id,
        account.auth_url,
    )
    return {
        "user_code": device_code.user_code,
        "verification_uri": device_code.verification_uri,
        "verification_uri_complete": device_code.verification_uri_complete,
        "expires_in": device_code.expires_in,
        "message": f"Go to {device_code.verification_uri_complete} and enter code {device_code.user_code}",
    }


@router.post("/auth/{account_name}/poll-token")
async def poll_for_token(account_name: str, background_tasks: BackgroundTasks):
    """Poll for token after user has authorized the device code."""
    account = app_state.account_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")

    try:
        token = await app_state.auth_manager.poll_for_token(
            account.name,
            account.client_id,
            account.client_secret,
            account.auth_url,
        )
        return {"status": "authenticated", "expires_in": token.expires_in}
    except TimeoutError as exc:
        raise HTTPException(status_code=408, detail="Device flow timed out. Start again.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str):
    return app_state.auth_manager.get_status(account_name)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses():
    accounts = app_state.account_manager.list_accounts()
    return [app_state.auth_manager.get_status(a.name) for a in accounts]


# ── Accounts ────────────────────────────────────────────────────────


class AccountCreateRequest(BaseModel):
    name: str
    client_id: str
    client_secret: str
    api_url: str = "https://api.allegro.pl"
    auth_url: str = "https://allegro.pl/auth/oauth"
    environment: str = "production"


@router.get("/accounts")
async def list_accounts():
    accounts = app_state.account_manager.list_accounts()
    return [{"name": a.name, "environment": a.environment, "api_url": a.api_url} for a in accounts]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest):
    account = AllegroAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str):
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return {"status": "removed"}


# ── Orders ──────────────────────────────────────────────────────────


@router.get("/orders", response_model=OrdersPage)
async def list_orders(
    account_name: str = Query(..., description="Allegro account name"),
    since: datetime | None = Query(None, description="Fetch orders updated since this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    _require_auth(account_name)
    return await app_state.integration.fetch_orders(account_name, since, page, page_size)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    return await app_state.integration.get_order(account_name, order_id)


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateStatusRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    await app_state.integration.update_order_status(account_name, order_id, body.status)
    return {"status": "updated", "order_id": order_id, "new_status": body.status}


# ── Order Events ────────────────────────────────────────────────────


@router.get("/orders/events")
async def get_order_events(
    account_name: str = Query(..., description="Allegro account name"),
    from_event_id: str | None = Query(None, alias="from", description="Last seen event ID"),
    type: list[str] | None = Query(
        None, description="Event types: BOUGHT, FILLED_IN, READY_FOR_PROCESSING, BUYER_CANCELLED, AUTO_CANCELLED"
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get order events (GET /order/events)."""
    _require_auth(account_name)
    params: dict[str, Any] = {"limit": limit}
    if from_event_id:
        params["from"] = from_event_id
    if type:
        params["type"] = type
    return await _proxy_get("order/events", account_name, params)


@router.get("/orders/event-stats")
async def get_order_event_stats(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get order events statistics (GET /order/event-stats)."""
    _require_auth(account_name)
    return await _proxy_get("order/event-stats", account_name)


# ── Order Tracking ──────────────────────────────────────────────────


class TrackingRequest(BaseModel):
    carrier_id: str
    tracking_number: str
    line_items: list[dict[str, Any]] | None = None


@router.post("/orders/{order_id}/tracking")
async def add_tracking_number(
    order_id: str,
    body: TrackingRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Add a parcel tracking number (POST /order/checkout-forms/{id}/shipments)."""
    _require_auth(account_name)
    payload: dict[str, Any] = {
        "carrierId": body.carrier_id,
        "waybill": body.tracking_number,
    }
    if body.line_items:
        payload["lineItems"] = body.line_items
    return await _proxy_post(f"order/checkout-forms/{order_id}/shipments", account_name, payload)


@router.get("/orders/{order_id}/tracking")
async def get_tracking_numbers(
    order_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get tracking numbers for an order (GET /order/checkout-forms/{id}/shipments)."""
    _require_auth(account_name)
    return await _proxy_get(f"order/checkout-forms/{order_id}/shipments", account_name)


@router.get("/orders/carriers")
async def get_carriers(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get available shipping carriers (GET /order/carriers)."""
    _require_auth(account_name)
    return await _proxy_get("order/carriers", account_name)


@router.get("/orders/{order_id}/tracking-history")
async def get_tracking_history(
    order_id: str,
    account_name: str = Query(..., description="Allegro account name"),
    waybill: str = Query(..., description="Tracking number"),
    carrier_id: str = Query(..., description="Carrier ID"),
):
    """Get carrier parcel tracking history."""
    _require_auth(account_name)
    return await _proxy_get(
        f"order/carriers/{carrier_id}/tracking",
        account_name,
        params={"waybill": waybill},
    )


# ── Order Billing ───────────────────────────────────────────────────


class BillingUploadRequest(BaseModel):
    url: str


@router.post("/orders/{order_id}/billing")
async def upload_billing_document(
    order_id: str,
    body: BillingUploadRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Upload URL to billing documents (POST /billing/billing-entries)."""
    _require_auth(account_name)
    return await _proxy_post(
        f"order/checkout-forms/{order_id}/billing",
        account_name,
        {"url": body.url},
    )


# ── Invoices ────────────────────────────────────────────────────────


class InvoiceUploadJsonRequest(BaseModel):
    invoice_base64: str
    filename: str = "invoice.pdf"
    invoice_number: str = ""


@router.put("/orders/{order_id}/invoice")
async def upload_invoice_multipart(
    order_id: str,
    account_name: str = Query(..., description="Allegro account name"),
    invoice_number: str = Query("", description="Invoice number (e.g. FV 01/2026)"),
    file: UploadFile = File(...),
):
    """Upload an invoice PDF to an Allegro order (multipart form)."""
    _require_auth(account_name)
    contents = await file.read()
    if len(contents) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Invoice file exceeds 8 MB limit")
    result = await app_state.integration.upload_invoice(
        account_name,
        order_id,
        contents,
        file.filename or "invoice.pdf",
        invoice_number,
    )
    return {"status": "uploaded", "order_id": order_id, **result}


@router.post("/orders/{order_id}/invoice")
async def upload_invoice_json(
    order_id: str,
    body: InvoiceUploadJsonRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Upload an invoice PDF to an Allegro order (base64 JSON body)."""
    _require_auth(account_name)
    try:
        contents = base64.b64decode(body.invoice_base64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {exc}") from exc
    if len(contents) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Invoice file exceeds 8 MB limit")
    result = await app_state.integration.upload_invoice(
        account_name,
        order_id,
        contents,
        body.filename,
        body.invoice_number,
    )
    return {"status": "uploaded", "order_id": order_id, **result}


@router.get("/orders/{order_id}/invoices")
async def get_order_invoices(
    order_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get invoice details for an Allegro order."""
    _require_auth(account_name)
    return await app_state.integration.get_order_invoices(account_name, order_id)


# ── Offers ──────────────────────────────────────────────────────────


@router.get("/offers")
async def list_offers(
    account_name: str = Query(..., description="Allegro account name"),
    publication_status: str | None = Query(None, alias="publication.status", description="ACTIVE, INACTIVE, ENDED"),
    selling_mode_format: str | None = Query(
        None, alias="selling_mode.format", description="BUY_NOW, AUCTION, ADVERTISEMENT"
    ),
    name: str | None = Query(None, description="Offer name fragment"),
    category_id: str | None = Query(None, alias="category.id"),
    external_id: str | None = Query(None, alias="external.id"),
    sort: str | None = Query(None),
    limit: int = Query(20, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get seller's offers (GET /sale/offers)."""
    _require_auth(account_name)
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if publication_status:
        params["publication.status"] = publication_status
    if selling_mode_format:
        params["sellingMode.format"] = selling_mode_format
    if name:
        params["name"] = name
    if category_id:
        params["category.id"] = category_id
    if external_id:
        params["external.id"] = external_id
    if sort:
        params["sort"] = sort
    return await _proxy_get("sale/offers", account_name, params)


@router.get("/offers/{offer_id}")
async def get_offer(
    offer_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get all data of a particular offer (GET /sale/product-offers/{offerId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/product-offers/{offer_id}", account_name)


class OfferCreateRequest(BaseModel):
    product_id: str | None = None
    name: str
    category_id: str | None = None
    parameters: list[dict[str, Any]] | None = None
    description: dict[str, Any] | None = None
    images: list[str] | None = None
    selling_mode: dict[str, Any]
    stock: dict[str, Any] | None = None
    delivery: dict[str, Any] | None = None
    location: dict[str, Any] | None = None
    external: dict[str, Any] | None = None
    publication: dict[str, Any] | None = None
    after_sales_services: dict[str, Any] | None = None


@router.post("/offers", status_code=201)
async def create_offer(
    body: OfferCreateRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create offer based on product (POST /sale/product-offers)."""
    _require_auth(account_name)
    payload: dict[str, Any] = {"name": body.name, "sellingMode": body.selling_mode}
    if body.product_id:
        payload["product"] = {"id": body.product_id}
    if body.category_id:
        payload["category"] = {"id": body.category_id}
    if body.parameters:
        payload["parameters"] = body.parameters
    if body.description:
        payload["description"] = body.description
    if body.images:
        payload["images"] = [{"url": u} for u in body.images]
    if body.stock:
        payload["stock"] = body.stock
    if body.delivery:
        payload["delivery"] = body.delivery
    if body.location:
        payload["location"] = body.location
    if body.external:
        payload["external"] = body.external
    if body.publication:
        payload["publication"] = body.publication
    if body.after_sales_services:
        payload["afterSalesServices"] = body.after_sales_services
    return await _proxy_post("sale/product-offers", account_name, payload)


@router.patch("/offers/{offer_id}")
async def edit_offer(
    offer_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Edit an offer (PATCH /sale/product-offers/{offerId})."""
    _require_auth(account_name)
    return await _proxy_request("PATCH", f"sale/product-offers/{offer_id}", account_name, json_data=body)


@router.delete("/offers/{offer_id}/draft")
async def delete_draft_offer(
    offer_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Delete a draft offer (DELETE /sale/offers/{offerId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"sale/offers/{offer_id}", account_name)


# ── Offer Events ────────────────────────────────────────────────────


@router.get("/offers/events")
async def get_offer_events(
    account_name: str = Query(..., description="Allegro account name"),
    from_event_id: str | None = Query(None, alias="from", description="Last seen event ID"),
    type: list[str] | None = Query(None, description="OFFER_ACTIVATED, OFFER_CHANGED, OFFER_ENDED, etc."),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get events about the seller's offers (GET /sale/offer-events)."""
    _require_auth(account_name)
    params: dict[str, Any] = {"limit": limit}
    if from_event_id:
        params["from"] = from_event_id
    if type:
        params["type"] = type
    return await _proxy_get("sale/offer-events", account_name, params)


# ── Offer Publish / Batch ───────────────────────────────────────────


class OfferPublishRequest(BaseModel):
    offer_criteria: list[dict[str, Any]]
    publication: dict[str, Any]


@router.put("/offers/batch/publish")
async def batch_publish_offers(
    body: OfferPublishRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Batch offer publish/unpublish (PUT /sale/offer-publication-commands/{commandId})."""
    _require_auth(account_name)
    import uuid

    cmd_id = str(uuid.uuid4())
    payload = {"offerCriteria": body.offer_criteria, "publication": body.publication}
    return await _proxy_request("PUT", f"sale/offer-publication-commands/{cmd_id}", account_name, json_data=payload)


class OfferBatchPriceRequest(BaseModel):
    offer_criteria: list[dict[str, Any]]
    modification: dict[str, Any]


@router.put("/offers/batch/price")
async def batch_price_change(
    body: OfferBatchPriceRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Batch offer price modification (PUT /sale/offer-price-change-commands/{commandId})."""
    _require_auth(account_name)
    import uuid

    cmd_id = str(uuid.uuid4())
    payload = {"offerCriteria": body.offer_criteria, "modification": body.modification}
    return await _proxy_request("PUT", f"sale/offer-price-change-commands/{cmd_id}", account_name, json_data=payload)


class OfferBatchQuantityRequest(BaseModel):
    offer_criteria: list[dict[str, Any]]
    modification: dict[str, Any]


@router.put("/offers/batch/quantity")
async def batch_quantity_change(
    body: OfferBatchQuantityRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Batch offer quantity modification (PUT /sale/offer-quantity-change-commands/{commandId})."""
    _require_auth(account_name)
    import uuid

    cmd_id = str(uuid.uuid4())
    payload = {"offerCriteria": body.offer_criteria, "modification": body.modification}
    return await _proxy_request("PUT", f"sale/offer-quantity-change-commands/{cmd_id}", account_name, json_data=payload)


class OfferBatchModifyRequest(BaseModel):
    offer_criteria: list[dict[str, Any]]
    modification: dict[str, Any]


@router.put("/offers/batch/modify")
async def batch_modify_offers(
    body: OfferBatchModifyRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Batch offer modification (PUT /sale/offer-modification-commands/{commandId})."""
    _require_auth(account_name)
    import uuid

    cmd_id = str(uuid.uuid4())
    payload = {"offerCriteria": body.offer_criteria, "modification": body.modification}
    return await _proxy_request("PUT", f"sale/offer-modification-commands/{cmd_id}", account_name, json_data=payload)


# ── Offer Promotions ────────────────────────────────────────────────


@router.get("/offers/{offer_id}/promo")
async def get_offer_promo(
    offer_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get offer promotion packages (GET /sale/offers/{offerId}/promo-options)."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/offers/{offer_id}/promo-options", account_name)


@router.get("/offers/{offer_id}/rating")
async def get_offer_rating(
    offer_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get offer rating (GET /sale/offers/{offerId}/rating)."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/offers/{offer_id}/rating", account_name)


# ── Stock ───────────────────────────────────────────────────────────


class StockSyncRequest(BaseModel):
    items: list[StockItem]


@router.post("/stock/sync")
async def sync_stock(
    body: StockSyncRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


# ── Products ────────────────────────────────────────────────────────


@router.get("/products/search")
async def search_products(
    query: str = Query("", description="Search phrase"),
    account_name: str = Query(..., description="Allegro account name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=60),
):
    _require_auth(account_name)
    return await app_state.integration.search_products(account_name, query, page, page_size)


@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    return await app_state.integration.get_product(account_name, product_id)


@router.get("/products/{product_id}/params")
async def get_product_params(
    product_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get product parameters available in given category."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/products/{product_id}", account_name)


class ProductProposeRequest(BaseModel):
    name: str
    category_id: str
    parameters: list[dict[str, Any]] | None = None
    images: list[str] | None = None
    description: dict[str, Any] | None = None


@router.post("/products/propose", status_code=201)
async def propose_product(
    body: ProductProposeRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Propose a product (POST /sale/products)."""
    _require_auth(account_name)
    payload: dict[str, Any] = {
        "name": body.name,
        "category": {"id": body.category_id},
    }
    if body.parameters:
        payload["parameters"] = body.parameters
    if body.images:
        payload["images"] = [{"url": u} for u in body.images]
    if body.description:
        payload["description"] = body.description
    return await _proxy_post("sale/products", account_name, payload)


# ── Categories ──────────────────────────────────────────────────────


@router.get("/categories")
async def list_categories(
    account_name: str = Query(..., description="Allegro account name"),
    parent_id: str | None = Query(None, description="Parent category ID"),
):
    """Get IDs of Allegro categories (GET /sale/categories)."""
    _require_auth(account_name)
    params: dict[str, Any] = {}
    if parent_id:
        params["parent.id"] = parent_id
    return await _proxy_get("sale/categories", account_name, params)


@router.get("/categories/{category_id}")
async def get_category(
    category_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a category by ID (GET /sale/categories/{categoryId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/categories/{category_id}", account_name)


@router.get("/categories/{category_id}/params")
async def get_category_params(
    category_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get parameters supported by a category (GET /sale/categories/{categoryId}/parameters)."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/categories/{category_id}/parameters", account_name)


@router.get("/categories/suggestions")
async def get_category_suggestions(
    name: str = Query(..., description="Product name"),
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get categories suggestions (GET /sale/matching-categories)."""
    _require_auth(account_name)
    return await _proxy_get("sale/matching-categories", account_name, params={"name": name})


@router.get("/categories/events")
async def get_category_events(
    account_name: str = Query(..., description="Allegro account name"),
    from_event_id: str | None = Query(None, alias="from"),
    type: list[str] | None = Query(
        None, description="CATEGORY_CREATED, CATEGORY_RENAMED, CATEGORY_MOVED, CATEGORY_DELETED"
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get changes in categories (GET /sale/category-events)."""
    _require_auth(account_name)
    params: dict[str, Any] = {"limit": limit}
    if from_event_id:
        params["from"] = from_event_id
    if type:
        params["type"] = type
    return await _proxy_get("sale/category-events", account_name, params)


# ── Images & Attachments ────────────────────────────────────────────


class ImageUploadRequest(BaseModel):
    url: str


@router.post("/images", status_code=201)
async def upload_image(
    body: ImageUploadRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Upload an offer image (POST /sale/images)."""
    _require_auth(account_name)
    return await _proxy_post("sale/images", account_name, {"url": body.url})


class AttachmentCreateRequest(BaseModel):
    type: str
    filename: str


@router.post("/attachments", status_code=201)
async def create_attachment(
    body: AttachmentCreateRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create an offer attachment (POST /sale/offer-attachments)."""
    _require_auth(account_name)
    return await _proxy_post(
        "sale/offer-attachments",
        account_name,
        {
            "type": body.type,
            "file": {"name": body.filename},
        },
    )


# ── Offer Variants ──────────────────────────────────────────────────


@router.get("/variants")
async def list_variant_sets(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get the user's variant sets (GET /sale/offer-variants)."""
    _require_auth(account_name)
    return await _proxy_get("sale/offer-variants", account_name, params={"limit": limit, "offset": offset})


@router.get("/variants/{set_id}")
async def get_variant_set(
    set_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a variant set (GET /sale/offer-variants/{setId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/offer-variants/{set_id}", account_name)


@router.post("/variants", status_code=201)
async def create_variant_set(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create variant set (POST /sale/offer-variants)."""
    _require_auth(account_name)
    return await _proxy_post("sale/offer-variants", account_name, body)


@router.put("/variants/{set_id}")
async def update_variant_set(
    set_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Update variant set (PUT /sale/offer-variants/{setId})."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"sale/offer-variants/{set_id}", account_name, json_data=body)


@router.delete("/variants/{set_id}")
async def delete_variant_set(
    set_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Delete a variant set (DELETE /sale/offer-variants/{setId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"sale/offer-variants/{set_id}", account_name)


# ── Offer Tags ──────────────────────────────────────────────────────


@router.get("/tags")
async def list_tags(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's tags (GET /sale/offer-tags)."""
    _require_auth(account_name)
    return await _proxy_get("sale/offer-tags", account_name)


class TagRequest(BaseModel):
    name: str
    hidden: bool = False


@router.post("/tags", status_code=201)
async def create_tag(
    body: TagRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a tag (POST /sale/offer-tags)."""
    _require_auth(account_name)
    return await _proxy_post("sale/offer-tags", account_name, {"name": body.name, "hidden": body.hidden})


@router.put("/tags/{tag_id}")
async def update_tag(
    tag_id: str,
    body: TagRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Modify a tag (PUT /sale/offer-tags/{tagId})."""
    _require_auth(account_name)
    return await _proxy_request(
        "PUT", f"sale/offer-tags/{tag_id}", account_name, json_data={"name": body.name, "hidden": body.hidden}
    )


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Delete a tag (DELETE /sale/offer-tags/{tagId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"sale/offer-tags/{tag_id}", account_name)


class TagAssignRequest(BaseModel):
    tag_ids: list[str]


@router.post("/offers/{offer_id}/tags")
async def assign_tags(
    offer_id: str,
    body: TagAssignRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Assign tags to an offer (POST /sale/offers/{offerId}/tags)."""
    _require_auth(account_name)
    return await _proxy_post(f"sale/offers/{offer_id}/tags", account_name, {"tags": [{"id": t} for t in body.tag_ids]})


# ── Promotions ──────────────────────────────────────────────────────


@router.get("/promotions")
async def list_promotions(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get the user's list of promotions (GET /sale/loyalty/promotions)."""
    _require_auth(account_name)
    return await _proxy_get("sale/loyalty/promotions", account_name, params={"limit": limit, "offset": offset})


@router.get("/promotions/{promotion_id}")
async def get_promotion(
    promotion_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a promotion data by id (GET /sale/loyalty/promotions/{promotionId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/loyalty/promotions/{promotion_id}", account_name)


@router.post("/promotions", status_code=201)
async def create_promotion(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a new promotion (POST /sale/loyalty/promotions)."""
    _require_auth(account_name)
    return await _proxy_post("sale/loyalty/promotions", account_name, body)


@router.put("/promotions/{promotion_id}")
async def update_promotion(
    promotion_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Modify a promotion (PUT /sale/loyalty/promotions/{promotionId})."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"sale/loyalty/promotions/{promotion_id}", account_name, json_data=body)


@router.delete("/promotions/{promotion_id}")
async def delete_promotion(
    promotion_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Deactivate a promotion (DELETE /sale/loyalty/promotions/{promotionId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"sale/loyalty/promotions/{promotion_id}", account_name)


# ── Turnover Discounts ──────────────────────────────────────────────


@router.get("/turnover-discounts")
async def list_turnover_discounts(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the list of turnover discounts (GET /sale/loyalty/turnover-discount)."""
    _require_auth(account_name)
    return await _proxy_get("sale/loyalty/turnover-discount", account_name)


@router.put("/turnover-discounts/{marketplace_id}")
async def create_turnover_discount(
    marketplace_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create/modify turnover discount (PUT /sale/loyalty/turnover-discount/{marketplaceId})."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"sale/loyalty/turnover-discount/{marketplace_id}", account_name, json_data=body)


@router.delete("/turnover-discounts/{marketplace_id}")
async def deactivate_turnover_discount(
    marketplace_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Deactivate turnover discount (PUT /sale/loyalty/turnover-discount/{marketplaceId} with empty)."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"sale/loyalty/turnover-discount/{marketplace_id}", account_name)


# ── Bundles ─────────────────────────────────────────────────────────


@router.get("/bundles")
async def list_bundles(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
):
    """List seller's bundles (GET /sale/bundles)."""
    _require_auth(account_name)
    return await _proxy_get("sale/bundles", account_name, params={"limit": limit, "offset": offset})


@router.get("/bundles/{bundle_id}")
async def get_bundle(
    bundle_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get bundle by ID (GET /sale/bundles/{bundleId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/bundles/{bundle_id}", account_name)


@router.post("/bundles", status_code=201)
async def create_bundle(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a new offer bundle (POST /sale/bundles)."""
    _require_auth(account_name)
    return await _proxy_post("sale/bundles", account_name, body)


@router.delete("/bundles/{bundle_id}")
async def delete_bundle(
    bundle_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Delete bundle by ID (DELETE /sale/bundles/{bundleId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"sale/bundles/{bundle_id}", account_name)


# ── Payments ────────────────────────────────────────────────────────


@router.get("/payments/history")
async def payment_history(
    account_name: str = Query(..., description="Allegro account name"),
    wallet_type: str | None = Query(None),
    payment_id: str | None = Query(None),
    type: str | None = Query(None, description="Operation type"),
    occurred_at_gte: datetime | None = Query(None, alias="occurred_at.gte"),
    occurred_at_lte: datetime | None = Query(None, alias="occurred_at.lte"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Payment operations history (GET /payments/payment-operations)."""
    _require_auth(account_name)
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if wallet_type:
        params["wallet.type"] = wallet_type
    if payment_id:
        params["payment.id"] = payment_id
    if type:
        params["type"] = type
    if occurred_at_gte:
        params["occurredAt.gte"] = occurred_at_gte.isoformat()
    if occurred_at_lte:
        params["occurredAt.lte"] = occurred_at_lte.isoformat()
    return await _proxy_get("payments/payment-operations", account_name, params)


@router.get("/payments/refunds")
async def list_refunds(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get a list of refunded payments (GET /payments/refunds)."""
    _require_auth(account_name)
    return await _proxy_get("payments/refunds", account_name, params={"limit": limit, "offset": offset})


class RefundRequest(BaseModel):
    payment_id: str
    reason_code: str
    line_items: list[dict[str, Any]] | None = None
    delivery: dict[str, Any] | None = None
    overpaid: dict[str, Any] | None = None
    additional_services: dict[str, Any] | None = None
    surcharges: dict[str, Any] | None = None


@router.post("/payments/refunds", status_code=201)
async def initiate_refund(
    body: RefundRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Initiate a refund of a payment (POST /payments/refunds)."""
    _require_auth(account_name)
    payload: dict[str, Any] = {"payment": {"id": body.payment_id}, "reason": body.reason_code}
    if body.line_items:
        payload["lineItems"] = body.line_items
    if body.delivery:
        payload["delivery"] = body.delivery
    if body.overpaid:
        payload["overpaid"] = body.overpaid
    if body.additional_services:
        payload["additionalServices"] = body.additional_services
    if body.surcharges:
        payload["surcharges"] = body.surcharges
    return await _proxy_post("payments/refunds", account_name, payload)


# ── Shipments ───────────────────────────────────────────────────────


@router.post("/shipments", status_code=201)
async def create_shipment(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create new shipment (POST /shipment-management/shipments/create-commands)."""
    _require_auth(account_name)
    return await _proxy_post("shipment-management/shipments/create-commands", account_name, body)


@router.get("/shipments/{shipment_id}")
async def get_shipment(
    shipment_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get shipment details (GET /shipment-management/shipments/{shipmentId})."""
    _require_auth(account_name)
    return await _proxy_get(f"shipment-management/shipments/{shipment_id}", account_name)


@router.post("/shipments/{shipment_id}/cancel")
async def cancel_shipment(
    shipment_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Cancel shipment (POST /shipment-management/shipments/cancel-commands)."""
    _require_auth(account_name)
    return await _proxy_post("shipment-management/shipments/cancel-commands", account_name, {"shipmentId": shipment_id})


@router.post("/shipments/labels")
async def get_shipment_labels(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get shipments labels (POST /shipment-management/shipments/labels)."""
    _require_auth(account_name)
    return await _proxy_post("shipment-management/shipments/labels", account_name, body)


@router.post("/shipments/protocol")
async def get_shipment_protocol(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get shipments protocol (POST /shipment-management/shipments/protocol)."""
    _require_auth(account_name)
    return await _proxy_post("shipment-management/shipments/protocol", account_name, body)


@router.get("/shipments/services")
async def get_delivery_services(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get available delivery services (GET /shipment-management/delivery-services)."""
    _require_auth(account_name)
    return await _proxy_get("shipment-management/delivery-services", account_name)


@router.post("/shipments/pickup-request")
async def request_pickup(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Request shipments pickup (POST /shipment-management/pickups/create-commands)."""
    _require_auth(account_name)
    return await _proxy_post("shipment-management/pickups/create-commands", account_name, body)


@router.post("/shipments/pickup-proposals")
async def get_pickup_proposals(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get shipments pickup proposals (POST /shipment-management/pickups/proposals)."""
    _require_auth(account_name)
    return await _proxy_post("shipment-management/pickups/proposals", account_name, body)


@router.get("/pickup-points")
async def get_pickup_points(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get Allegro pickup drop off points (GET /order/carriers/ALLEGRO/drop-off-points)."""
    _require_auth(account_name)
    return await _proxy_get("order/carriers/ALLEGRO/drop-off-points", account_name)


# ── Returns ─────────────────────────────────────────────────────────


@router.get("/returns")
async def list_returns(
    account_name: str = Query(..., description="Allegro account name"),
    buyer_login: str | None = Query(None),
    status: str | None = Query(None),
    created_at_gte: datetime | None = Query(None, alias="created_at.gte"),
    created_at_lte: datetime | None = Query(None, alias="created_at.lte"),
    limit: int = Query(25, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get customer returns (GET /order/customer-returns)."""
    _require_auth(account_name)
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if buyer_login:
        params["buyerLogin"] = buyer_login
    if status:
        params["status"] = status
    if created_at_gte:
        params["createdAt.gte"] = created_at_gte.isoformat()
    if created_at_lte:
        params["createdAt.lte"] = created_at_lte.isoformat()
    return await _proxy_get("order/customer-returns", account_name, params)


@router.get("/returns/{return_id}")
async def get_return(
    return_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get customer return by id (GET /order/customer-returns/{customerReturnId})."""
    _require_auth(account_name)
    return await _proxy_get(f"order/customer-returns/{return_id}", account_name)


class ReturnRejectRequest(BaseModel):
    rejection_reason: str


@router.post("/returns/{return_id}/reject")
async def reject_return(
    return_id: str,
    body: ReturnRejectRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Reject customer return refund (POST /order/customer-returns/{customerReturnId}/rejection)."""
    _require_auth(account_name)
    return await _proxy_post(
        f"order/customer-returns/{return_id}/rejection", account_name, {"rejectionReason": body.rejection_reason}
    )


# ── Delivery ────────────────────────────────────────────────────────


@router.get("/delivery/methods")
async def list_delivery_methods(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the list of delivery methods (GET /sale/delivery-methods)."""
    _require_auth(account_name)
    return await _proxy_get("sale/delivery-methods", account_name)


@router.get("/delivery/settings")
async def get_delivery_settings(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's delivery settings (GET /sale/delivery-settings)."""
    _require_auth(account_name)
    return await _proxy_get("sale/delivery-settings", account_name)


@router.put("/delivery/settings")
async def update_delivery_settings(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Modify the user's delivery settings (PUT /sale/delivery-settings)."""
    _require_auth(account_name)
    return await _proxy_request("PUT", "sale/delivery-settings", account_name, json_data=body)


@router.get("/delivery/shipping-rates")
async def list_shipping_rates(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's shipping rates (GET /sale/shipping-rates)."""
    _require_auth(account_name)
    return await _proxy_get("sale/shipping-rates", account_name)


@router.get("/delivery/shipping-rates/{rates_id}")
async def get_shipping_rates(
    rates_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the details of a shipping rates set (GET /sale/shipping-rates/{shippingRatesSetId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/shipping-rates/{rates_id}", account_name)


@router.post("/delivery/shipping-rates", status_code=201)
async def create_shipping_rates(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a new shipping rates set (POST /sale/shipping-rates)."""
    _require_auth(account_name)
    return await _proxy_post("sale/shipping-rates", account_name, body)


@router.put("/delivery/shipping-rates/{rates_id}")
async def update_shipping_rates(
    rates_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Edit a user's shipping rates set (PUT /sale/shipping-rates/{shippingRatesSetId})."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"sale/shipping-rates/{rates_id}", account_name, json_data=body)


# ── After Sale Services ────────────────────────────────────────────


@router.get("/warranties")
async def list_warranties(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's warranties (GET /after-sales-service-conditions/warranties)."""
    _require_auth(account_name)
    return await _proxy_get("after-sales-service-conditions/warranties", account_name)


@router.get("/warranties/{warranty_id}")
async def get_warranty(
    warranty_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's warranty (GET /after-sales-service-conditions/warranties/{warrantyId})."""
    _require_auth(account_name)
    return await _proxy_get(f"after-sales-service-conditions/warranties/{warranty_id}", account_name)


@router.post("/warranties", status_code=201)
async def create_warranty(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create new user's warranty (POST /after-sales-service-conditions/warranties)."""
    _require_auth(account_name)
    return await _proxy_post("after-sales-service-conditions/warranties", account_name, body)


@router.put("/warranties/{warranty_id}")
async def update_warranty(
    warranty_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Change the user's warranty (PUT /after-sales-service-conditions/warranties/{warrantyId})."""
    _require_auth(account_name)
    return await _proxy_request(
        "PUT", f"after-sales-service-conditions/warranties/{warranty_id}", account_name, json_data=body
    )


@router.get("/return-policies")
async def list_return_policies(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's return policies (GET /after-sales-service-conditions/return-policies)."""
    _require_auth(account_name)
    return await _proxy_get("after-sales-service-conditions/return-policies", account_name)


@router.get("/return-policies/{policy_id}")
async def get_return_policy(
    policy_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's return policy (GET /after-sales-service-conditions/return-policies/{returnPolicyId})."""
    _require_auth(account_name)
    return await _proxy_get(f"after-sales-service-conditions/return-policies/{policy_id}", account_name)


@router.post("/return-policies", status_code=201)
async def create_return_policy(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create new user's return policy (POST /after-sales-service-conditions/return-policies)."""
    _require_auth(account_name)
    return await _proxy_post("after-sales-service-conditions/return-policies", account_name, body)


@router.put("/return-policies/{policy_id}")
async def update_return_policy(
    policy_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Change the user's return policy (PUT /after-sales-service-conditions/return-policies/{returnPolicyId})."""
    _require_auth(account_name)
    return await _proxy_request(
        "PUT", f"after-sales-service-conditions/return-policies/{policy_id}", account_name, json_data=body
    )


@router.delete("/return-policies/{policy_id}")
async def delete_return_policy(
    policy_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Delete the user's return policy (DELETE /after-sales-service-conditions/return-policies/{returnPolicyId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"after-sales-service-conditions/return-policies/{policy_id}", account_name)


# ── Messages ────────────────────────────────────────────────────────


@router.get("/messages/threads")
async def list_message_threads(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
):
    """List user threads (GET /messaging/threads)."""
    _require_auth(account_name)
    return await _proxy_get("messaging/threads", account_name, params={"limit": limit, "offset": offset})


@router.get("/messages/threads/{thread_id}")
async def get_message_thread(
    thread_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get user thread (GET /messaging/threads/{threadId})."""
    _require_auth(account_name)
    return await _proxy_get(f"messaging/threads/{thread_id}", account_name)


@router.get("/messages/threads/{thread_id}/messages")
async def list_thread_messages(
    thread_id: str,
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
):
    """List messages in thread (GET /messaging/threads/{threadId}/messages)."""
    _require_auth(account_name)
    return await _proxy_get(
        f"messaging/threads/{thread_id}/messages", account_name, params={"limit": limit, "offset": offset}
    )


class MessageSendRequest(BaseModel):
    recipient_login: str
    text: str
    offer_id: str | None = None
    order_id: str | None = None
    attachments: list[dict[str, Any]] | None = None


@router.post("/messages", status_code=201)
async def send_message(
    body: MessageSendRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Write a new message (POST /messaging/messages)."""
    _require_auth(account_name)
    payload: dict[str, Any] = {
        "recipient": {"login": body.recipient_login},
        "text": body.text,
    }
    if body.offer_id:
        payload["offer"] = {"id": body.offer_id}
    if body.order_id:
        payload["order"] = {"id": body.order_id}
    if body.attachments:
        payload["attachments"] = body.attachments
    return await _proxy_post("messaging/messages", account_name, payload)


@router.put("/messages/threads/{thread_id}/read")
async def mark_thread_read(
    thread_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Mark a particular thread as read (PUT /messaging/threads/{threadId}/read)."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"messaging/threads/{thread_id}/read", account_name, json_data={"read": True})


# ── Billing ─────────────────────────────────────────────────────────


@router.get("/billing/types")
async def list_billing_types(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a list of billing types (GET /billing/billing-types)."""
    _require_auth(account_name)
    return await _proxy_get("billing/billing-types", account_name)


@router.get("/billing/entries")
async def list_billing_entries(
    account_name: str = Query(..., description="Allegro account name"),
    type_id: str | None = Query(None, alias="type.id"),
    occurred_at_gte: datetime | None = Query(None, alias="occurred_at.gte"),
    occurred_at_lte: datetime | None = Query(None, alias="occurred_at.lte"),
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get a list of billing entries (GET /billing/billing-entries)."""
    _require_auth(account_name)
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if type_id:
        params["type.id"] = type_id
    if occurred_at_gte:
        params["occurredAt.gte"] = occurred_at_gte.isoformat()
    if occurred_at_lte:
        params["occurredAt.lte"] = occurred_at_lte.isoformat()
    return await _proxy_get("billing/billing-entries", account_name, params)


# ── User ────────────────────────────────────────────────────────────


@router.get("/user/info")
async def get_user_info(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get basic information about user (GET /me)."""
    _require_auth(account_name)
    return await _proxy_get("me", account_name)


@router.get("/user/ratings")
async def get_user_ratings(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get the user's ratings (GET /sale/user-ratings)."""
    _require_auth(account_name)
    return await _proxy_get("sale/user-ratings", account_name, params={"limit": limit, "offset": offset})


@router.get("/user/sales-quality")
async def get_sales_quality(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get sales quality (GET /sale/quality)."""
    _require_auth(account_name)
    return await _proxy_get("sale/quality", account_name)


# ── Commission Refunds ──────────────────────────────────────────────


@router.get("/commission-refunds")
async def list_commission_refunds(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(25, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get a list of refund applications (GET /order/refund-claims)."""
    _require_auth(account_name)
    return await _proxy_get("order/refund-claims", account_name, params={"limit": limit, "offset": offset})


@router.get("/commission-refunds/{refund_id}")
async def get_commission_refund(
    refund_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a refund application details (GET /order/refund-claims/{claimId})."""
    _require_auth(account_name)
    return await _proxy_get(f"order/refund-claims/{refund_id}", account_name)


@router.post("/commission-refunds", status_code=201)
async def create_commission_refund(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a refund application (POST /order/refund-claims)."""
    _require_auth(account_name)
    return await _proxy_post("order/refund-claims", account_name, body)


@router.delete("/commission-refunds/{refund_id}")
async def cancel_commission_refund(
    refund_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Cancel a refund application (DELETE /order/refund-claims/{claimId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"order/refund-claims/{refund_id}", account_name)


# ── Additional Services ────────────────────────────────────────────


@router.get("/additional-services/groups")
async def list_additional_service_groups(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's additional services groups (GET /sale/offer-additional-services/groups)."""
    _require_auth(account_name)
    return await _proxy_get("sale/offer-additional-services/groups", account_name)


@router.get("/additional-services/groups/{group_id}")
async def get_additional_service_group(
    group_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the details of an additional services group."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/offer-additional-services/groups/{group_id}", account_name)


@router.post("/additional-services/groups", status_code=201)
async def create_additional_service_group(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create additional services group (POST /sale/offer-additional-services/groups)."""
    _require_auth(account_name)
    return await _proxy_post("sale/offer-additional-services/groups", account_name, body)


@router.put("/additional-services/groups/{group_id}")
async def update_additional_service_group(
    group_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Modify an additional services group."""
    _require_auth(account_name)
    return await _proxy_request(
        "PUT", f"sale/offer-additional-services/groups/{group_id}", account_name, json_data=body
    )


@router.get("/additional-services/definitions")
async def get_additional_service_definitions(
    account_name: str = Query(..., description="Allegro account name"),
    category_id: str | None = Query(None),
):
    """Get the additional services definitions by categories."""
    _require_auth(account_name)
    params: dict[str, Any] = {}
    if category_id:
        params["category.id"] = category_id
    return await _proxy_get("sale/offer-additional-services/definitions", account_name, params)


# ── Size Tables ─────────────────────────────────────────────────────


@router.get("/size-tables")
async def list_size_tables(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's size tables (GET /sale/size-tables)."""
    _require_auth(account_name)
    return await _proxy_get("sale/size-tables", account_name)


@router.get("/size-tables/{table_id}")
async def get_size_table(
    table_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a size table (GET /sale/size-tables/{tableId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/size-tables/{table_id}", account_name)


@router.post("/size-tables", status_code=201)
async def create_size_table(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a size table (POST /sale/size-tables)."""
    _require_auth(account_name)
    return await _proxy_post("sale/size-tables", account_name, body)


@router.put("/size-tables/{table_id}")
async def update_size_table(
    table_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Update a size table (PUT /sale/size-tables/{tableId})."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"sale/size-tables/{table_id}", account_name, json_data=body)


# ── Points of Service ──────────────────────────────────────────────


@router.get("/points-of-service")
async def list_points_of_service(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's points of service (GET /points-of-service)."""
    _require_auth(account_name)
    return await _proxy_get("points-of-service", account_name)


@router.get("/points-of-service/{point_id}")
async def get_point_of_service(
    point_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the details of a point of service (GET /points-of-service/{pointOfServiceId})."""
    _require_auth(account_name)
    return await _proxy_get(f"points-of-service/{point_id}", account_name)


@router.post("/points-of-service", status_code=201)
async def create_point_of_service(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a point of service (POST /points-of-service)."""
    _require_auth(account_name)
    return await _proxy_post("points-of-service", account_name, body)


@router.put("/points-of-service/{point_id}")
async def update_point_of_service(
    point_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Modify a point of service (PUT /points-of-service/{pointOfServiceId})."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"points-of-service/{point_id}", account_name, json_data=body)


@router.delete("/points-of-service/{point_id}")
async def delete_point_of_service(
    point_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Delete a point of service (DELETE /points-of-service/{pointOfServiceId})."""
    _require_auth(account_name)
    return await _proxy_request("DELETE", f"points-of-service/{point_id}", account_name)


# ── Contacts ────────────────────────────────────────────────────────


@router.get("/contacts")
async def list_contacts(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's contacts (GET /sale/offer-contacts)."""
    _require_auth(account_name)
    return await _proxy_get("sale/offer-contacts", account_name)


@router.get("/contacts/{contact_id}")
async def get_contact(
    contact_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get contact details (GET /sale/offer-contacts/{contactId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/offer-contacts/{contact_id}", account_name)


@router.post("/contacts", status_code=201)
async def create_contact(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create a new contact (POST /sale/offer-contacts)."""
    _require_auth(account_name)
    return await _proxy_post("sale/offer-contacts", account_name, body)


@router.put("/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Modify contact details (PUT /sale/offer-contacts/{contactId})."""
    _require_auth(account_name)
    return await _proxy_request("PUT", f"sale/offer-contacts/{contact_id}", account_name, json_data=body)


# ── Pricing ─────────────────────────────────────────────────────────


@router.get("/pricing/offer-quotes")
async def get_offer_quotes(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the user's current offer quotes (GET /pricing/offer-quotes)."""
    _require_auth(account_name)
    return await _proxy_get("pricing/offer-quotes", account_name)


@router.post("/pricing/fee-calculate")
async def calculate_fee(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Calculate fee and commission for an offer (POST /pricing/offer-fee-preview)."""
    _require_auth(account_name)
    return await _proxy_post("pricing/offer-fee-preview", account_name, body)


# ── Tax ─────────────────────────────────────────────────────────────


@router.get("/tax/settings/{category_id}")
async def get_tax_settings(
    category_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get all tax settings for category (GET /sale/tax-settings)."""
    _require_auth(account_name)
    return await _proxy_get("sale/tax-settings", account_name, params={"category.id": category_id})


# ── Badge Campaigns ─────────────────────────────────────────────────


@router.get("/badges/campaigns")
async def list_badge_campaigns(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a list of available badge campaigns (GET /sale/badges/campaigns)."""
    _require_auth(account_name)
    return await _proxy_get("sale/badges/campaigns", account_name)


@router.get("/badges")
async def list_badges(
    account_name: str = Query(..., description="Allegro account name"),
    offer_id: str | None = Query(None),
    campaign_id: str | None = Query(None),
):
    """Get a list of badges (GET /sale/badges)."""
    _require_auth(account_name)
    params: dict[str, Any] = {}
    if offer_id:
        params["offer.id"] = offer_id
    if campaign_id:
        params["campaign.id"] = campaign_id
    return await _proxy_get("sale/badges", account_name, params)


@router.post("/badges", status_code=201)
async def apply_badge(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Apply for badge in selected offer (POST /sale/badges)."""
    _require_auth(account_name)
    return await _proxy_post("sale/badges", account_name, body)


# ── Compatibility List ──────────────────────────────────────────────


@router.get("/compatibility/products/{offer_id}")
async def get_compatible_products(
    offer_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get list of compatible products (GET /sale/offers/{offerId}/compatibility-list)."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/offers/{offer_id}/compatibility-list", account_name)


@router.get("/compatibility/groups/{category_id}")
async def get_compatibility_groups(
    category_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get list of compatible product groups (GET /sale/compatibility-list/supported-categories/{categoryId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/compatibility-list/supported-categories/{category_id}", account_name)


@router.get("/compatibility/suggestions/{offer_id}")
async def get_compatibility_suggestions(
    offer_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get suggested compatibility list (GET /sale/compatibility-list/suggestions)."""
    _require_auth(account_name)
    return await _proxy_get("sale/compatibility-list/suggestions", account_name, params={"offer.id": offer_id})


@router.get("/compatibility/categories")
async def get_compatibility_categories(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get list of categories where compatibility list is supported."""
    _require_auth(account_name)
    return await _proxy_get("sale/compatibility-list/supported-categories", account_name)


# ── Fulfillment (One Fulfillment) ──────────────────────────────────


@router.get("/fulfillment/stock")
async def get_fulfillment_stock(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get available stock (GET /fulfillment/stock)."""
    _require_auth(account_name)
    return await _proxy_get("fulfillment/stock", account_name)


@router.get("/fulfillment/parcels")
async def get_fulfillment_parcels(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get list of shipped parcels (GET /fulfillment/shipments)."""
    _require_auth(account_name)
    return await _proxy_get("fulfillment/shipments", account_name)


@router.get("/fulfillment/products")
async def get_fulfillment_products(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get list of available products (GET /fulfillment/products)."""
    _require_auth(account_name)
    return await _proxy_get("fulfillment/products", account_name)


@router.get("/fulfillment/advance-ship-notices")
async def list_advance_ship_notices(
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get list of Advance Ship Notices (GET /fulfillment/advance-ship-notices)."""
    _require_auth(account_name)
    return await _proxy_get("fulfillment/advance-ship-notices", account_name)


@router.get("/fulfillment/advance-ship-notices/{asn_id}")
async def get_advance_ship_notice(
    asn_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get single Advance Ship Notice (GET /fulfillment/advance-ship-notices/{id})."""
    _require_auth(account_name)
    return await _proxy_get(f"fulfillment/advance-ship-notices/{asn_id}", account_name)


@router.post("/fulfillment/advance-ship-notices", status_code=201)
async def create_advance_ship_notice(
    body: dict[str, Any],
    account_name: str = Query(..., description="Allegro account name"),
):
    """Create an Advance Ship Notice (POST /fulfillment/advance-ship-notices)."""
    _require_auth(account_name)
    return await _proxy_post("fulfillment/advance-ship-notices", account_name, body)


# ── Post Purchase Issues (Disputes/Claims) ─────────────────────────


@router.get("/disputes")
async def list_disputes(
    account_name: str = Query(..., description="Allegro account name"),
    limit: int = Query(25, ge=1),
    offset: int = Query(0, ge=0),
):
    """Get the user's post purchase issues (GET /sale/disputes)."""
    _require_auth(account_name)
    return await _proxy_get("sale/disputes", account_name, params={"limit": limit, "offset": offset})


@router.get("/disputes/{dispute_id}")
async def get_dispute(
    dispute_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get a single dispute or claim (GET /sale/disputes/{disputeId})."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/disputes/{dispute_id}", account_name)


@router.get("/disputes/{dispute_id}/messages")
async def get_dispute_messages(
    dispute_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    """Get the messages and state changes within a post purchase issue."""
    _require_auth(account_name)
    return await _proxy_get(f"sale/disputes/{dispute_id}/messages", account_name)


# ── Helpers ─────────────────────────────────────────────────────────


def _require_auth(account_name: str) -> None:
    if not app_state.auth_manager.is_authenticated(account_name):
        raise HTTPException(
            status_code=401,
            detail=f"Account '{account_name}' not authenticated. Use POST /auth/{account_name}/device-code first.",
        )


def _get_auth_args(account_name: str) -> tuple[str, str, str, str, str]:
    account = app_state.account_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return account.name, account.client_id, account.client_secret, account.api_url, account.auth_url


async def _proxy_get(
    path: str,
    account_name: str,
    params: dict[str, Any] | None = None,
) -> Any:
    auth = _get_auth_args(account_name)
    resp = await app_state.client.get(path, *auth, params=params)
    resp.raise_for_status()
    return resp.json()


async def _proxy_post(
    path: str,
    account_name: str,
    json_data: dict[str, Any],
) -> Any:
    auth = _get_auth_args(account_name)
    resp = await app_state.client.post(path, *auth, json_data=json_data)
    resp.raise_for_status()
    return resp.json()


async def _proxy_request(
    method: str,
    path: str,
    account_name: str,
    json_data: dict[str, Any] | None = None,
) -> Any:
    auth = _get_auth_args(account_name)
    resp = await app_state.client.request(method, path, *auth, json_data=json_data)
    if resp.status_code == 204:
        return {"status": "success"}
    resp.raise_for_status()
    try:
        return resp.json()
    except (ValueError, KeyError):
        return {"status": "success", "status_code": resp.status_code}

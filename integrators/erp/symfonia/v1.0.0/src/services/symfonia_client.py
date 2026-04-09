"""Symfonia WebAPI HTTP client.

Wraps all REST calls to the Symfonia ERP WebAPI,
handling session management and error mapping.
"""

import asyncio
import logging
from typing import Any

import httpx

from src.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class SymfoniaApiError(Exception):
    """Raised when the Symfonia WebAPI returns an error."""

    def __init__(self, status_code: int, message: str, details: Any = None) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"Symfonia API error {status_code}: {message}")


class SymfoniaClient:
    """Async HTTP client for Symfonia ERP WebAPI."""

    def __init__(
        self,
        base_url: str,
        application_guid: str,
        device_name: str = "pinquark-oip",
        session_timeout_minutes: int = 30,
        connect_timeout: float = 30.0,
        read_timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=connect_timeout, read=read_timeout, write=60.0, pool=30.0),
            verify=False,
        )
        self._session = SessionManager(
            base_url=base_url,
            application_guid=application_guid,
            device_name=device_name,
            session_timeout_minutes=session_timeout_minutes,
            http_client=self._client,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
    ) -> Any:
        """Execute an authenticated request with automatic session renewal on 401."""
        url = f"{self._base_url}{path}"

        for attempt in range(self._max_retries):
            token = await self._session.get_session_token()
            headers = {
                "Authorization": f"Session {token}",
                "Content-Type": "application/json",
            }

            try:
                resp = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    headers=headers,
                )
            except httpx.ConnectError as exc:
                raise SymfoniaApiError(
                    status_code=503,
                    message=f"Connection failed: {method} {path}",
                    details=str(exc),
                ) from exc
            except httpx.TimeoutException as exc:
                raise SymfoniaApiError(
                    status_code=504,
                    message=f"Request timed out: {method} {path}",
                    details=str(exc),
                ) from exc

            if resp.status_code == 401 and attempt < self._max_retries - 1:
                logger.warning("Symfonia session expired (401), renewing (attempt %d)", attempt + 1)
                await self._session.invalidate()
                await asyncio.sleep(0.5 * (attempt + 1))
                continue

            if resp.status_code >= 400:
                error_body = None
                try:
                    error_body = resp.json()
                except Exception:
                    error_body = resp.text
                raise SymfoniaApiError(
                    status_code=resp.status_code,
                    message=f"Request failed: {method} {path}",
                    details=error_body,
                )

            if resp.status_code == 204:
                return None

            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                return resp.json()
            return resp.text

        raise SymfoniaApiError(status_code=401, message="Session renewal failed after max retries")

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json_body: Any = None) -> Any:
        return await self._request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body: Any = None) -> Any:
        return await self._request("PUT", path, json_body=json_body)

    async def patch(self, path: str, json_body: Any = None) -> Any:
        return await self._request("PATCH", path, json_body=json_body)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    # ---- Health / Diagnostics ----

    async def ping(self) -> dict[str, Any]:
        return await self._session.ping()

    async def alive(self) -> str:
        return await self._session.alive()

    # ---- Contractors ----

    async def list_contractors(self) -> list[dict[str, Any]]:
        return await self.get("/api/Contractors")

    async def get_contractor_by_id(self, contractor_id: int) -> dict[str, Any]:
        return await self.get("/api/Contractors", params={"id": contractor_id})

    async def get_contractor_by_code(self, code: str) -> dict[str, Any]:
        return await self.get("/api/Contractors", params={"code": code})

    async def get_contractor_by_nip(self, nip: str) -> list[dict[str, Any]]:
        return await self.get("/api/Contractors", params={"nip": nip})

    async def create_contractor(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self.post("/api/Contractors/Create", json_body=data)

    async def update_contractor(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self.put("/api/Contractors/Update", json_body=data)

    async def filter_contractors(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        return await self.patch("/api/Contractors/Filter", json_body=criteria)

    async def filter_contractors_sql(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        return await self.patch("/api/Contractors/FilterSql", json_body=criteria)

    async def sync_contractors(self, date_from: str) -> list[dict[str, Any]]:
        return await self.get("/api/Contractors/IncrementalSync", params={"dateFrom": date_from})

    async def get_contractor_catalogs(self) -> list[dict[str, Any]]:
        return await self.get("/api/Contractors/Catalogs")

    async def get_contractor_kinds(self) -> list[dict[str, Any]]:
        return await self.get("/api/Contractors/Kinds")

    # ---- Products ----

    async def list_products(self) -> list[dict[str, Any]]:
        return await self.get("/api/Products")

    async def get_product_by_id(self, product_id: int) -> dict[str, Any]:
        return await self.get("/api/Products", params={"id": product_id})

    async def get_product_by_code(self, code: str) -> dict[str, Any]:
        return await self.get("/api/Products", params={"code": code})

    async def create_product(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self.post("/api/Products/Create", json_body=data)

    async def update_product(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self.put("/api/Products/Update", json_body=data)

    async def filter_products(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        return await self.patch("/api/Products/Filter", json_body=criteria)

    async def filter_products_sql(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        return await self.patch("/api/Products/FilterSql", json_body=criteria)

    async def get_product_barcodes(self, product_id: int | None = None, product_code: str | None = None) -> list:
        params: dict[str, Any] = {}
        if product_id is not None:
            params["productId"] = product_id
        elif product_code is not None:
            params["productCode"] = product_code
        return await self.get("/api/Products/Barcodes", params=params)

    async def sync_products(self, date_from: str) -> list[dict[str, Any]]:
        return await self.get("/api/Products/IncrementalSync", params={"dateFrom": date_from})

    # ---- Sales Documents ----

    async def list_sales(self) -> list[dict[str, Any]]:
        return await self.get("/api/Sales")

    async def get_sale_by_id(self, document_id: int) -> dict[str, Any]:
        return await self.get("/api/Sales", params={"id": document_id})

    async def get_sale_by_number(self, number: str) -> dict[str, Any]:
        return await self.get("/api/Sales", params={"number": number})

    async def filter_sales(
        self,
        date_from: str,
        date_to: str,
        buyer_code: str | None = None,
        buyer_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"dateFrom": date_from, "dateTo": date_to}
        if buyer_code:
            params["buyerCode"] = buyer_code
        if buyer_id is not None:
            params["buyerId"] = buyer_id
        return await self.get("/api/Sales/Filter", params=params)

    async def get_sale_status(self, document_id: int | None = None, number: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if document_id is not None:
            params["documentId"] = document_id
        elif number is not None:
            params["documentNumber"] = number
        return await self.get("/api/Sales/Status", params=params)

    async def get_sale_pdf(self, document_id: int | None = None, number: str | None = None) -> str:
        params: dict[str, Any] = {}
        if document_id is not None:
            params["documentId"] = document_id
        elif number is not None:
            params["documentNumber"] = number
        return await self.get("/api/Sales/PDF", params=params)

    async def get_sale_correction(self, correction_id: int | None = None, number: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if correction_id is not None:
            params["id"] = correction_id
        elif number is not None:
            params["number"] = number
        return await self.get("/api/Sales/Correction", params=params)

    async def sync_sales(self, date_from: str) -> list[dict[str, Any]]:
        return await self.get("/api/Sales/IncrementalSync", params={"dateFrom": date_from})

    # ---- Purchase Documents ----

    async def list_purchases(self) -> list[dict[str, Any]]:
        return await self.get("/api/Purchases")

    async def get_purchase_by_id(self, document_id: int) -> dict[str, Any]:
        return await self.get("/api/Purchases", params={"id": document_id})

    async def get_purchase_by_number(self, number: str) -> dict[str, Any]:
        return await self.get("/api/Purchases", params={"number": number})

    async def filter_purchases(
        self,
        date_from: str,
        date_to: str,
        supplier_code: str | None = None,
        supplier_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"dateFrom": date_from, "dateTo": date_to}
        if supplier_code:
            params["delivererCode"] = supplier_code
        if supplier_id is not None:
            params["delivererId"] = supplier_id
        return await self.get("/api/Purchases/Filter", params=params)

    async def get_purchase_status(
        self,
        document_id: int | None = None,
        number: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if document_id is not None:
            params["documentId"] = document_id
        elif number is not None:
            params["documentNumber"] = number
        return await self.get("/api/Purchases/Status", params=params)

    async def sync_purchases(self, date_from: str) -> list[dict[str, Any]]:
        return await self.get("/api/Purchases/IncrementalSync", params={"dateFrom": date_from})

    # ---- Orders (foreign / ZMO) ----

    async def list_orders(self) -> list[dict[str, Any]]:
        return await self.get("/api/Orders")

    async def get_order_by_id(self, order_id: int) -> dict[str, Any]:
        return await self.get("/api/Orders", params={"id": order_id})

    async def get_order_by_number(self, number: str) -> dict[str, Any]:
        return await self.get("/api/Orders", params={"number": number})

    async def filter_orders(
        self,
        date_from: str,
        date_to: str,
        recipient_code: str | None = None,
        recipient_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"dateFrom": date_from, "dateTo": date_to}
        if recipient_code:
            params["recipientCode"] = recipient_code
        if recipient_id is not None:
            params["recipientId"] = recipient_id
        return await self.get("/api/Orders/Filter", params=params)

    async def get_order_status(self, order_id: int | None = None, number: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if order_id is not None:
            params["orderId"] = order_id
        elif number is not None:
            params["orderNumber"] = number
        return await self.get("/api/Orders/Status", params=params)

    async def sync_orders(self, date_from: str) -> list[dict[str, Any]]:
        return await self.get("/api/Orders/IncrementalSync", params={"dateFrom": date_from})

    # ---- Own Orders (ZMW) ----

    async def list_own_orders(self) -> list[dict[str, Any]]:
        return await self.get("/api/OwnOrders")

    async def get_own_order_by_id(self, order_id: int) -> dict[str, Any]:
        return await self.get("/api/OwnOrders", params={"id": order_id})

    # ---- Inventory States ----

    async def get_inventory_all(self) -> list[dict[str, Any]]:
        return await self.get("/api/InventoryStates")

    async def get_inventory_by_product_id(self, product_id: int) -> list[dict[str, Any]]:
        return await self.get("/api/InventoryStates/ByProduct", params={"id": product_id})

    async def get_inventory_by_product_code(self, code: str) -> list[dict[str, Any]]:
        return await self.get("/api/InventoryStates/ByProduct", params={"code": code})

    async def get_inventory_by_warehouse_id(self, warehouse_id: int) -> list[dict[str, Any]]:
        return await self.get("/api/InventoryStates/ByWarehouse", params={"id": warehouse_id})

    async def get_inventory_by_warehouse_code(self, code: str) -> list[dict[str, Any]]:
        return await self.get("/api/InventoryStates/ByWarehouse", params={"code": code})

    async def get_inventory_changes(self) -> list[dict[str, Any]]:
        return await self.get("/api/InventoryStates/Changes")

    # ---- Payments ----

    async def list_payments(self) -> list[dict[str, Any]]:
        return await self.get("/api/Payments")

    # ---- Dictionaries ----

    async def list_warehouses(self) -> list[dict[str, Any]]:
        return await self.get("/api/Dictionaries/Warehouses")

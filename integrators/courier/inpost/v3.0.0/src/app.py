"""InPost International 2025 Courier Connector — SDK-based application.

Migrated from manual FastAPI setup to the Pinquark Connector SDK.
All business logic remains in ``integration.py``; this module wires
actions to the SDK framework.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, ClassVar

try:
    SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
    if SDK_PYTHON_PATH.exists() and str(SDK_PYTHON_PATH) not in sys.path:
        sys.path.insert(0, str(SDK_PYTHON_PATH))
except (IndexError, OSError):
    pass

from pinquark_connector_sdk import ConnectorApp, action

try:
    from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app
except ImportError:
    augment_legacy_fastapi_app = None  # type: ignore[assignment,misc]

from src.integration import InpostIntegration
from src.schemas import (
    CreateShipmentRequest,
    InpostCredentials,
    PickupRequest,
    RateProduct,
    ReturnsShipmentRequest,
    StandardizedRateResponse,
)


class InPostConnector(ConnectorApp):
    name = "inpost"
    category = "courier"
    version = "3.0.0"
    display_name = "InPost International 2025"
    description = "InPost courier integration — Paczkomaty, Kurier, International, Returns"

    class Config:
        required_credentials: ClassVar[list[str]] = ["organization_id", "client_secret"]
        rate_limits: ClassVar[dict[str, str]] = {"default": "100/minute"}

    def __init__(self) -> None:
        self._integration = InpostIntegration()
        super().__init__()

    def _creds(self, payload: dict[str, Any]) -> InpostCredentials:
        """Extract credentials from action payload or account store."""
        if "credentials" in payload and isinstance(payload["credentials"], dict):
            return InpostCredentials(**payload["credentials"])
        account_name = payload.get("account_name", "default")
        stored = self.accounts.get(account_name) or {}
        return InpostCredentials(
            organization_id=stored.get("organization_id", payload.get("organization_id", "")),
            client_secret=stored.get("client_secret", payload.get("client_secret", "")),
            access_token=stored.get("access_token", payload.get("access_token")),
            sandbox_mode=stored.get("sandbox_mode", payload.get("sandbox_mode", False)),
        )

    @action("shipment.create")
    async def create_shipment(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        request = CreateShipmentRequest(
            credentials=creds, **{k: v for k, v in payload.items() if k not in ("credentials", "account_name")}
        )
        result, status_code = await self._integration.create_order(creds, request)
        if status_code >= 400:
            return {"error": result, "status_code": status_code}
        return result if isinstance(result, dict) else {"data": result}

    @action("shipment.status")
    async def get_shipment_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        waybill = payload["waybill"]
        status, status_code = await self._integration.get_order_status(creds, waybill)
        return {"status": status, "status_code": status_code}

    @action("shipment.get")
    async def get_shipment(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        tracking_number = payload["tracking_number"]
        result, status_code = await self._integration.get_order(creds, tracking_number)
        if status_code >= 400:
            return {"error": result, "status_code": status_code}
        return result if isinstance(result, dict) else {"data": result}

    @action("label.get")
    async def get_label(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        tracking_number = payload["tracking_number"]
        label_bytes, status_code = await self._integration.get_waybill_label_bytes(creds, tracking_number)
        if status_code >= 400:
            return {"error": str(label_bytes), "status_code": status_code}
        import base64

        return {"label_base64": base64.b64encode(label_bytes).decode(), "content_type": "application/pdf"}

    @action("shipment.cancel")
    async def cancel_shipment(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        waybill = payload["waybill"]
        order_id = payload.get("order_id")
        result, status_code = await self._integration.delete_order(creds, waybill, order_id=order_id)
        return {"result": result, "status_code": status_code}

    @action("pickup_points.list")
    async def get_pickup_points(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        data: dict[str, Any] = {}
        if payload.get("city"):
            data["city"] = payload["city"]
        if payload.get("postcode"):
            data["postcode"] = payload["postcode"]
        data["extras"] = payload.get("extras", {})
        result, status_code = await self._integration.get_points(creds, data)
        if status_code >= 400:
            return {"error": result, "status_code": status_code}
        return result if isinstance(result, dict) else {"data": result}

    @action("tracking.get")
    async def get_tracking(self, payload: dict[str, Any]) -> dict[str, Any]:
        waybill = payload["waybill"]
        result, _status = await self._integration.get_tracking_info(waybill)
        return result.model_dump()

    @action("rates.get", output_schema=StandardizedRateResponse, dynamic_schema=True)
    async def get_rates(self, payload: dict[str, Any]) -> dict[str, Any]:
        products = _calculate_inpost_rates(
            weight=payload.get("weight", 1.0),
            length=payload.get("length", 20.0),
            width=payload.get("width", 20.0),
            height=payload.get("height", 20.0),
            sender_country=payload.get("sender_country_code", "PL"),
            receiver_country=payload.get("receiver_country_code", "PL"),
        )
        resp = StandardizedRateResponse(
            products=products,
            source="inpost",
            raw={"method": "pricing_table", "weight": payload.get("weight", 1.0)},
        )
        return resp.model_dump()

    @action("return.create")
    async def create_return(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        request = ReturnsShipmentRequest(
            credentials=creds, **{k: v for k, v in payload.items() if k not in ("credentials", "account_name")}
        )
        returns_dto = self._integration.build_returns_dto(request)
        result, status_code = await self._integration.create_return_shipment(creds, returns_dto)
        if status_code >= 400:
            return {"error": result, "status_code": status_code}
        return result if isinstance(result, dict) else {"data": result}

    @action("pickup.create")
    async def create_pickup(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        request = PickupRequest(
            credentials=creds, **{k: v for k, v in payload.items() if k not in ("credentials", "account_name")}
        )
        pickup_dto = self._integration._build_pickup_order_dto(
            CreateShipmentRequest(
                credentials=creds,
                serviceName="inpost_international",
                extras=request.extras,
                content=request.content,
                parcels=request.parcels,
                shipper=request.shipper,
                receiver=request.shipper,
            ),
            tracking_number=request.tracking_numbers[0] if request.tracking_numbers else "",
        )
        result = await self._integration._create_pickup_order(pickup_dto, creds)
        return result if isinstance(result, dict) else {"data": result}

    @action("pickup_hours.get")
    async def get_pickup_hours(self, payload: dict[str, Any]) -> dict[str, Any]:
        creds = self._creds(payload)
        result, status_code = await self._integration.get_pickup_hours(
            creds,
            payload["postcode"],
            payload.get("country_code", "PL"),
        )
        if status_code >= 400:
            return {"error": result, "status_code": status_code}
        return result if isinstance(result, dict) else {"data": result}

    async def test_connection(self) -> bool:
        """Verify InPost API is reachable by hitting the public tracking endpoint."""
        try:
            resp = await self.http.get(
                "https://api.inpost-group.com/tracking/v1/parcels",
                params={"trackingNumbers": "HEALTHCHECK"},
            )
            return resp.status_code < 500
        except Exception:
            return False


def _calculate_inpost_rates(
    weight: float,
    length: float,
    width: float,
    height: float,
    sender_country: str,
    receiver_country: str,
) -> list[RateProduct]:
    is_domestic = sender_country == receiver_country == "PL"
    products: list[RateProduct] = []
    volume_weight = (length * width * height) / 5000
    billable = max(weight, volume_weight)

    if is_domestic:
        if billable <= 25 and max(length, width, height) <= 41:
            products.append(
                RateProduct(
                    name="InPost Paczkomat (A)",
                    price=12.99,
                    currency="PLN",
                    delivery_days=2,
                    attributes={"source": "inpost", "service": "paczkomat", "size": "A"},
                )
            )
        if billable <= 25 and max(length, width, height) <= 64:
            products.append(
                RateProduct(
                    name="InPost Paczkomat (B)",
                    price=13.99,
                    currency="PLN",
                    delivery_days=2,
                    attributes={"source": "inpost", "service": "paczkomat", "size": "B"},
                )
            )
        if billable <= 25:
            products.append(
                RateProduct(
                    name="InPost Paczkomat (C)",
                    price=15.49,
                    currency="PLN",
                    delivery_days=2,
                    attributes={"source": "inpost", "service": "paczkomat", "size": "C"},
                )
            )
        if billable <= 30:
            products.append(
                RateProduct(
                    name="InPost Kurier Standard",
                    price=14.99,
                    currency="PLN",
                    delivery_days=2,
                    attributes={"source": "inpost", "service": "courier_standard"},
                )
            )
            products.append(
                RateProduct(
                    name="InPost Kurier Express",
                    price=19.99,
                    currency="PLN",
                    delivery_days=1,
                    attributes={"source": "inpost", "service": "courier_express"},
                )
            )
    else:
        if billable <= 30:
            products.append(
                RateProduct(
                    name="InPost International Standard",
                    price=39.99,
                    currency="PLN",
                    delivery_days=5,
                    attributes={"source": "inpost", "service": "international_standard"},
                )
            )
            products.append(
                RateProduct(
                    name="InPost International Express",
                    price=59.99,
                    currency="PLN",
                    delivery_days=3,
                    attributes={"source": "inpost", "service": "international_express"},
                )
            )
    return products


connector = InPostConnector()
if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        connector._fastapi,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )

if __name__ == "__main__":
    connector.run()

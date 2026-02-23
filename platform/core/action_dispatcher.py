"""Action Dispatcher -- routes workflow/flow actions to connector services via HTTP.

Resolves connector names to Docker service URLs and maps actions to
specific HTTP endpoints on each connector.
"""

import base64
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

DEFAULT_CONNECTOR_PORT = 8000
HTTP_TIMEOUT = 30.0


@dataclass
class ActionRoute:
    method: str
    path: str
    payload_key: str | None = None
    query_from_payload: list[str] = field(default_factory=list)


_ACTION_ROUTES: dict[str, dict[str, ActionRoute]] = {
    "email-client": {
        "email.send": ActionRoute(
            method="POST",
            path="/emails/send",
            query_from_payload=["account_name"],
        ),
        "email.fetch": ActionRoute(
            method="GET",
            path="/emails",
            query_from_payload=["account_name", "folder", "max_count", "unseen_only"],
        ),
        "email.get": ActionRoute(
            method="GET",
            path="/emails/{message_id}",
            query_from_payload=["account_name", "folder"],
        ),
        "email.mark_read": ActionRoute(
            method="PUT",
            path="/emails/{message_id}/read",
            query_from_payload=["account_name", "folder"],
        ),
        "email.delete": ActionRoute(
            method="DELETE",
            path="/emails/{message_id}",
            query_from_payload=["account_name", "folder"],
        ),
        "folder.list": ActionRoute(
            method="GET",
            path="/folders",
            query_from_payload=["account_name"],
        ),
    },
    "inpost": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "label.get": ActionRoute(method="GET", path="/shipments/{shipment_id}/label"),
        "shipment.cancel": ActionRoute(method="POST", path="/shipments/{shipment_id}/cancel"),
        "pickup_points.list": ActionRoute(method="GET", path="/pickup-points"),
        "return.create": ActionRoute(method="POST", path="/returns"),
    },
    "allegro": {
        "order.fetch": ActionRoute(method="GET", path="/orders"),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}"),
        "order.status_update": ActionRoute(method="PATCH", path="/orders/{order_id}/status"),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync"),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}"),
    },
    "shoper": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
    },
    "idosell": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "parcel.create": ActionRoute(method="POST", path="/parcels", query_from_payload=["account_name"]),
    },
    "pinquark-wms": {
        "article.create": ActionRoute(method="POST", path="/articles"),
        "article.delete": ActionRoute(method="DELETE", path="/articles/{article_id}"),
        "document.create": ActionRoute(method="POST", path="/documents"),
        "document.delete": ActionRoute(method="DELETE", path="/documents/{document_id}"),
        "contractor.create": ActionRoute(method="POST", path="/contractors"),
        "contractor.delete": ActionRoute(method="DELETE", path="/contractors/{contractor_id}"),
    },
    "ai-agent": {
        "agent.analyze": ActionRoute(method="POST", path="/analyze"),
        "agent.analyze_risk": ActionRoute(method="POST", path="/analyze/risk"),
        "agent.recommend_courier": ActionRoute(method="POST", path="/analyze/courier"),
        "agent.classify_priority": ActionRoute(method="POST", path="/analyze/priority"),
        "agent.extract_data": ActionRoute(method="POST", path="/analyze/extract"),
    },
    "baselinker": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "parcel.create": ActionRoute(method="POST", path="/parcels", query_from_payload=["account_name"]),
    },
    "raben": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{waybill_number}/status"),
        "shipment.cancel": ActionRoute(method="PUT", path="/shipments/{waybill_number}/cancel"),
        "tracking.get": ActionRoute(method="GET", path="/tracking/{waybill_number}"),
        "eta.get": ActionRoute(method="GET", path="/shipments/{waybill_number}/eta"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "claim.create": ActionRoute(method="POST", path="/claims"),
        "delivery_confirmation.get": ActionRoute(method="GET", path="/deliveries/{waybill_number}/confirmation"),
    },
    "skanuj-fakture": {
        "document.upload": ActionRoute(
            method="POST",
            path="/companies/{company_id}/documents",
            query_from_payload=["account_name", "single_document", "sale"],
        ),
        "document.list": ActionRoute(
            method="GET",
            path="/companies/{company_id}/documents",
            query_from_payload=["account_name", "document_statuses", "is_sale"],
        ),
        "document.get": ActionRoute(
            method="GET",
            path="/companies/{company_id}/documents/{document_id}",
            query_from_payload=["account_name"],
        ),
        "document.update": ActionRoute(
            method="PUT",
            path="/companies/{company_id}/documents/{document_id}",
            query_from_payload=["account_name"],
        ),
        "document.delete": ActionRoute(
            method="DELETE",
            path="/companies/{company_id}/documents",
            query_from_payload=["account_name"],
        ),
        "document.file.get": ActionRoute(
            method="GET",
            path="/companies/{company_id}/documents/{document_id}/file",
            query_from_payload=["account_name"],
        ),
        "document.image.get": ActionRoute(
            method="GET",
            path="/companies/{company_id}/documents/{document_id}/image",
            query_from_payload=["account_name"],
        ),
        "company.list": ActionRoute(
            method="GET",
            path="/companies",
            query_from_payload=["account_name"],
        ),
        "ksef.xml.get": ActionRoute(
            method="GET",
            path="/companies/{company_id}/documents/{document_id}/ksef-xml",
            query_from_payload=["account_name"],
        ),
        "ksef.invoice.send": ActionRoute(
            method="PUT",
            path="/companies/{company_id}/ksef/invoice",
            query_from_payload=["account_name"],
        ),
    },
}

_CONNECTOR_SERVICE_NAMES: dict[str, str] = {
    "email-client": "connector-email-client",
    "inpost": "connector-inpost",
    "dhl": "connector-dhl",
    "dpd": "connector-dpd",
    "allegro": "connector-allegro",
    "shoper": "connector-shoper",
    "idosell": "connector-idosell",
    "pinquark-wms": "connector-pinquark-wms",
    "ai-agent": "connector-ai-agent",
    "skanuj-fakture": "connector-skanuj-fakture",
    "baselinker": "connector-baselinker",
    "raben": "connector-raben",
}


_LIST_FIELDS: dict[str, dict[str, set[str]]] = {
    "email-client": {
        "email.send": {"to", "cc", "bcc"},
    },
}


_PRIORITY_MAP: dict[str, str] = {
    "1": "high", "2": "normal", "3": "low",
    "high": "high", "normal": "normal", "low": "low",
}


def _coerce_payload(
    connector_name: str, action: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Coerce payload field types to match connector expectations."""
    list_fields = _LIST_FIELDS.get(connector_name, {}).get(action, set())
    for field_name in list_fields:
        if field_name in payload and isinstance(payload[field_name], str):
            value = payload[field_name].strip()
            if "," in value:
                payload[field_name] = [v.strip() for v in value.split(",") if v.strip()]
            elif value:
                payload[field_name] = [value]
            else:
                payload[field_name] = []

    if connector_name == "email-client" and "priority" in payload:
        raw = str(payload["priority"]).strip().lower()
        payload["priority"] = _PRIORITY_MAP.get(raw, "normal")

    return payload


def _resolve_service_url(connector_name: str) -> str:
    service = _CONNECTOR_SERVICE_NAMES.get(
        connector_name, f"connector-{connector_name}"
    )
    return f"http://{service}:{DEFAULT_CONNECTOR_PORT}"


def _build_url(
    route: ActionRoute, base_url: str, payload: dict[str, Any]
) -> tuple[str, dict[str, str], dict[str, Any]]:
    """Build URL, query params, and remaining body from route + payload."""
    path = route.path
    body = dict(payload)

    for key in list(body.keys()):
        placeholder = "{" + key + "}"
        if placeholder in path:
            path = path.replace(placeholder, str(body.pop(key)))

    query_params: dict[str, str] = {}
    for qp in route.query_from_payload:
        if qp in body:
            query_params[qp] = str(body.pop(qp))

    return f"{base_url}{path}", query_params, body


async def _ensure_email_account(
    base_url: str, credentials: dict[str, str]
) -> str:
    """Ensure an email account exists on the connector, creating it if needed."""
    account_name = credentials.get("account_name", "default")
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{base_url}/accounts")
        existing = resp.json() if resp.status_code == 200 else []
        for acc in existing:
            if acc.get("name") == account_name:
                return account_name

        account_payload = {
            "name": account_name,
            "email_address": credentials.get("email_address", ""),
            "username": credentials.get("username", ""),
            "password": credentials.get("password", ""),
            "imap_host": credentials.get("imap_host", ""),
            "imap_port": int(credentials.get("imap_port", "993")),
            "smtp_host": credentials.get("smtp_host", ""),
            "smtp_port": int(credentials.get("smtp_port", "587")),
            "use_ssl": credentials.get("use_ssl", "true").lower() in ("true", "1", "yes"),
            "polling_folder": credentials.get("polling_folder", "INBOX"),
        }
        resp = await client.post(f"{base_url}/accounts", json=account_payload)
        if resp.status_code < 300:
            await logger.ainfo("email_account_provisioned", account=account_name)
        else:
            await logger.awarning(
                "email_account_provision_failed",
                account=account_name,
                status=resp.status_code,
                body=resp.text[:200],
            )
    return account_name


async def _ensure_skanuj_fakture_account(
    base_url: str, credentials: dict[str, str]
) -> str:
    """Ensure a SkanujFakture account exists on the connector, creating it if needed."""
    account_name = credentials.get("account_name", "default")
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{base_url}/accounts")
        existing = resp.json() if resp.status_code == 200 else []
        for acc in existing:
            if acc.get("name") == account_name:
                return account_name

        account_payload = {
            "name": account_name,
            "login": credentials.get("login", ""),
            "password": credentials.get("password", ""),
            "api_url": credentials.get("api_url", "https://skanujfakture.pl:8443/SFApi"),
            "company_id": int(cid) if (cid := credentials.get("company_id")) else None,
            "environment": credentials.get("environment", "production"),
        }
        resp = await client.post(f"{base_url}/accounts", json=account_payload)
        if resp.status_code < 300:
            await logger.ainfo("skanuj_fakture_account_provisioned", account=account_name)
        else:
            await logger.awarning(
                "skanuj_fakture_account_provision_failed",
                account=account_name,
                status=resp.status_code,
                body=resp.text[:200],
            )
    return account_name


def _extract_file_from_payload(body: dict[str, Any]) -> tuple[bytes, str] | None:
    """Extract file data from payload — handles attachment objects and raw base64."""
    file_data = body.pop("file", None)
    if file_data is None:
        return None

    if isinstance(file_data, list) and file_data:
        file_data = file_data[0]

    if isinstance(file_data, dict):
        content_b64 = file_data.get("content_base64", "")
        filename = file_data.get("filename", "document.pdf")
        if content_b64:
            return base64.b64decode(content_b64), filename

    if isinstance(file_data, str) and file_data:
        try:
            return base64.b64decode(file_data), "document.pdf"
        except Exception:
            pass

    return None


_MULTIPART_ACTIONS: set[str] = {"document.upload"}


async def dispatch_action(
    connector_name: str,
    action: str,
    payload: dict[str, Any],
    tenant_id: uuid.UUID,
    credentials: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Dispatch an action to a connector service via HTTP."""
    base_url = _resolve_service_url(connector_name)

    connector_routes = _ACTION_ROUTES.get(connector_name, {})
    route = connector_routes.get(action)

    if credentials:
        if connector_name == "email-client":
            account_name = await _ensure_email_account(base_url, credentials)
            if "account_name" not in payload:
                payload["account_name"] = account_name
        elif connector_name == "ai-agent":
            payload["credentials"] = {
                "gemini_api_key": credentials.get("gemini_api_key", ""),
                "model_name": credentials.get("model_name", "gemini-2.5-flash"),
            }
        elif connector_name == "skanuj-fakture":
            account_name = await _ensure_skanuj_fakture_account(base_url, credentials)
            payload["account_name"] = account_name
        elif "account_name" not in payload:
            account_name = credentials.get("account_name", "default")
            payload["account_name"] = account_name

    payload = _coerce_payload(connector_name, action, payload)

    if route is None:
        url = f"{base_url}/actions/{action}"
        await logger.ainfo(
            "action_dispatch_generic",
            connector=connector_name,
            action=action,
            url=url,
            tenant_id=str(tenant_id),
        )
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    url, query_params, body = _build_url(route, base_url, payload)

    await logger.ainfo(
        "action_dispatch",
        connector=connector_name,
        action=action,
        method=route.method,
        url=url,
        payload_keys=list(body.keys()),
        tenant_id=str(tenant_id),
    )

    use_multipart = action in _MULTIPART_ACTIONS and "file" in body

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        if use_multipart:
            file_result = _extract_file_from_payload(body)
            if file_result:
                file_bytes, filename = file_result
                files = {"file": (filename, file_bytes)}
                response = await client.post(url, files=files, params=query_params)
            else:
                response = await client.post(url, json=body, params=query_params)
        elif route.method == "GET":
            response = await client.get(url, params=query_params)
        elif route.method == "POST":
            response = await client.post(url, json=body, params=query_params)
        elif route.method == "PUT":
            response = await client.put(url, json=body, params=query_params)
        elif route.method == "PATCH":
            response = await client.patch(url, json=body, params=query_params)
        elif route.method == "DELETE":
            response = await client.delete(url, params=query_params)
        else:
            response = await client.post(url, json=body, params=query_params)

        if response.status_code == 422:
            detail = response.text[:1000]
            await logger.awarning(
                "action_dispatch_validation_error",
                connector=connector_name,
                action=action,
                url=url,
                status=422,
                detail=detail,
                sent_body={k: type(v).__name__ for k, v in body.items()},
            )

        response.raise_for_status()

        try:
            return response.json()
        except Exception:
            return {"status": "ok", "text": response.text[:2000]}

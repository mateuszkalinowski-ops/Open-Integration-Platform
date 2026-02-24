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
        "rates.get": ActionRoute(method="POST", path="/rates"),
    },
    "allegro": {
        "order.fetch": ActionRoute(method="GET", path="/orders"),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}"),
        "order.status_update": ActionRoute(method="PATCH", path="/orders/{order_id}/status"),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync"),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}"),
        "product.search": ActionRoute(method="GET", path="/products/search", query_from_payload=["account_name", "query", "page", "page_size"]),
    },
    "shoper": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "product.search": ActionRoute(method="GET", path="/products/search", query_from_payload=["account_name", "query", "page", "page_size"]),
    },
    "idosell": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "product.search": ActionRoute(method="GET", path="/products/search", query_from_payload=["account_name", "query", "page", "page_size"]),
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
    "amazon": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "product.search": ActionRoute(method="GET", path="/products/search", query_from_payload=["account_name", "query", "page", "page_size"]),
    },
    "baselinker": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "product.search": ActionRoute(method="GET", path="/products/search", query_from_payload=["account_name", "query", "page", "page_size"]),
        "parcel.create": ActionRoute(method="POST", path="/parcels", query_from_payload=["account_name"]),
    },
    "dhl": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{waybill_number}/status"),
        "shipment.cancel": ActionRoute(method="DELETE", path="/shipments/{waybill_number}"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "points.list": ActionRoute(method="GET", path="/points"),
        "rates.get": ActionRoute(method="POST", path="/rates"),
    },
    "dpd": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{waybill_number}/status"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "protocol.get": ActionRoute(method="POST", path="/protocol"),
        "rates.get": ActionRoute(method="POST", path="/rates"),
    },
    "fedex": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.cancel": ActionRoute(method="DELETE", path="/shipments/{order_id}"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "tracking.get": ActionRoute(method="GET", path="/tracking/{tracking_number}"),
        "points.list": ActionRoute(method="POST", path="/points"),
        "rates.get": ActionRoute(method="POST", path="/rates"),
    },
    "fedexpl": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{waybill_number}/status"),
        "label.get": ActionRoute(method="POST", path="/labels"),
    },
    "geis": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="POST", path="/shipments/status"),
        "shipment.detail": ActionRoute(method="POST", path="/shipments/detail"),
        "shipment.delete": ActionRoute(method="POST", path="/shipments/delete"),
        "shipment.assign_range": ActionRoute(method="POST", path="/shipments/assign-range"),
        "label.get": ActionRoute(method="POST", path="/labels"),
    },
    "gls": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{waybill_number}/status"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "rates.get": ActionRoute(method="POST", path="/rates"),
    },
    "orlenpaczka": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="POST", path="/shipments/status"),
        "shipment.cancel": ActionRoute(method="POST", path="/shipments/delete"),
        "tracking.get": ActionRoute(method="GET", path="/shipments/{order_id}/tracking"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "points.list": ActionRoute(method="POST", path="/points"),
    },
    "packeta": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="POST", path="/shipments/status"),
        "shipment.cancel": ActionRoute(method="POST", path="/shipments/delete"),
        "label.get": ActionRoute(method="POST", path="/labels"),
    },
    "paxy": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="POST", path="/shipments/status"),
        "shipment.cancel": ActionRoute(method="POST", path="/shipments/delete"),
        "label.get": ActionRoute(method="POST", path="/labels"),
    },
    "pocztapolska": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{order_id}/status"),
        "tracking.get": ActionRoute(method="GET", path="/shipments/{order_id}/tracking"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "points.list": ActionRoute(method="POST", path="/points"),
    },
    "schenker": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{waybill_number}/status"),
        "shipment.cancel": ActionRoute(method="DELETE", path="/shipments/{waybill_number}"),
        "tracking.get": ActionRoute(method="GET", path="/shipments/{waybill_number}/tracking"),
        "label.get": ActionRoute(method="POST", path="/labels"),
    },
    "sellasist": {
        "label.get": ActionRoute(method="POST", path="/labels"),
    },
    "suus": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="POST", path="/shipments/status"),
        "label.get": ActionRoute(method="POST", path="/labels"),
    },
    "ups": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="POST", path="/shipments/{waybill}/status"),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "documents.upload": ActionRoute(method="POST", path="/upload-documents"),
        "rates.get": ActionRoute(method="POST", path="/rates"),
    },
    "woocommerce": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name", "since", "page", "per_page"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "product.search": ActionRoute(method="GET", path="/products/search", query_from_payload=["account_name", "query", "page", "page_size"]),
        "products.sync": ActionRoute(method="POST", path="/products/sync", query_from_payload=["account_name"]),
    },
    "shopify": {
        "order.fetch": ActionRoute(method="GET", path="/orders", query_from_payload=["account_name", "since", "page", "per_page"]),
        "order.get": ActionRoute(method="GET", path="/orders/{order_id}", query_from_payload=["account_name"]),
        "order.status_update": ActionRoute(method="PUT", path="/orders/{order_id}/status", query_from_payload=["account_name"]),
        "order.fulfill": ActionRoute(method="POST", path="/orders/{order_id}/fulfill", query_from_payload=["account_name"]),
        "stock.sync": ActionRoute(method="POST", path="/stock/sync", query_from_payload=["account_name"]),
        "product.get": ActionRoute(method="GET", path="/products/{product_id}", query_from_payload=["account_name"]),
        "product.search": ActionRoute(method="GET", path="/products/search", query_from_payload=["account_name", "query", "page", "page_size"]),
        "products.sync": ActionRoute(method="POST", path="/products/sync", query_from_payload=["account_name"]),
    },
    "dhl-express": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{tracking_number}/status"),
        "label.get": ActionRoute(method="GET", path="/shipments/{tracking_number}/label"),
        "documents.get": ActionRoute(method="GET", path="/shipments/{tracking_number}/documents"),
        "rates.get": ActionRoute(method="POST", path="/rates/standardized"),
        "rates.raw": ActionRoute(method="POST", path="/rates"),
        "pickup.create": ActionRoute(method="POST", path="/pickups"),
        "pickup.cancel": ActionRoute(method="DELETE", path="/pickups/{dispatch_confirmation_number}"),
        "address.validate": ActionRoute(method="GET", path="/address-validate", query_from_payload=["countryCode", "postalCode", "cityName"]),
        "points.list": ActionRoute(method="GET", path="/points", query_from_payload=["countryCode", "postalCode", "city"]),
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
    "fxcouriers": {
        "shipment.create": ActionRoute(method="POST", path="/shipments"),
        "shipment.status": ActionRoute(method="GET", path="/shipments/{order_id}/status", query_from_payload=["api_token"]),
        "shipment.get": ActionRoute(method="GET", path="/shipments/{order_id}", query_from_payload=["api_token"]),
        "shipment.find_by_number": ActionRoute(method="GET", path="/shipments/by-number/{order_number}", query_from_payload=["api_token"]),
        "shipment.cancel": ActionRoute(method="DELETE", path="/shipments/{order_id}", query_from_payload=["api_token"]),
        "shipment.list": ActionRoute(method="GET", path="/shipments", query_from_payload=["api_token", "since", "offset", "company_id"]),
        "tracking.get": ActionRoute(method="GET", path="/tracking/{order_id}", query_from_payload=["api_token"]),
        "label.get": ActionRoute(method="POST", path="/labels"),
        "pickup.create": ActionRoute(method="POST", path="/pickups"),
        "pickup.get": ActionRoute(method="GET", path="/pickups/{order_id}", query_from_payload=["api_token"]),
        "pickup.cancel": ActionRoute(method="DELETE", path="/pickups/{order_id}", query_from_payload=["api_token"]),
        "services.list": ActionRoute(method="GET", path="/services", query_from_payload=["api_token"]),
        "company.get": ActionRoute(method="GET", path="/company/{company_id}", query_from_payload=["api_token"]),
    },
    "ftp-sftp": {
        "file.upload": ActionRoute(
            method="POST",
            path="/files/upload",
            query_from_payload=["account_name"],
        ),
        "file.download": ActionRoute(
            method="GET",
            path="/files/download",
            query_from_payload=["account_name", "remote_path"],
        ),
        "file.list": ActionRoute(
            method="GET",
            path="/files",
            query_from_payload=["account_name", "remote_path", "pattern"],
        ),
        "file.delete": ActionRoute(
            method="DELETE",
            path="/files",
            query_from_payload=["account_name"],
        ),
        "file.move": ActionRoute(
            method="POST",
            path="/files/move",
            query_from_payload=["account_name"],
        ),
        "directory.create": ActionRoute(
            method="POST",
            path="/directories",
            query_from_payload=["account_name"],
        ),
        "directory.list": ActionRoute(
            method="GET",
            path="/directories",
            query_from_payload=["account_name", "remote_path"],
        ),
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
    "dhl-express": "connector-dhl-express",
    "dpd": "connector-dpd",
    "fedex": "connector-fedex",
    "fedexpl": "connector-fedexpl",
    "geis": "connector-geis",
    "gls": "connector-gls",
    "orlenpaczka": "connector-orlenpaczka",
    "packeta": "connector-packeta",
    "paxy": "connector-paxy",
    "pocztapolska": "connector-pocztapolska",
    "schenker": "connector-schenker",
    "sellasist": "connector-sellasist",
    "suus": "connector-suus",
    "ups": "connector-ups",
    "allegro": "connector-allegro",
    "amazon": "connector-amazon",
    "shoper": "connector-shoper",
    "idosell": "connector-idosell",
    "baselinker": "connector-baselinker",
    "woocommerce": "connector-woocommerce",
    "shopify": "connector-shopify",
    "pinquark-wms": "connector-pinquark-wms",
    "ai-agent": "connector-ai-agent",
    "ftp-sftp": "connector-ftp-sftp",
    "skanuj-fakture": "connector-skanuj-fakture",
    "raben": "connector-raben",
    "fxcouriers": "connector-fxcouriers",
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


async def _ensure_ftp_sftp_account(
    base_url: str, credentials: dict[str, str]
) -> str:
    """Ensure an FTP/SFTP account exists on the connector, creating it if needed."""
    account_name = credentials.get("account_name", "default")
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{base_url}/accounts")
        existing = resp.json() if resp.status_code == 200 else []
        for acc in existing:
            if acc.get("name") == account_name:
                return account_name

        account_payload = {
            "name": account_name,
            "host": credentials.get("host", ""),
            "protocol": credentials.get("protocol", "sftp"),
            "port": int(credentials.get("port", "0")),
            "username": credentials.get("username", ""),
            "password": credentials.get("password", ""),
            "private_key": credentials.get("private_key", ""),
            "passive_mode": credentials.get("passive_mode", "true").lower() in ("true", "1", "yes"),
            "base_path": credentials.get("base_path", "/"),
            "environment": credentials.get("environment", "production"),
        }
        resp = await client.post(f"{base_url}/accounts", json=account_payload)
        if resp.status_code < 300:
            await logger.ainfo("ftp_sftp_account_provisioned", account=account_name)
        else:
            await logger.awarning(
                "ftp_sftp_account_provision_failed",
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
        elif connector_name == "fxcouriers":
            payload["api_token"] = credentials.get("api_token", "")
            if "credentials" not in payload:
                payload["credentials"] = {
                    "api_token": credentials.get("api_token", ""),
                    "company_id": credentials.get("company_id"),
                }
        elif connector_name == "skanuj-fakture":
            account_name = await _ensure_skanuj_fakture_account(base_url, credentials)
            payload["account_name"] = account_name
        elif connector_name == "ftp-sftp":
            account_name = await _ensure_ftp_sftp_account(base_url, credentials)
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

    requires_file = action in _MULTIPART_ACTIONS

    if requires_file and "file" not in body:
        raise ValueError(
            f"Action '{action}' on connector '{connector_name}' requires a file "
            f"attachment, but no 'file' field was found in the payload. "
            f"Ensure that the source node provides a file (e.g. an email "
            f"attachment) and that the field mapping maps it to the 'file' field."
        )

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        if requires_file:
            file_result = _extract_file_from_payload(body)
            if file_result:
                file_bytes, filename = file_result
                files = {"file": (filename, file_bytes)}
                response = await client.post(url, files=files, params=query_params)
            else:
                raise ValueError(
                    f"Action '{action}' on connector '{connector_name}' requires a "
                    f"file attachment, but the provided 'file' field could not be "
                    f"decoded. Expected a base64-encoded string or an object with "
                    f"'content_base64' and 'filename' keys."
                )
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

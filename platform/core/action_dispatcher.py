"""Action Dispatcher -- routes workflow/flow actions to connector services via HTTP.

Fully generic: reads action_routes, service_name, credential_provisioning,
and payload_hints from each connector's manifest (connector.yaml) via the
ConnectorRegistry.  No per-connector logic lives here.
"""

import asyncio
import base64
import json
import re
import uuid
from typing import Any

import httpx
import structlog
from fastapi import HTTPException

from core.connector_registry import ConnectorManifest, ConnectorRegistry, DEFAULT_CONNECTOR_PORT

logger = structlog.get_logger()

HTTP_TIMEOUT = 30.0
_MAX_429_RETRIES = 3
_DEFAULT_RETRY_AFTER = 2.0
_rate_limiter: Any | None = None


def set_rate_limiter(rate_limiter: Any | None) -> None:
    """Register the shared connector rate limiter used by dispatch_action()."""
    global _rate_limiter
    _rate_limiter = rate_limiter


_CONNECTOR_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,62}$")


def _resolve_service_url(
    connector_name: str,
    registry: ConnectorRegistry | None = None,
    connector_version: str | None = None,
) -> str:
    if not _CONNECTOR_NAME_RE.match(connector_name):
        raise ValueError(f"Invalid connector_name: {connector_name!r}")
    if registry:
        manifest = registry.get_by_name_version(connector_name, connector_version)
        if manifest:
            return manifest.base_url
    return f"http://connector-{connector_name}:{DEFAULT_CONNECTOR_PORT}"


def _field_to_header_name(field: str) -> str:
    """Convert a payload field name to an X-prefixed HTTP header name.

    ``api_token`` -> ``X-Api-Token``, ``username`` -> ``X-Username``.
    """
    return "X-" + "-".join(part.capitalize() for part in field.split("_"))


def _build_url(
    route: dict, base_url: str, payload: dict[str, Any]
) -> tuple[str, dict[str, Any], dict[str, str], dict[str, Any]]:
    """Build URL, query params, extra headers, and remaining body from route + payload.

    List values are preserved so httpx sends them as multi-value query params
    (e.g. ?contractor=A&contractor=B).  None values are dropped.
    """
    path: str = route["path"]
    body = dict(payload)

    for key in list(body.keys()):
        placeholder = "{" + key + "}"
        if placeholder in path:
            path = path.replace(placeholder, str(body.pop(key)))

    query_params: dict[str, Any] = {}
    for qp in route.get("query_from_payload", []):
        if qp in body:
            val = body.pop(qp)
            if val is not None:
                query_params[qp] = val

    extra_headers: dict[str, str] = {}
    for hp in route.get("header_from_payload", []):
        if hp in body:
            val = body.pop(hp)
            if val is not None:
                extra_headers[_field_to_header_name(hp)] = str(val)

    return f"{base_url}{path}", query_params, extra_headers, body


def _coerce_payload(
    manifest: ConnectorManifest | None,
    action: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Coerce payload field types using payload_hints from connector.yaml."""
    if not manifest or not manifest.payload_hints:
        return payload

    hints = manifest.payload_hints

    list_fields = hints.get("list_fields", {}).get(action, [])
    for field_name in list_fields:
        if field_name in payload and isinstance(payload[field_name], str):
            value = payload[field_name].strip()
            if "," in value:
                payload[field_name] = [v.strip() for v in value.split(",") if v.strip()]
            elif value:
                payload[field_name] = [value]
            else:
                payload[field_name] = []

    enum_fields = hints.get("enum_fields", {}).get(action, {})
    for field_name, enum_config in enum_fields.items():
        if field_name in payload:
            mapping = enum_config.get("values", {})
            default = enum_config.get("default", payload[field_name])
            raw = str(payload[field_name]).strip().lower()
            payload[field_name] = mapping.get(raw, default)

    return payload


def _apply_credential_mapping(
    credentials: dict[str, str], mapping: dict
) -> dict[str, Any]:
    """Build an account payload from credential_mapping config."""
    result: dict[str, Any] = {}
    for target_key, source_spec in mapping.items():
        if isinstance(source_spec, str):
            result[target_key] = credentials.get(source_spec, "")
        elif isinstance(source_spec, dict):
            source_field = source_spec.get("source", target_key)
            raw = credentials.get(source_field, "")
            field_type = source_spec.get("type", "string")
            default = source_spec.get("default")

            if not raw and default is not None:
                result[target_key] = default
            elif field_type == "integer":
                try:
                    result[target_key] = int(raw) if raw else (default if default is not None else None)
                except (ValueError, TypeError):
                    result[target_key] = default
            elif field_type == "boolean":
                if isinstance(raw, str):
                    result[target_key] = raw.lower() in ("true", "1", "yes")
                else:
                    result[target_key] = bool(raw) if raw else (default if default is not None else False)
            else:
                result[target_key] = raw or (default if default is not None else "")
    return result


async def _ensure_account_generic(
    base_url: str,
    credentials: dict[str, str],
    provisioning: dict,
    *,
    force_update: bool = False,
) -> str:
    """Generic account provisioning driven by credential_provisioning config."""
    mapping = provisioning.get("credential_mapping", {})
    account_endpoint = provisioning.get("account_endpoint", "/accounts")

    account_name = credentials.get("account_name", "default")
    account_payload = _apply_credential_mapping(credentials, mapping)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{base_url}{account_endpoint}")
        existing: list[dict[str, Any]] = []
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                existing = data
            elif isinstance(data, dict) and isinstance(data.get("accounts"), list):
                existing = data["accounts"]
        already_exists = any(acc.get("name") == account_name for acc in existing)

        if already_exists and force_update:
            resp = await client.put(
                f"{base_url}{account_endpoint}/{account_name}",
                json=account_payload,
            )
            if resp.status_code < 300:
                await logger.ainfo("account_updated", account=account_name)
            else:
                await logger.awarning(
                    "account_update_failed", account=account_name,
                    status=resp.status_code,
                )
        elif already_exists:
            return account_name
        else:
            resp = await client.post(
                f"{base_url}{account_endpoint}", json=account_payload
            )
            if resp.status_code < 300:
                await logger.ainfo("account_provisioned", account=account_name)
            else:
                await logger.awarning(
                    "account_provision_failed", account=account_name,
                    status=resp.status_code,
                )
    return account_name


async def _provision_credentials(
    base_url: str,
    connector_name: str,
    payload: dict[str, Any],
    credentials: dict[str, str],
    manifest: ConnectorManifest | None,
) -> dict[str, Any]:
    """Inject credentials into payload based on credential_provisioning config."""
    provisioning = manifest.credential_provisioning if manifest else {}
    mode = provisioning.get("mode", "none")

    if mode == "account":
        account_name = await _ensure_account_generic(
            base_url, credentials, provisioning
        )
        field = provisioning.get("payload_field", "account_name")
        payload[field] = account_name

    elif mode == "inject":
        mapping = provisioning.get("credential_mapping", {})
        for target_key, source_spec in mapping.items():
            source_field = source_spec if isinstance(source_spec, str) else source_spec.get("source", target_key)
            if source_field in credentials:
                payload[target_key] = credentials[source_field]
        if "credentials" not in payload:
            payload["credentials"] = {
                k: credentials.get(
                    v if isinstance(v, str) else v.get("source", k), ""
                )
                for k, v in mapping.items()
            }

    elif mode == "inject_nested":
        inject_key = provisioning.get("inject_key", "credentials")
        mapping = provisioning.get("credential_mapping", {})
        nested: dict[str, Any] = {}
        for target_key, source_spec in mapping.items():
            if isinstance(source_spec, str):
                nested[target_key] = credentials.get(source_spec, "")
            elif isinstance(source_spec, dict):
                src = source_spec.get("source", target_key)
                nested[target_key] = credentials.get(src, "") or source_spec.get("default", "")
        payload[inject_key] = nested

    else:
        if "account_name" not in payload:
            payload["account_name"] = credentials.get("account_name", "default")

    return payload


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
            logger.warning("Failed to base64-decode file payload for extraction")

    return None


def _parse_retry_after(response: httpx.Response) -> float:
    """Extract wait time from Retry-After header (seconds or HTTP-date)."""
    raw = response.headers.get("retry-after", "")
    if not raw:
        return _DEFAULT_RETRY_AFTER
    try:
        return max(0.5, min(float(raw), 120.0))
    except (ValueError, TypeError):
        return _DEFAULT_RETRY_AFTER


async def _execute_with_429_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    connector_name: str,
    action: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    files: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> httpx.Response:
    """Execute an HTTP request with automatic retry on 429 Too Many Requests."""
    for attempt in range(_MAX_429_RETRIES + 1):
        if files is not None:
            response = await client.post(url, files=files, data=data, params=params, headers=headers)
        elif method == "GET":
            response = await client.get(url, params=params, headers=headers)
        elif method == "POST":
            response = await client.post(url, json=json_body, params=params, headers=headers)
        elif method == "PUT":
            response = await client.put(url, json=json_body, params=params, headers=headers)
        elif method == "PATCH":
            response = await client.patch(url, json=json_body, params=params, headers=headers)
        elif method == "DELETE":
            response = await client.delete(url, params=params, headers=headers)
        else:
            response = await client.post(url, json=json_body, params=params, headers=headers)

        if response.status_code != 429 or attempt >= _MAX_429_RETRIES:
            return response

        wait = _parse_retry_after(response)
        await logger.awarning(
            "action_dispatch_429_retry",
            connector=connector_name,
            action=action,
            attempt=attempt + 1,
            retry_after_s=wait,
        )
        await asyncio.sleep(wait)

    return response  # type: ignore[possibly-undefined]


async def dispatch_action(
    connector_name: str,
    action: str,
    payload: dict[str, Any],
    tenant_id: uuid.UUID,
    credentials: dict[str, str] | None = None,
    registry: ConnectorRegistry | None = None,
    connector_version: str | None = None,
) -> dict[str, Any]:
    """Dispatch an action to a connector service via HTTP.

    Fully generic — all routing, credential provisioning, and payload
    coercion is driven by connector.yaml via the registry.

    When *connector_version* is provided, the exact manifest version is
    used; otherwise the latest discovered version is selected.
    """
    manifest: ConnectorManifest | None = None
    if registry:
        manifest = registry.get_by_name_version(connector_name, connector_version)

    base_url = manifest.base_url if manifest else _resolve_service_url(
        connector_name, registry, connector_version
    )

    if _rate_limiter is not None:
        rl_result = await _rate_limiter.check(
            connector_name,
            action,
            str(tenant_id),
            connector_version=connector_version,
        )
        if not rl_result.allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "CONNECTOR_RATE_LIMITED",
                    "message": f"Rate limit exceeded for {connector_name}/{action}",
                    "retry_after": rl_result.retry_after,
                    "limit": rl_result.limit,
                    "window_seconds": rl_result.window_seconds,
                },
            )

    route: dict | None = None
    if manifest and manifest.action_routes:
        route = manifest.action_routes.get(action)

    if credentials:
        payload = await _provision_credentials(
            base_url, connector_name, payload, credentials, manifest
        )

    payload = _coerce_payload(manifest, action, payload)

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
            response = await _execute_with_429_retry(
                client, "POST", url, connector_name, action,
                json_body=payload,
            )
            response.raise_for_status()
            return response.json()

    url, query_params, extra_headers, body = _build_url(route, base_url, payload)

    await logger.ainfo(
        "action_dispatch",
        connector=connector_name,
        action=action,
        method=route["method"],
        url=url,
        payload_keys=list(body.keys()),
        tenant_id=str(tenant_id),
    )

    requires_file = route.get("multipart", False)

    if requires_file and "file" not in body:
        raise ValueError(
            f"Action '{action}' on connector '{connector_name}' requires a file "
            f"attachment, but no 'file' field was found in the payload. "
            f"Ensure that the source node provides a file (e.g. an email "
            f"attachment) and that the field mapping maps it to the 'file' field."
        )

    method = route["method"]

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        if requires_file:
            file_result = _extract_file_from_payload(body)
            if file_result:
                file_bytes, filename = file_result
                files = {"file": (filename, file_bytes)}
                remaining = {
                    k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v))
                    for k, v in body.items()
                    if k != "file" and v is not None
                }
                response = await _execute_with_429_retry(
                    client, "POST", url, connector_name, action,
                    files=files, data=remaining, params=query_params,
                    headers=extra_headers or None,
                )
            else:
                raise ValueError(
                    f"Action '{action}' on connector '{connector_name}' requires a "
                    f"file attachment, but the provided 'file' field could not be "
                    f"decoded. Expected a base64-encoded string or an object with "
                    f"'content_base64' and 'filename' keys."
                )
        else:
            response = await _execute_with_429_retry(
                client, method, url, connector_name, action,
                json_body=body, params=query_params,
                headers=extra_headers or None,
            )

        if response.status_code == 422:
            await logger.awarning(
                "action_dispatch_validation_error",
                connector=connector_name,
                action=action,
                url=url,
                status=422,
                sent_body={k: type(v).__name__ for k, v in body.items()},
            )

        response.raise_for_status()

        try:
            return response.json()
        except Exception:
            await logger.awarning(
                "action_dispatch_non_json_response",
                connector=connector_name,
                action=action,
                status=response.status_code,
                content_type=response.headers.get("content-type", ""),
            )
            return {"status": "ok", "raw_response": True, "status_code": response.status_code}

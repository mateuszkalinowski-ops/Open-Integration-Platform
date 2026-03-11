"""Helpers for incrementally migrating legacy FastAPI connectors to the SDK."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import httpx
import yaml
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from pinquark_connector_sdk.accounts import register_account_routes
from pinquark_connector_sdk.metrics import register_metrics


def augment_legacy_fastapi_app(
    app: FastAPI,
    *,
    manifest_path: str | Path,
    register_metrics_endpoint: bool = False,
    register_account_api_if_missing: bool = False,
) -> FastAPI:
    """Add SDK-compatible action endpoints to an existing FastAPI app.

    The bridge keeps existing legacy routes intact and exposes parallel
    `/actions/*` endpoints derived from `connector.yaml`. This provides an
    incremental migration path where the platform can rely on SDK-style action
    dispatch without forcing a full rewrite of each connector's transport layer.
    """

    manifest = _load_manifest(manifest_path)
    existing_paths = {getattr(route, "path", "") for route in app.routes}

    if register_metrics_endpoint and "/metrics" not in existing_paths:
        register_metrics(app, manifest["name"])

    if register_account_api_if_missing and "/accounts" not in existing_paths:
        register_account_routes(app, _LegacyConnectionAdapter())

    for action_name, route in (manifest.get("action_routes") or {}).items():
        action_path = f"/actions/{action_name.replace('.', '/')}"
        if action_path in existing_paths:
            continue
        _register_action_proxy(app, action_name, route)

    return app


class _LegacyConnectionAdapter:
    async def test_connection(self) -> bool:
        raise NotImplementedError


def _load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid connector manifest: {path}")
    return data


def _register_action_proxy(app: FastAPI, action_name: str, route: dict[str, Any]) -> None:
    method = str(route.get("method", "POST")).upper()

    @app.post(f"/actions/{action_name.replace('.', '/')}", tags=["actions"], name=f"legacy_action_{action_name}")
    async def action_proxy(request: Request) -> Response:
        payload = await request.json()
        url_path, query_params, body = _build_request(route, payload)

        files = None
        data = None
        json_body = body
        if route.get("multipart"):
            files, data = _extract_multipart(body)
            json_body = None

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://legacy-connector",
        ) as client:
            response = await client.request(
                method,
                url_path,
                params=query_params or None,
                json=json_body if method != "GET" else None,
                files=files,
                data=data,
            )

        return _copy_response(response)


def _build_request(route: dict[str, Any], payload: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    body = dict(payload)
    path = route["path"]

    placeholders = [part[1:-1] for part in path.split("/") if part.startswith("{") and part.endswith("}")]
    for placeholder in placeholders:
        value = body.pop(placeholder, None)
        if value is None:
            raise ValueError(f"Missing path parameter '{placeholder}' for route {path}")
        path = path.replace(f"{{{placeholder}}}", str(value))

    query_params: dict[str, Any] = {}
    for field_name in route.get("query_from_payload", []):
        if field_name in body:
            query_params[field_name] = body.pop(field_name)

    return path, query_params, body


def _extract_multipart(body: dict[str, Any]) -> tuple[dict[str, tuple[str, bytes]], dict[str, str]]:
    file_value = body.get("file")
    if file_value is None:
        raise ValueError("Multipart action requires 'file' in payload")

    filename = "upload.bin"
    content_bytes: bytes
    if isinstance(file_value, str):
        content_bytes = base64.b64decode(file_value)
    elif isinstance(file_value, dict) and isinstance(file_value.get("content_base64"), str):
        filename = str(file_value.get("filename") or filename)
        content_bytes = base64.b64decode(file_value["content_base64"])
    else:
        raise ValueError("Unsupported multipart file payload")

    remaining = {
        key: json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        for key, value in body.items()
        if key != "file" and value is not None
    }
    return {"file": (filename, content_bytes)}, remaining


def _copy_response(response: httpx.Response) -> Response:
    headers: dict[str, str] = {}
    content_type = response.headers.get("content-type")
    if content_type:
        headers["content-type"] = content_type

    if content_type and "application/json" in content_type:
        return JSONResponse(status_code=response.status_code, content=response.json(), headers=headers)

    return Response(content=response.content, status_code=response.status_code, headers=headers)

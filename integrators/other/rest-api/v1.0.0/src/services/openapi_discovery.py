"""Auto-discovery of endpoints from OpenAPI/Swagger specs."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from src.schemas.common import DiscoveredEndpoint, RestDiscoverResponse

logger = logging.getLogger(__name__)

PROBE_PATHS = [
    "/openapi.json",
    "/swagger.json",
    "/api-docs",
    "/v3/api-docs",
    "/.well-known/openapi",
]

ALIAS_MAP: dict[str, str] = {
    "tos_notification_rail_save": "awk.create",
    "tos_notification_rail_approve": "awk.approve",
    "tos_notification_rail_cancel": "awk.cancel",
    "tos_notification_rail_copy": "awk.copy",
    "tos_notification_rail_create_outbound": "awk.create_outbound",
    "tos_notification_road_save": "awd.create",
    "tos_notification_road_approve": "awd.approve",
    "tos_notification_road_cancel": "awd.cancel",
    "tos_train_wagon_add": "train.add_wagon",
    "tos_train_container_add": "train.add_container",
    "tos_logistic_unit_save": "logistic_unit.save",
    "tos_gate_rail_entry_confirm": "gate.rail_entry_confirm",
    "tos_gate_rail_entry_reject": "gate.rail_entry_reject",
    "tos_gate_rail_exit_confirm": "gate.rail_exit_confirm",
    "tos_gate_road_entry_confirm": "gate.road_entry_confirm",
    "tos_gate_road_entry_reject": "gate.road_entry_reject",
    "tos_gate_road_exit_confirm": "gate.road_exit_confirm",
    "tos_gate_road_zdb_confirm": "gate.road_zdb_confirm",
    "tos_gate_ocr_override": "gate.ocr_override",
    "tos_gate_assign_track": "gate.assign_track",
    "tos_movement_save": "movement.save",
    "tos_movement_execute": "movement.execute",
    "tos_movement_complete": "movement.complete",
    "tos_operation_start": "operation.start",
    "tos_operation_complete": "operation.complete",
    "tos_zt_rail_save": "zt_rail.save",
    "tos_zt_change_status": "zt.change_status",
    "tos_damage_report_save": "damage.report",
    "tos_photo_save": "photo.save",
    "tos_doc_file_add": "doc.file_add",
    "tos_doc_set_status": "doc.set_status",
    "tos_validate_vehicle_number": "validate.vehicle_number",
    "tos_validate_container_code": "validate.container_code",
    "tos_validate_slot_availability": "validate.slot_availability",
    "tos_doc_get_status": "doc.get_status",
    "tos_container_get_status": "container.get_status",
    "tos_get_events_since": "events.poll",
    "tos_get_doc_status_changes_since": "doc_status_changes.poll",
}


class OpenAPIDiscovery:
    """Discovers endpoints from OpenAPI/Swagger specification of a target system."""

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    async def discover(
        self,
        base_url: str,
        path_prefix: str = "",
        auth_headers: dict[str, str] | None = None,
        openapi_url: str = "",
        generate_aliases: bool = True,
    ) -> RestDiscoverResponse:
        probe_paths = [openapi_url] if openapi_url else self._build_probe_paths(path_prefix)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for probe_path in probe_paths:
                url = probe_path if probe_path.startswith("http") else f"{base_url.rstrip('/')}{probe_path}"
                spec = await self._try_fetch_spec(client, url, auth_headers or {})
                if spec:
                    endpoints = self._parse_spec(spec, path_prefix, generate_aliases)
                    openapi_version = spec.get("openapi", spec.get("swagger", "unknown"))
                    return RestDiscoverResponse(
                        status="success",
                        found=True,
                        openapi_url=url,
                        openapi_version=str(openapi_version),
                        endpoints=endpoints,
                        count=len(endpoints),
                        message=f"Discovered {len(endpoints)} endpoints from {url}",
                    )

        return RestDiscoverResponse(
            status="success",
            found=False,
            message="No OpenAPI specification found at any probed path",
        )

    def _build_probe_paths(self, path_prefix: str) -> list[str]:
        paths = list(PROBE_PATHS)
        if path_prefix:
            paths.append(f"{path_prefix.rstrip('/')}/openapi.json")
        return paths

    async def _try_fetch_spec(
        self,
        client: httpx.AsyncClient,
        url: str,
        auth_headers: dict[str, str],
    ) -> dict[str, Any] | None:
        try:
            response = await client.get(url, headers=auth_headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
                    logger.info("Found OpenAPI spec at %s", url)
                    return data
        except Exception:
            logger.debug("No spec at %s", url, exc_info=True)
        return None

    def _parse_spec(
        self,
        spec: dict[str, Any],
        path_prefix: str,
        generate_aliases: bool,
    ) -> list[DiscoveredEndpoint]:
        endpoints: list[DiscoveredEndpoint] = []
        http_methods = {"get", "post", "put", "patch", "delete"}

        for path, methods in spec.get("paths", {}).items():
            if not isinstance(methods, dict):
                continue

            for method, operation in methods.items():
                if method not in http_methods:
                    continue
                if not isinstance(operation, dict):
                    continue

                clean_path = path
                if path_prefix and clean_path.startswith(path_prefix):
                    clean_path = clean_path[len(path_prefix) :]
                endpoint_name = clean_path.strip("/")

                description = operation.get("summary", "") or operation.get("description", "")
                if isinstance(description, str) and len(description) > 200:
                    description = description[:200] + "..."

                input_schema = self._extract_request_schema(operation, spec)
                output_schema = self._extract_response_schema(operation, spec)

                alias = ""
                if generate_aliases:
                    alias = ALIAS_MAP.get(endpoint_name, self._auto_alias(endpoint_name))

                endpoints.append(
                    DiscoveredEndpoint(
                        endpoint=endpoint_name,
                        method=method.upper(),
                        description=description,
                        alias=alias,
                        input_schema=input_schema,
                        output_schema=output_schema,
                    )
                )

        return endpoints

    def _extract_request_schema(self, operation: dict, spec: dict) -> dict[str, Any]:
        request_body = operation.get("requestBody", {})
        if not isinstance(request_body, dict):
            return {}

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        return self._resolve_ref(schema, spec)

    def _extract_response_schema(self, operation: dict, spec: dict) -> dict[str, Any]:
        responses = operation.get("responses", {})
        for status_code in ("200", "201", "default"):
            response_def = responses.get(status_code, {})
            if not isinstance(response_def, dict):
                continue
            content = response_def.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            if schema:
                return self._resolve_ref(schema, spec)
        return {}

    def _resolve_ref(self, schema: dict[str, Any], spec: dict) -> dict[str, Any]:
        """Resolve a single level of $ref in an OpenAPI schema."""
        if not isinstance(schema, dict):
            return {}
        ref = schema.get("$ref")
        if not ref or not isinstance(ref, str):
            return schema

        parts = ref.lstrip("#/").split("/")
        current: Any = spec
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return schema
        return current if isinstance(current, dict) else schema

    def _auto_alias(self, endpoint: str) -> str:
        """Generate a readable alias from an endpoint path."""
        clean = endpoint.replace("/", ".").replace("-", "_")
        clean = re.sub(r"[{}]", "", clean)
        clean = re.sub(r"\.+", ".", clean).strip(".")
        return clean

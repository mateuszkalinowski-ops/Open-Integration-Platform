"""Dynamic schema registry with Redis cache, diffing, and change detection."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

import httpx

from config import settings
from core.connector_registry import ConnectorRegistry

logger = logging.getLogger(__name__)

SchemaChangeHandler = Callable[[dict[str, Any]], Awaitable[None]]
MappingInvalidator = Callable[[str | None], Awaitable[None]]


class SchemaRegistry:
    def __init__(
        self,
        registry: ConnectorRegistry,
        redis_getter: Callable[[], Awaitable[Any]],
        *,
        mapping_invalidator: MappingInvalidator | None = None,
        change_handler: SchemaChangeHandler | None = None,
        refresh_interval_seconds: int | None = None,
    ) -> None:
        self._registry = registry
        self._redis_getter = redis_getter
        self._mapping_invalidator = mapping_invalidator
        self._change_handler = change_handler
        self._refresh_interval_seconds = refresh_interval_seconds or settings.schema_registry_refresh_interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._observed_schemas: dict[str, dict[str, str | None]] = {}

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._refresh_loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def get_action_schema(
        self,
        connector_name: str,
        action: str,
        *,
        connector_version: str | None = None,
        tenant_id: str | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        manifest = self._registry.get_by_name_version(connector_name, connector_version)
        if not manifest:
            raise LookupError(f"Connector '{connector_name}' not found")

        cache_key = self._cache_key(connector_name, action, tenant_id)
        self._observed_schemas[cache_key] = {
            "connector_name": connector_name,
            "action": action,
            "connector_version": manifest.version,
            "tenant_id": tenant_id,
        }

        redis = await self._redis_getter()
        if not force_refresh:
            cached_raw = await redis.get(cache_key)
            if cached_raw:
                try:
                    payload = json.loads(cached_raw)
                    payload["cached"] = True
                    return payload
                except (TypeError, json.JSONDecodeError):
                    logger.warning("Invalid cached schema payload for key=%s", cache_key)

        payload = await self._build_schema_payload(manifest, action, tenant_id)
        await redis.set(cache_key, json.dumps(payload), ex=settings.schema_registry_ttl_seconds)
        return payload

    def diff_schemas(
        self,
        previous: dict[str, Any] | None,
        current: dict[str, Any] | None,
    ) -> dict[str, Any]:
        previous = previous or {}
        current = current or {}
        diff = {
            "input_fields": self._diff_field_sets(previous.get("input_fields", []), current.get("input_fields", [])),
            "output_fields": self._diff_field_sets(previous.get("output_fields", []), current.get("output_fields", [])),
        }
        diff["changed"] = any(section["changed"] for section in diff.values())
        return diff

    async def refresh_observed_schemas(self) -> None:
        if not self._observed_schemas:
            return
        redis = await self._redis_getter()
        for cache_key, descriptor in list(self._observed_schemas.items()):
            cached_payload = await self._load_cached_payload(redis, cache_key)
            try:
                fresh_payload = await self.get_action_schema(
                    str(descriptor["connector_name"]),
                    str(descriptor["action"]),
                    connector_version=self._opt_str(descriptor.get("connector_version")),
                    tenant_id=self._opt_str(descriptor.get("tenant_id")),
                    force_refresh=True,
                )
            except LookupError:
                continue
            diff = self.diff_schemas(cached_payload, fresh_payload)
            if not diff["changed"]:
                continue
            if self._mapping_invalidator is not None:
                await self._mapping_invalidator(str(descriptor["connector_name"]))
            change_event = {
                "connector_name": descriptor["connector_name"],
                "action": descriptor["action"],
                "connector_version": descriptor.get("connector_version"),
                "tenant_id": descriptor.get("tenant_id"),
                "diff": diff,
            }
            if self._change_handler is not None:
                await self._change_handler(change_event)
            else:
                logger.info("schema_registry.schema_changed", extra=change_event)

    async def _refresh_loop(self) -> None:
        consecutive_failures = 0
        while True:
            try:
                await self.refresh_observed_schemas()
                consecutive_failures = 0
            except Exception:
                consecutive_failures += 1
                logger.exception("schema_registry.refresh_failed", consecutive_failures=consecutive_failures)
            backoff = min(
                self._refresh_interval_seconds * (2 ** min(consecutive_failures, 5)),
                self._refresh_interval_seconds * 32,
            ) if consecutive_failures > 0 else self._refresh_interval_seconds
            await asyncio.sleep(backoff)

    async def _build_schema_payload(
        self,
        manifest: Any,
        action: str,
        tenant_id: str | None,
    ) -> dict[str, Any]:
        static_input = self._normalize_fields(manifest.action_fields.get(action, []))
        static_output = self._normalize_fields(manifest.output_fields.get(action, []))

        dynamic_input: list[dict[str, Any]] = []
        dynamic_output: list[dict[str, Any]] = []
        source = "static"

        dynamic_payload = await self._fetch_dynamic_schema(manifest.base_url, action)
        if dynamic_payload:
            dynamic_input = self._normalize_fields(dynamic_payload.get("input_fields", []))
            dynamic_output = self._normalize_fields(dynamic_payload.get("output_fields", []))
            source = "merged" if static_input or static_output else "dynamic"

        return {
            "connector_name": manifest.name,
            "connector_version": manifest.version,
            "tenant_id": tenant_id,
            "action": action,
            "source": source,
            "cached": False,
            "input_fields": self._merge_fields(static_input, dynamic_input),
            "output_fields": self._merge_fields(static_output, dynamic_output),
        }

    async def _load_cached_payload(self, redis: Any, cache_key: str) -> dict[str, Any] | None:
        cached_raw = await redis.get(cache_key)
        if not cached_raw:
            return None
        try:
            return json.loads(cached_raw)
        except (TypeError, json.JSONDecodeError):
            return None

    async def _fetch_dynamic_schema(self, base_url: str, action: str) -> dict[str, Any] | None:
        action_path = action.replace(".", "/")
        url = f"{base_url}/schema/{action_path}"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, read=10.0)) as client:
                response = await client.get(url)
            if response.status_code != 200:
                return None
            data = response.json()
            if isinstance(data, dict):
                return data
        except Exception:
            return None
        return None

    def _cache_key(self, connector_name: str, action: str, tenant_id: str | None) -> str:
        tenant_part = tenant_id or "global"
        return f"schema:{connector_name}:{action}:{tenant_part}"

    def _merge_fields(
        self,
        static_fields: list[dict[str, Any]],
        dynamic_fields: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {field["field"]: field for field in static_fields}
        for field in dynamic_fields:
            merged[field["field"]] = {**merged.get(field["field"], {}), **field}
        return list(merged.values())

    def _diff_field_sets(
        self,
        previous_fields: list[dict[str, Any]],
        current_fields: list[dict[str, Any]],
    ) -> dict[str, Any]:
        previous = {field["field"]: field for field in previous_fields if field.get("field")}
        current = {field["field"]: field for field in current_fields if field.get("field")}
        added = sorted(name for name in current.keys() - previous.keys())
        removed = sorted(name for name in previous.keys() - current.keys())
        changed = sorted(
            name
            for name in current.keys() & previous.keys()
            if current[name] != previous[name]
        )
        return {
            "added": added,
            "removed": removed,
            "changed_fields": changed,
            "changed": bool(added or removed or changed),
        }

    def _normalize_fields(self, fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for field in fields:
            if not isinstance(field, dict) or not field.get("field"):
                continue
            normalized.append(
                {
                    "field": str(field["field"]),
                    "label": str(field.get("label") or field["field"]),
                    "type": str(field.get("type", "string")),
                    "required": bool(field.get("required", False)),
                    "description": field.get("description"),
                }
            )
        return normalized

    def _opt_str(self, value: str | None) -> str | None:
        return str(value) if value is not None else None

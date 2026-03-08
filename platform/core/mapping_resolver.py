"""Mapping Resolver -- hybrid field mapping (files + DB overrides).

Layer 1: Default mappings from connector's mapping files (YAML/JSON), cached in Redis.
Layer 2: Per-tenant overrides from the database, cached in Redis.
Resolution: merge defaults with overrides, tenant overrides take priority.
"""

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.redis_client import cache_delete, cache_get, cache_set
from db.models import FieldMapping

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "mapping:"
_DEFAULTS_TTL = 600
_OVERRIDES_TTL = 300


class MappingResolver:
    def __init__(self, connector_base_path: str = "../integrators") -> None:
        self._connector_base_path = Path(connector_base_path)
        self._local_fallback: dict[str, dict] = {}

    async def load_defaults(self, connector_name: str, connector_path: str) -> dict:
        cache_key = f"{_CACHE_PREFIX}defaults:{connector_name}"

        cached = await cache_get(cache_key)
        if cached is not None:
            return cached

        if connector_name in self._local_fallback:
            return self._local_fallback[connector_name]

        defaults: dict[str, Any] = {}
        mapping_dir = Path(connector_path) / "mappings"

        if mapping_dir.exists():
            for mapping_file in mapping_dir.glob("*.yaml"):
                with open(mapping_file) as f:
                    data = yaml.safe_load(f) or {}
                defaults.update(data)
            for mapping_file in mapping_dir.glob("*.json"):
                with open(mapping_file) as f:
                    data = json.load(f)
                defaults.update(data)

        try:
            await cache_set(cache_key, defaults, ttl=_DEFAULTS_TTL)
        except Exception:
            logger.warning("Redis unavailable, using local fallback for %s", connector_name)
            self._local_fallback[connector_name] = defaults

        return defaults

    async def get_tenant_overrides(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        mapping_type: str,
    ) -> list[FieldMapping]:
        result = await db.execute(
            select(FieldMapping)
            .where(
                FieldMapping.tenant_id == tenant_id,
                FieldMapping.connector_name == connector_name,
                FieldMapping.mapping_type == mapping_type,
                FieldMapping.is_active.is_(True),
            )
            .order_by(FieldMapping.priority)
        )
        return list(result.scalars().all())

    def _resolve_sources(
        self, mapping_entry: dict, source_data: dict[str, Any]
    ) -> list[Any]:
        """Resolve all source values for a mapping rule."""
        sources: list[str] = mapping_entry.get("sources", [])
        if sources:
            return [self._get_nested(source_data, s) for s in sources]

        from_field = mapping_entry.get("from", "")
        if not from_field:
            return []
        if from_field == "__custom__":
            return [mapping_entry.get("from_custom", "")]
        return [self._get_nested(source_data, from_field)]

    async def resolve(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        mapping_type: str,
        source_data: dict[str, Any],
        flow_field_mapping: list[dict] | None = None,
        connector_path: str | None = None,
    ) -> dict[str, Any]:
        mapped: dict[str, Any] = {}

        if connector_path:
            defaults = await self.load_defaults(connector_name, connector_path)
            if defaults:
                for key, value in defaults.items():
                    self._set_nested(mapped, key, value)

        if flow_field_mapping:
            for mapping_entry in flow_field_mapping:
                to_field = mapping_entry.get("to", "")
                if to_field == "__custom__":
                    to_field = mapping_entry.get("to_custom", "")
                if not to_field:
                    continue

                resolved = self._resolve_sources(mapping_entry, source_data)
                if not resolved and not mapping_entry.get("from") and not mapping_entry.get("sources"):
                    continue

                raw_transform = mapping_entry.get("transform")
                if raw_transform:
                    steps = raw_transform if isinstance(raw_transform, list) else [raw_transform]
                    pipe: list[Any] = resolved
                    for step in steps:
                        pipe = [self._apply_transform(pipe, step)]
                    value = pipe[0]
                elif len(resolved) == 1:
                    value = resolved[0]
                else:
                    value = " ".join(str(v) for v in resolved if v is not None)

                if value is not None:
                    self._set_nested(mapped, to_field, value)

        overrides = await self.get_tenant_overrides(db, tenant_id, connector_name, mapping_type)
        for override in overrides:
            values = [self._get_nested(source_data, override.source_field)]
            if values[0] is not None:
                if override.transform:
                    value = self._apply_transform(values, override.transform)
                else:
                    value = values[0]
                self._set_nested(mapped, override.target_field, value)

        return mapped

    def _get_nested(self, data: dict, key: str) -> Any:
        if "[]" in key:
            return self._get_nested_array(data, key)
        parts = key.split(".")
        current: Any = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    def _get_nested_array(self, data: dict, key: str) -> Any:
        bracket_pos = key.index("[]")
        array_path = key[:bracket_pos]
        rest = key[bracket_pos + 2:]
        if rest.startswith("."):
            rest = rest[1:]

        arr = self._get_nested(data, array_path) if array_path else data
        if not isinstance(arr, list):
            return None
        if not rest:
            return arr
        return [self._get_nested(item, rest) if isinstance(item, dict) else None for item in arr]

    def _set_nested(self, data: dict, key: str, value: Any) -> None:
        if "[]" in key:
            self._set_nested_array(data, key, value)
            return
        parts = key.split(".")
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def _set_nested_array(self, data: dict, key: str, value: Any) -> None:
        bracket_pos = key.index("[]")
        array_path = key[:bracket_pos]
        rest = key[bracket_pos + 2:]
        if rest.startswith("."):
            rest = rest[1:]

        parts = array_path.split(".") if array_path else []
        current: Any = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        arr_key = parts[-1] if parts else ""
        if not arr_key:
            return

        if arr_key not in current or not isinstance(current[arr_key], list):
            current[arr_key] = []
        arr = current[arr_key]

        if not isinstance(value, list):
            value = [value]

        while len(arr) < len(value):
            arr.append({})

        for i, v in enumerate(value):
            if rest:
                if not isinstance(arr[i], dict):
                    arr[i] = {}
                self._set_nested(arr[i], rest, v)
            else:
                arr[i] = v

    def _apply_transform(self, values: list[Any], transform: dict) -> Any:
        """Apply a transform to resolved source values.

        ``values`` is always a list (single-element for 1:1 mappings).
        """
        t = transform.get("type", "")
        val = values[0] if values else None

        if t == "template":
            tpl = transform.get("template", "")
            for i, v in enumerate(values):
                tpl = tpl.replace(f"{{{{{i}}}}}", str(v) if v is not None else "")
            return tpl
        if t == "join":
            sep = transform.get("separator", " ")
            return sep.join(str(v) for v in values if v is not None)
        if t == "coalesce":
            for v in values:
                if v is not None:
                    return v
            return transform.get("default_value")
        if t == "map" or t == "lookup":
            table = transform.get("values") or transform.get("table", {})
            return table.get(str(val), transform.get("default", val))
        if t == "format":
            tpl = transform.get("template", "{0}")
            try:
                return tpl.format(val)
            except (KeyError, IndexError):
                return str(val) if val is not None else None
        if t == "uppercase":
            return str(val).upper() if val is not None else None
        if t == "lowercase":
            return str(val).lower() if val is not None else None
        if t == "to_int":
            try:
                return int(val)
            except (ValueError, TypeError):
                return val
        if t == "to_float":
            try:
                return float(val)
            except (ValueError, TypeError):
                return val
        if t == "to_string":
            return str(val) if val is not None else None
        if t == "default":
            return val if val is not None else transform.get("default_value")
        if t == "concat":
            separator = transform.get("separator", "")
            parts = transform.get("parts", [])
            return separator.join(str(p) for p in parts)
        if t == "split":
            separator = transform.get("separator", ",")
            return str(val).split(separator) if val is not None else []
        if t == "trim":
            return str(val).strip() if val is not None else None
        if t == "replace":
            old = transform.get("old", "")
            new = transform.get("new", "")
            return str(val).replace(old, new) if val is not None else None
        if t == "regex_extract":
            pattern = transform.get("pattern", "")
            group = transform.get("group", 0)
            if val is None or not pattern:
                return val
            try:
                match = re.search(pattern, str(val))
            except re.error:
                return val
            if match:
                try:
                    return match.group(group)
                except IndexError:
                    return match.group(0)
            return None
        if t == "regex_replace":
            pattern = transform.get("pattern", "")
            replacement = transform.get("replacement", "")
            if val is None or not pattern:
                return val
            try:
                return re.sub(pattern, replacement, str(val))
            except re.error:
                return val
        if t == "substring":
            start = transform.get("start", 0)
            end = transform.get("end")
            s = str(val) if val is not None else ""
            return s[start:end] if end is not None else s[start:]
        if t == "date_format":
            in_fmt = transform.get("input_format", "%Y-%m-%d")
            out_fmt = transform.get("output_format", "%d.%m.%Y")
            try:
                return datetime.strptime(str(val), in_fmt).strftime(out_fmt)
            except (ValueError, TypeError):
                return val
        if t == "math":
            op = transform.get("operation", "add")
            operand = transform.get("operand", 0)
            try:
                n = float(val)
            except (ValueError, TypeError):
                return val
            if op == "add":
                return n + operand
            if op == "sub":
                return n - operand
            if op == "mul":
                return n * operand
            if op == "div":
                return n / operand if operand != 0 else val
            return val
        if t == "prepend":
            prefix = transform.get("value", "")
            return f"{prefix}{val}" if val is not None else None
        if t == "append":
            suffix = transform.get("value", "")
            return f"{val}{suffix}" if val is not None else None

        return val

    async def invalidate_cache(self, connector_name: str | None = None) -> None:
        if connector_name:
            await cache_delete(f"{_CACHE_PREFIX}*:{connector_name}")
            self._local_fallback.pop(connector_name, None)
        else:
            await cache_delete(f"{_CACHE_PREFIX}*")
            self._local_fallback.clear()

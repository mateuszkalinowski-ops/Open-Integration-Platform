"""Mapping Resolver -- hybrid field mapping (files + DB overrides).

Layer 1: Default mappings from connector's mapping files (YAML/JSON), cached in Redis.
Layer 2: Per-tenant overrides from the database, cached in Redis.
Resolution: merge defaults with overrides, tenant overrides take priority.
"""

import json
import logging
import uuid
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

    async def resolve(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        mapping_type: str,
        source_data: dict[str, Any],
        flow_field_mapping: list[dict] | None = None,
    ) -> dict[str, Any]:
        mapped: dict[str, Any] = {}

        if flow_field_mapping:
            for mapping_entry in flow_field_mapping:
                from_field = mapping_entry.get("from", "")
                to_field = mapping_entry.get("to", "")
                if not from_field or not to_field:
                    continue

                if from_field == "__custom__":
                    value = mapping_entry.get("from_custom", "")
                else:
                    value = self._get_nested(source_data, from_field)

                if to_field == "__custom__":
                    to_field = mapping_entry.get("to_custom", "")

                if to_field and value is not None:
                    self._set_nested(mapped, to_field, value)

        overrides = await self.get_tenant_overrides(db, tenant_id, connector_name, mapping_type)
        for override in overrides:
            value = self._get_nested(source_data, override.source_field)
            if value is not None:
                if override.transform:
                    value = self._apply_transform(value, override.transform)
                self._set_nested(mapped, override.target_field, value)

        return mapped

    def _get_nested(self, data: dict, key: str) -> Any:
        parts = key.split(".")
        current: Any = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _set_nested(self, data: dict, key: str, value: Any) -> None:
        parts = key.split(".")
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def _apply_transform(self, value: Any, transform: dict) -> Any:
        transform_type = transform.get("type", "")

        if transform_type == "map":
            mapping_table = transform.get("values", {})
            return mapping_table.get(str(value), value)
        elif transform_type == "format":
            template = transform.get("template", "{}")
            return template.format(value)
        elif transform_type == "uppercase":
            return str(value).upper()
        elif transform_type == "lowercase":
            return str(value).lower()

        return value

    async def invalidate_cache(self, connector_name: str | None = None) -> None:
        if connector_name:
            await cache_delete(f"{_CACHE_PREFIX}*:{connector_name}")
            self._local_fallback.pop(connector_name, None)
        else:
            await cache_delete(f"{_CACHE_PREFIX}*")
            self._local_fallback.clear()

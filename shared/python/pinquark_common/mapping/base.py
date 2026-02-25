"""Base mapper that applies a MappingProfile to transform data.

Supports nested field access via dot notation, array iteration,
value transforms, multi-source mappings, and per-client custom
transform hooks.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from pinquark_common.mapping.config import (
    FieldMapping,
    MappingProfile,
    TransformType,
)

logger = logging.getLogger(__name__)


class BaseMapper:
    """Applies a MappingProfile to convert between external and WMS formats.

    Usage:
        profile = MappingProfile.model_validate(yaml_data)
        mapper = BaseMapper(profile)
        mapper.register_custom_transform("parse_allegro_status", my_func)
        wms_data = mapper.map(external_data)
    """

    def __init__(self, profile: MappingProfile) -> None:
        self.profile = profile
        self._custom_transforms: dict[str, Callable[[Any], Any]] = {}

    def register_custom_transform(
        self, name: str, func: Callable[[Any], Any]
    ) -> None:
        self._custom_transforms[name] = func

    def map(self, source_data: dict[str, Any]) -> dict[str, Any]:
        """Apply the profile's field mappings to source_data."""
        result: dict[str, Any] = {}

        for key, value in self.profile.static_values.items():
            _set_nested(result, key, value)

        for fm in self.profile.field_mappings:
            resolved = self._resolve_sources(fm, source_data)

            if not resolved or all(v is None for v in resolved):
                if fm.required:
                    label = ", ".join(fm.source_fields) if fm.source_fields else fm.source_field
                    raise MappingError(
                        f"Required field(s) '{label}' missing "
                        f"(profile={self.profile.profile_id})"
                    )
                if fm.default_value is not None:
                    _set_nested(result, fm.target_field, fm.default_value)
                continue

            transformed = self._apply_transform(fm, resolved)
            if fm.extra_transforms:
                for extra in fm.extra_transforms:
                    transformed = self._apply_transform(extra, [transformed])
            _set_nested(result, fm.target_field, transformed)

        return result

    def _resolve_sources(
        self, fm: FieldMapping, source_data: dict[str, Any]
    ) -> list[Any]:
        """Resolve all source values for a mapping rule."""
        if fm.source_fields:
            return [_get_nested(source_data, f) for f in fm.source_fields]
        if fm.source_field:
            return [_get_nested(source_data, fm.source_field)]
        return []

    def map_list(
        self, source_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return [self.map(item) for item in source_items]

    def _apply_transform(self, fm: FieldMapping, values: list[Any]) -> Any:
        """Apply the configured transform to resolved source values.

        ``values`` is a list of resolved sources (single-element for
        legacy 1:1 mappings, multi-element for multi-source rules).
        """
        value = values[0] if values else None

        match fm.transform:
            case TransformType.NONE:
                return value if len(values) == 1 else " ".join(
                    str(v) for v in values if v is not None
                )
            case TransformType.STRING:
                return str(value)
            case TransformType.INTEGER:
                return int(value)
            case TransformType.DECIMAL:
                try:
                    return Decimal(str(value))
                except InvalidOperation:
                    logger.warning(
                        "Cannot convert '%s' to Decimal for field '%s'",
                        value,
                        fm.source_field or fm.source_fields,
                    )
                    return fm.default_value
            case TransformType.DATE:
                if isinstance(value, date):
                    return value
                return date.fromisoformat(str(value)[:10])
            case TransformType.DATETIME:
                if isinstance(value, datetime):
                    return value
                return datetime.fromisoformat(str(value))
            case TransformType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ("true", "1", "yes", "tak")
            case TransformType.UPPERCASE:
                return str(value).upper()
            case TransformType.LOWERCASE:
                return str(value).lower()
            case TransformType.STRIP | TransformType.TRIM:
                return str(value).strip()
            case TransformType.MAP_VALUE | TransformType.LOOKUP:
                mapped = fm.value_map.get(str(value))
                if mapped is None:
                    logger.warning(
                        "No mapping for value '%s' in field '%s', "
                        "using default '%s'",
                        value,
                        fm.source_field,
                        fm.default_value,
                    )
                    return fm.default_value
                return mapped
            case TransformType.TEMPLATE:
                tpl = fm.template
                for i, v in enumerate(values):
                    tpl = tpl.replace(f"{{{{{i}}}}}", str(v) if v is not None else "")
                try:
                    return tpl.format(value=value)
                except (KeyError, IndexError):
                    return tpl
            case TransformType.CUSTOM:
                func = self._custom_transforms.get(fm.custom_transform_name)
                if func is None:
                    raise MappingError(
                        f"Custom transform '{fm.custom_transform_name}' "
                        f"not registered"
                    )
                return func(value)
            case TransformType.REGEX_EXTRACT:
                if value is None or not fm.regex_pattern:
                    return value
                match = re.search(fm.regex_pattern, str(value))
                if match:
                    try:
                        return match.group(fm.regex_group)
                    except IndexError:
                        return match.group(0)
                return None
            case TransformType.REGEX_REPLACE:
                if value is None or not fm.regex_pattern:
                    return value
                return re.sub(fm.regex_pattern, fm.regex_replacement, str(value))
            case TransformType.COALESCE:
                for v in values:
                    if v is not None:
                        return v
                return fm.default_value
            case TransformType.JOIN:
                sep = fm.separator or " "
                return sep.join(str(v) for v in values if v is not None)
            case TransformType.SUBSTRING:
                s = str(value) if value is not None else ""
                end = fm.substring_end
                return s[fm.substring_start:end] if end is not None else s[fm.substring_start:]
            case TransformType.DATE_FORMAT:
                in_fmt = fm.input_format or "%Y-%m-%d"
                out_fmt = fm.output_format or "%d.%m.%Y"
                try:
                    return datetime.strptime(str(value), in_fmt).strftime(out_fmt)
                except (ValueError, TypeError):
                    return value
            case TransformType.MATH:
                op = fm.math_operation or "add"
                operand = fm.math_operand
                try:
                    n = float(value)
                except (ValueError, TypeError):
                    return value
                if op == "add":
                    return n + operand
                if op == "sub":
                    return n - operand
                if op == "mul":
                    return n * operand
                if op == "div":
                    return n / operand if operand != 0 else value
                return value
            case TransformType.PREPEND:
                return f"{fm.prepend_value}{value}" if value is not None else None
            case TransformType.APPEND:
                return f"{value}{fm.append_value}" if value is not None else None
            case TransformType.SPLIT:
                sep = fm.separator or ","
                return str(value).split(sep) if value is not None else []
            case TransformType.REPLACE:
                return str(value).replace(
                    fm.regex_pattern, fm.regex_replacement
                ) if value is not None else None
            case _:
                return value


class MappingError(Exception):
    """Raised when a mapping operation fails."""


def _get_nested(data: dict[str, Any], path: str) -> Any:
    """Retrieve a value from a nested dict using dot notation.

    Supports simple array access: "items[].name" returns a list of names
    from each element in the items array.
    """
    parts = path.split(".")
    current: Any = data

    for i, part in enumerate(parts):
        if current is None:
            return None

        if part.endswith("[]"):
            key = part[:-2]
            arr = current.get(key) if isinstance(current, dict) else None
            if not isinstance(arr, list):
                return None
            remaining = ".".join(parts[i + 1 :])
            if not remaining:
                return arr
            return [_get_nested(item, remaining) for item in arr]

        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None

    return current


def _set_nested(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dict using dot notation."""
    parts = path.split(".")

    current = data
    for part in parts[:-1]:
        if part.endswith("[]"):
            key = part[:-2]
            if key not in current:
                current[key] = []
            return

        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    final_key = parts[-1]
    if final_key.endswith("[]"):
        key = final_key[:-2]
        if key not in current:
            current[key] = []
        if isinstance(value, list):
            current[key].extend(value)
        else:
            current[key].append(value)
    else:
        current[final_key] = value

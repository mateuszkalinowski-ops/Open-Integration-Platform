"""Per-client configurable mapping profiles.

A MappingProfile defines how fields from an external system (ERP,
e-commerce, courier) are transformed to/from Pinquark WMS DTOs.

Profiles can be loaded from YAML/JSON files, allowing each client
to customize field mappings without code changes.

Example YAML profile:
    profile_id: "client_acme_allegro"
    client_id: "acme"
    system: "allegro"
    category: "ecommerce"
    direction: "inbound"
    entity: "order"
    field_mappings:
      - source_field: "buyer.login"
        target_field: "contractor.symbol"
      - source_field: "buyer.email"
        target_field: "contractor.email"
      - source_field: "line_items[].offer.name"
        target_field: "positions[].article.name"
      - source_field: "line_items[].quantity"
        target_field: "positions[].quantity"
      - source_field: "payment.paid_amount.amount"
        target_field: "attributes[symbol=total_paid].value_decimal"
        transform: "decimal"
    static_values:
      source: "ECOMMERCE"
      document_type: "ZK"
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MappingDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class TransformType(str, Enum):
    """Built-in field transformations."""

    NONE = "none"
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    STRIP = "strip"
    MAP_VALUE = "map_value"
    TEMPLATE = "template"
    CUSTOM = "custom"
    REGEX_EXTRACT = "regex_extract"
    REGEX_REPLACE = "regex_replace"
    COALESCE = "coalesce"
    JOIN = "join"
    SUBSTRING = "substring"
    DATE_FORMAT = "date_format"
    MATH = "math"
    PREPEND = "prepend"
    APPEND = "append"
    LOOKUP = "lookup"
    SPLIT = "split"
    REPLACE = "replace"
    TRIM = "trim"


class FieldMapping(BaseModel):
    """Single field-to-field mapping rule.

    Supports dot-notation for nested fields (e.g. "buyer.address.city")
    and array notation (e.g. "line_items[].quantity").

    Multi-source mode: when ``source_fields`` is provided, all listed
    fields are resolved and passed to the transform.  The legacy
    ``source_field`` is used as the primary source for backward
    compatibility.
    """

    source_field: str = ""
    source_fields: list[str] = Field(default_factory=list)
    target_field: str
    transform: TransformType = TransformType.NONE
    default_value: Any = None
    required: bool = False
    value_map: dict[str, str] = Field(default_factory=dict)
    template: str = ""
    custom_transform_name: str = ""
    description: str = ""
    regex_pattern: str = ""
    regex_group: int = 0
    regex_replacement: str = ""
    separator: str = ""
    input_format: str = ""
    output_format: str = ""
    math_operation: str = ""
    math_operand: float = 0
    prepend_value: str = ""
    append_value: str = ""
    substring_start: int = 0
    substring_end: int | None = None
    extra_transforms: list["FieldMapping"] = Field(default_factory=list)


class MappingProfile(BaseModel):
    """Complete mapping configuration for a client + system + entity.

    Each client can have multiple profiles (one per entity per direction).
    Profiles are resolved by (client_id, system, category, entity, direction).
    """

    profile_id: str
    client_id: str
    system: str
    category: str
    entity: str
    direction: MappingDirection = MappingDirection.INBOUND
    version: str = "1.0.0"
    description: str = ""
    field_mappings: list[FieldMapping] = Field(default_factory=list)
    static_values: dict[str, Any] = Field(default_factory=dict)
    ignore_unmapped: bool = True
    enabled: bool = True

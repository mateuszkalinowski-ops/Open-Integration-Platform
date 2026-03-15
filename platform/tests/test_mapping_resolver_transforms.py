"""Tests for MappingResolver: _resolve_sources, _apply_transform, resolve (flow field mapping).

Covers multi-source resolution, all transform types, transform chaining,
nested field get/set, and the resolve() integration with flow_field_mapping.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.mapping_resolver import MappingResolver


@pytest.fixture()
def resolver() -> MappingResolver:
    return MappingResolver()


@pytest.fixture()
def source_data() -> dict:
    return {
        "order_id": "ORD-456",
        "buyer": {
            "first_name": "Anna",
            "last_name": "Nowak",
            "email": "anna@example.com",
        },
        "amount": "250.00",
        "quantity": "3",
        "status": "shipped",
        "date": "2026-03-15",
        "address": {
            "street": "  Długa 10  ",
            "city": "Kraków",
            "zip": "30-001",
        },
        "description": "Shipment #789 — fragile",
        "tags": "books,priority",
        "phone": "+48 987 654 321",
        "empty_field": None,
    }


@pytest.fixture()
def mock_db() -> AsyncMock:
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result_mock)
    return db


# ── _resolve_sources ──


class TestResolverResolveSources:
    def test_single_from(self, resolver: MappingResolver, source_data: dict) -> None:
        m = {"from": "buyer.first_name"}
        assert resolver._resolve_sources(m, source_data) == ["Anna"]

    def test_multi_sources(self, resolver: MappingResolver, source_data: dict) -> None:
        m = {"sources": ["buyer.first_name", "buyer.last_name"]}
        assert resolver._resolve_sources(m, source_data) == ["Anna", "Nowak"]

    def test_custom_placeholder(self, resolver: MappingResolver, source_data: dict) -> None:
        m = {"from": "__custom__", "from_custom": "literal"}
        assert resolver._resolve_sources(m, source_data) == ["literal"]

    def test_empty_from(self, resolver: MappingResolver, source_data: dict) -> None:
        assert resolver._resolve_sources({"from": ""}, source_data) == []

    def test_no_fields(self, resolver: MappingResolver, source_data: dict) -> None:
        assert resolver._resolve_sources({}, source_data) == []

    def test_sources_priority(self, resolver: MappingResolver, source_data: dict) -> None:
        m = {"from": "buyer.email", "sources": ["buyer.first_name"]}
        assert resolver._resolve_sources(m, source_data) == ["Anna"]

    def test_nested_path(self, resolver: MappingResolver, source_data: dict) -> None:
        assert resolver._resolve_sources({"from": "address.zip"}, source_data) == ["30-001"]

    def test_missing_field(self, resolver: MappingResolver, source_data: dict) -> None:
        assert resolver._resolve_sources({"from": "no.such.path"}, source_data) == [None]


# ── _get_nested / _set_nested ──


class TestNestedAccess:
    def test_get_nested_simple(self, resolver: MappingResolver) -> None:
        assert resolver._get_nested({"a": 1}, "a") == 1

    def test_get_nested_deep(self, resolver: MappingResolver) -> None:
        assert resolver._get_nested({"a": {"b": {"c": 3}}}, "a.b.c") == 3

    def test_get_nested_missing(self, resolver: MappingResolver) -> None:
        assert resolver._get_nested({"a": 1}, "b") is None

    def test_get_nested_partial(self, resolver: MappingResolver) -> None:
        assert resolver._get_nested({"a": 1}, "a.b") is None

    def test_set_nested_simple(self, resolver: MappingResolver) -> None:
        d: dict = {}
        resolver._set_nested(d, "x", 1)
        assert d == {"x": 1}

    def test_set_nested_deep(self, resolver: MappingResolver) -> None:
        d: dict = {}
        resolver._set_nested(d, "a.b.c", 42)
        assert d == {"a": {"b": {"c": 42}}}


# ── _apply_transform ──


class TestResolverApplyTransform:
    def test_uppercase(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["hello"], {"type": "uppercase"}) == "HELLO"

    def test_lowercase(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["HELLO"], {"type": "lowercase"}) == "hello"

    def test_to_int(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["42"], {"type": "to_int"}) == 42

    def test_to_int_invalid(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["abc"], {"type": "to_int"}) == "abc"

    def test_to_float(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["3.14"], {"type": "to_float"}) == pytest.approx(3.14)

    def test_to_string(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([99], {"type": "to_string"}) == "99"

    def test_trim(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["  x  "], {"type": "trim"}) == "x"

    def test_split(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["a;b;c"], {"type": "split", "separator": ";"}) == ["a", "b", "c"]

    def test_replace(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["foo-bar"], {"type": "replace", "old": "-", "new": "_"}) == "foo_bar"

    def test_default_with_value(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["val"], {"type": "default", "default_value": "fb"}) == "val"

    def test_default_with_none(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([None], {"type": "default", "default_value": "fb"}) == "fb"

    def test_format(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["42"], {"type": "format", "template": "ID:{}"}) == "ID:42"

    def test_map(self, resolver: MappingResolver) -> None:
        t = {"type": "map", "values": {"shipped": "IN_TRANSIT"}}
        assert resolver._apply_transform(["shipped"], t) == "IN_TRANSIT"

    def test_lookup(self, resolver: MappingResolver) -> None:
        t = {"type": "lookup", "table": {"a": "1"}}
        assert resolver._apply_transform(["a"], t) == "1"

    def test_prepend(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["world"], {"type": "prepend", "value": "hello-"}) == "hello-world"

    def test_append(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["hello"], {"type": "append", "value": "!"}) == "hello!"

    def test_regex_extract(self, resolver: MappingResolver) -> None:
        t = {"type": "regex_extract", "pattern": r"#(\d+)", "group": 1}
        assert resolver._apply_transform(["Shipment #789"], t) == "789"

    def test_regex_extract_no_match(self, resolver: MappingResolver) -> None:
        t = {"type": "regex_extract", "pattern": r"\d+"}
        assert resolver._apply_transform(["no digits"], t) is None

    def test_regex_replace(self, resolver: MappingResolver) -> None:
        t = {"type": "regex_replace", "pattern": r"\s+", "replacement": "_"}
        assert resolver._apply_transform(["a b  c"], t) == "a_b_c"

    def test_substring(self, resolver: MappingResolver) -> None:
        t = {"type": "substring", "start": 0, "end": 3}
        assert resolver._apply_transform(["Hello"], t) == "Hel"

    def test_substring_start_only(self, resolver: MappingResolver) -> None:
        t = {"type": "substring", "start": 3}
        assert resolver._apply_transform(["Hello"], t) == "lo"

    def test_date_format(self, resolver: MappingResolver) -> None:
        t = {"type": "date_format", "input_format": "%Y-%m-%d", "output_format": "%d.%m.%Y"}
        assert resolver._apply_transform(["2026-03-15"], t) == "15.03.2026"

    def test_date_format_invalid(self, resolver: MappingResolver) -> None:
        t = {"type": "date_format"}
        assert resolver._apply_transform(["bad"], t) == "bad"

    def test_math_add(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([10], {"type": "math", "operation": "add", "operand": 5}) == pytest.approx(
            15.0
        )

    def test_math_sub(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([10], {"type": "math", "operation": "sub", "operand": 3}) == pytest.approx(7.0)

    def test_math_mul(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([6], {"type": "math", "operation": "mul", "operand": 7}) == pytest.approx(42.0)

    def test_math_div(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([100], {"type": "math", "operation": "div", "operand": 4}) == pytest.approx(
            25.0
        )

    def test_math_div_zero(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([10], {"type": "math", "operation": "div", "operand": 0}) == 10

    def test_math_invalid(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["abc"], {"type": "math", "operation": "add", "operand": 1}) == "abc"

    def test_template(self, resolver: MappingResolver) -> None:
        t = {"type": "template", "template": "{0} {1}"}
        assert resolver._apply_transform(["Anna", "Nowak"], t) == "Anna Nowak"

    def test_join(self, resolver: MappingResolver) -> None:
        t = {"type": "join", "separator": ", "}
        assert resolver._apply_transform(["Kraków", "Polska"], t) == "Kraków, Polska"

    def test_join_filters_none(self, resolver: MappingResolver) -> None:
        t = {"type": "join", "separator": "-"}
        assert resolver._apply_transform(["a", None, "b"], t) == "a-b"

    def test_coalesce(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform([None, None, "found"], {"type": "coalesce"}) == "found"

    def test_coalesce_all_none(self, resolver: MappingResolver) -> None:
        t = {"type": "coalesce", "default_value": "DEFAULT"}
        assert resolver._apply_transform([None, None], t) == "DEFAULT"

    def test_unknown_type(self, resolver: MappingResolver) -> None:
        assert resolver._apply_transform(["val"], {"type": "unknown"}) == "val"


# ── resolve() — integration with flow_field_mapping ──


class TestResolverResolve:
    @pytest.mark.asyncio()
    async def test_simple_flow_mapping(self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock) -> None:
        flow_mapping = [{"from": "buyer.first_name", "to": "name"}]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result == {"name": "Anna"}

    @pytest.mark.asyncio()
    async def test_multi_source_flow_mapping(
        self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock
    ) -> None:
        flow_mapping = [
            {
                "sources": ["buyer.first_name", "buyer.last_name"],
                "to": "full_name",
                "transform": {"type": "join", "separator": " "},
            }
        ]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result == {"full_name": "Anna Nowak"}

    @pytest.mark.asyncio()
    async def test_transform_chain_in_resolve(
        self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock
    ) -> None:
        flow_mapping = [
            {
                "from": "address.street",
                "to": "street",
                "transform": [
                    {"type": "trim"},
                    {"type": "uppercase"},
                ],
            }
        ]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result == {"street": "DŁUGA 10"}

    @pytest.mark.asyncio()
    async def test_nested_target_in_resolve(
        self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock
    ) -> None:
        flow_mapping = [
            {"from": "buyer.email", "to": "contact.email"},
            {"from": "buyer.first_name", "to": "contact.name"},
        ]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result == {"contact": {"email": "anna@example.com", "name": "Anna"}}

    @pytest.mark.asyncio()
    async def test_custom_source_target_in_resolve(
        self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock
    ) -> None:
        flow_mapping = [{"from": "__custom__", "from_custom": "MANUAL", "to": "__custom__", "to_custom": "source_type"}]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result == {"source_type": "MANUAL"}

    @pytest.mark.asyncio()
    async def test_none_values_skipped(self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock) -> None:
        flow_mapping = [{"from": "empty_field", "to": "out"}]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result == {}

    @pytest.mark.asyncio()
    async def test_empty_flow_mapping(self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock) -> None:
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_field_mapping=[])
        assert result == {}

    @pytest.mark.asyncio()
    async def test_no_flow_mapping(self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock) -> None:
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_field_mapping=None)
        assert result == {}

    @pytest.mark.asyncio()
    async def test_complex_chain_regex_prepend_upper(
        self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock
    ) -> None:
        flow_mapping = [
            {
                "from": "description",
                "to": "ref",
                "transform": [
                    {"type": "regex_extract", "pattern": r"#(\d+)", "group": 1},
                    {"type": "prepend", "value": "SHP-"},
                    {"type": "uppercase"},
                ],
            }
        ]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result == {"ref": "SHP-789"}

    @pytest.mark.asyncio()
    async def test_math_chain_in_resolve(
        self, resolver: MappingResolver, source_data: dict, mock_db: AsyncMock
    ) -> None:
        flow_mapping = [
            {
                "from": "amount",
                "to": "total_vat",
                "transform": [
                    {"type": "to_float"},
                    {"type": "math", "operation": "mul", "operand": 1.23},
                ],
            }
        ]
        result = await resolver.resolve(mock_db, uuid.uuid4(), "test", "order", source_data, flow_mapping)
        assert result["total_vat"] == pytest.approx(307.50)

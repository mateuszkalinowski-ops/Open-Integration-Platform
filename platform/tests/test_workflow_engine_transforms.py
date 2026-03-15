"""Tests for WorkflowEngine field mapping: _resolve_sources, _apply_transform, _apply_field_mapping.

Covers multi-source resolution, all transform types, transform chaining (pipelines),
and integration between these components.
"""

from __future__ import annotations

import pytest
from core.workflow_engine import WorkflowContext, WorkflowEngine


@pytest.fixture()
def engine() -> WorkflowEngine:
    return WorkflowEngine()


@pytest.fixture()
def ctx() -> WorkflowContext:
    return WorkflowContext(
        {
            "order_id": "ORD-123",
            "buyer": {
                "first_name": "Jan",
                "last_name": "Kowalski",
                "email": "jan@example.com",
            },
            "amount": "199.99",
            "quantity": "5",
            "status": "new",
            "date": "2026-02-25",
            "address": {
                "street": "  Marszałkowska 1  ",
                "city": "Warszawa",
                "zip": "00-001",
            },
            "description": "Order #123 — priority",
            "tags": "electronics,fragile,express",
            "phone": "+48 123 456 789",
            "empty_field": None,
        }
    )


# ── _resolve_sources ──


class TestResolveSources:
    def test_single_source_from_field(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {"from": "buyer.first_name"}
        result = engine._resolve_sources(m, ctx)
        assert result == ["Jan"]

    def test_multi_source(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {"sources": ["buyer.first_name", "buyer.last_name"]}
        result = engine._resolve_sources(m, ctx)
        assert result == ["Jan", "Kowalski"]

    def test_custom_placeholder(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {"from": "__custom__", "from_custom": "static-value"}
        result = engine._resolve_sources(m, ctx)
        assert result == ["static-value"]

    def test_empty_from_returns_empty(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {"from": ""}
        assert engine._resolve_sources(m, ctx) == []

    def test_no_from_no_sources(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {}
        assert engine._resolve_sources(m, ctx) == []

    def test_nested_path(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {"from": "address.city"}
        assert engine._resolve_sources(m, ctx) == ["Warszawa"]

    def test_missing_field_returns_none(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {"from": "nonexistent.field"}
        assert engine._resolve_sources(m, ctx) == [None]

    def test_sources_take_priority_over_from(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        m = {"from": "buyer.email", "sources": ["buyer.first_name", "buyer.last_name"]}
        result = engine._resolve_sources(m, ctx)
        assert result == ["Jan", "Kowalski"]


# ── _apply_transform — single-value transforms ──


class TestApplyTransformSingleValue:
    def test_uppercase(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["hello"], {"type": "uppercase"}) == "HELLO"

    def test_uppercase_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "uppercase"}) is None

    def test_lowercase(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["HELLO"], {"type": "lowercase"}) == "hello"

    def test_lowercase_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "lowercase"}) is None

    def test_to_int(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["42"], {"type": "to_int"}) == 42

    def test_to_int_invalid(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["abc"], {"type": "to_int"}) == "abc"

    def test_to_float(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["3.14"], {"type": "to_float"}) == pytest.approx(3.14)

    def test_to_float_invalid(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["abc"], {"type": "to_float"}) == "abc"

    def test_to_string(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([42], {"type": "to_string"}) == "42"

    def test_to_string_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "to_string"}) is None

    def test_trim(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["  hello  "], {"type": "trim"}) == "hello"

    def test_trim_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "trim"}) is None

    def test_split(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["a,b,c"], {"type": "split", "separator": ","}) == ["a", "b", "c"]

    def test_split_default_separator(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["x,y"], {"type": "split"}) == ["x", "y"]

    def test_split_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "split"}) == []

    def test_replace(self, engine: WorkflowEngine) -> None:
        assert (
            engine._apply_transform(["hello world"], {"type": "replace", "old": "world", "new": "there"})
            == "hello there"
        )

    def test_replace_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "replace", "old": "x", "new": "y"}) is None

    def test_default_with_value(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["exists"], {"type": "default", "default_value": "fallback"}) == "exists"

    def test_default_with_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "default", "default_value": "fallback"}) == "fallback"

    def test_format(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["world"], {"type": "format", "template": "Hello, {}!"}) == "Hello, world!"

    def test_map_with_values(self, engine: WorkflowEngine) -> None:
        t = {"type": "map", "values": {"new": "NOWY", "done": "GOTOWY"}}
        assert engine._apply_transform(["new"], t) == "NOWY"

    def test_map_with_default(self, engine: WorkflowEngine) -> None:
        t = {"type": "map", "values": {"new": "NOWY"}, "default": "UNKNOWN"}
        assert engine._apply_transform(["other"], t) == "UNKNOWN"

    def test_lookup_alias(self, engine: WorkflowEngine) -> None:
        t = {"type": "lookup", "table": {"a": "1", "b": "2"}}
        assert engine._apply_transform(["b"], t) == "2"

    def test_concat(self, engine: WorkflowEngine) -> None:
        t = {"type": "concat", "separator": "-", "parts": ["A", "B", "C"]}
        assert engine._apply_transform(["ignored"], t) == "A-B-C"

    def test_prepend(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["world"], {"type": "prepend", "value": "hello-"}) == "hello-world"

    def test_prepend_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "prepend", "value": "x"}) is None

    def test_append(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["hello"], {"type": "append", "value": "-world"}) == "hello-world"

    def test_append_none(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([None], {"type": "append", "value": "x"}) is None

    def test_unknown_type_returns_value(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform(["val"], {"type": "nonexistent"}) == "val"

    def test_empty_values_list(self, engine: WorkflowEngine) -> None:
        assert engine._apply_transform([], {"type": "uppercase"}) is None


# ── _apply_transform — regex transforms ──


class TestApplyTransformRegex:
    def test_regex_extract_basic(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_extract", "pattern": r"(\d+)"}
        assert engine._apply_transform(["Order #123"], t) == "123"

    def test_regex_extract_group(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_extract", "pattern": r"(\w+)\s(\w+)", "group": 2}
        assert engine._apply_transform(["Jan Kowalski"], t) == "Kowalski"

    def test_regex_extract_no_match(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_extract", "pattern": r"\d+"}
        assert engine._apply_transform(["no digits here"], t) is None

    def test_regex_extract_none(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_extract", "pattern": r"\d+"}
        assert engine._apply_transform([None], t) is None

    def test_regex_extract_empty_pattern(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_extract", "pattern": ""}
        assert engine._apply_transform(["test"], t) == "test"

    def test_regex_extract_invalid_group_falls_back(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_extract", "pattern": r"(\d+)", "group": 5}
        assert engine._apply_transform(["Order 123"], t) == "123"

    def test_regex_replace(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_replace", "pattern": r"\s+", "replacement": "-"}
        assert engine._apply_transform(["hello   world"], t) == "hello-world"

    def test_regex_replace_none(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_replace", "pattern": r"\d", "replacement": ""}
        assert engine._apply_transform([None], t) is None

    def test_regex_replace_empty_pattern(self, engine: WorkflowEngine) -> None:
        t = {"type": "regex_replace", "pattern": "", "replacement": "x"}
        assert engine._apply_transform(["test"], t) == "test"


# ── _apply_transform — substring, date_format, math ──


class TestApplyTransformAdvanced:
    def test_substring_start_end(self, engine: WorkflowEngine) -> None:
        t = {"type": "substring", "start": 0, "end": 5}
        assert engine._apply_transform(["Hello World"], t) == "Hello"

    def test_substring_start_only(self, engine: WorkflowEngine) -> None:
        t = {"type": "substring", "start": 6}
        assert engine._apply_transform(["Hello World"], t) == "World"

    def test_substring_none(self, engine: WorkflowEngine) -> None:
        t = {"type": "substring", "start": 0, "end": 3}
        assert engine._apply_transform([None], t) == ""

    def test_date_format(self, engine: WorkflowEngine) -> None:
        t = {"type": "date_format", "input_format": "%Y-%m-%d", "output_format": "%d.%m.%Y"}
        assert engine._apply_transform(["2026-02-25"], t) == "25.02.2026"

    def test_date_format_invalid(self, engine: WorkflowEngine) -> None:
        t = {"type": "date_format", "input_format": "%Y-%m-%d", "output_format": "%d.%m.%Y"}
        assert engine._apply_transform(["not-a-date"], t) == "not-a-date"

    def test_math_add(self, engine: WorkflowEngine) -> None:
        t = {"type": "math", "operation": "add", "operand": 10}
        assert engine._apply_transform(["5"], t) == pytest.approx(15.0)

    def test_math_sub(self, engine: WorkflowEngine) -> None:
        t = {"type": "math", "operation": "sub", "operand": 3}
        assert engine._apply_transform([10], t) == pytest.approx(7.0)

    def test_math_mul(self, engine: WorkflowEngine) -> None:
        t = {"type": "math", "operation": "mul", "operand": 4}
        assert engine._apply_transform([5], t) == pytest.approx(20.0)

    def test_math_div(self, engine: WorkflowEngine) -> None:
        t = {"type": "math", "operation": "div", "operand": 2}
        assert engine._apply_transform([10], t) == pytest.approx(5.0)

    def test_math_div_by_zero(self, engine: WorkflowEngine) -> None:
        t = {"type": "math", "operation": "div", "operand": 0}
        assert engine._apply_transform([10], t) == 10

    def test_math_invalid_value(self, engine: WorkflowEngine) -> None:
        t = {"type": "math", "operation": "add", "operand": 5}
        assert engine._apply_transform(["abc"], t) == "abc"


# ── _apply_transform — multi-source transforms ──


class TestApplyTransformMultiSource:
    def test_template(self, engine: WorkflowEngine) -> None:
        t = {"type": "template", "template": "{0} {1}"}
        assert engine._apply_transform(["Jan", "Kowalski"], t) == "Jan Kowalski"

    def test_template_with_none(self, engine: WorkflowEngine) -> None:
        t = {"type": "template", "template": "{0} {1}"}
        assert engine._apply_transform(["Jan", None], t) == "Jan "

    def test_template_three_sources(self, engine: WorkflowEngine) -> None:
        t = {"type": "template", "template": "{0}, {1} {2}"}
        assert (
            engine._apply_transform(["Marszałkowska 1", "00-001", "Warszawa"], t) == "Marszałkowska 1, 00-001 Warszawa"
        )

    def test_join(self, engine: WorkflowEngine) -> None:
        t = {"type": "join", "separator": ", "}
        assert engine._apply_transform(["Jan", "Kowalski"], t) == "Jan, Kowalski"

    def test_join_default_separator(self, engine: WorkflowEngine) -> None:
        t = {"type": "join"}
        assert engine._apply_transform(["a", "b"], t) == "a b"

    def test_join_filters_none(self, engine: WorkflowEngine) -> None:
        t = {"type": "join", "separator": "-"}
        assert engine._apply_transform(["a", None, "c"], t) == "a-c"

    def test_coalesce_first_non_none(self, engine: WorkflowEngine) -> None:
        t = {"type": "coalesce"}
        assert engine._apply_transform([None, None, "found"], t) == "found"

    def test_coalesce_all_none(self, engine: WorkflowEngine) -> None:
        t = {"type": "coalesce", "default_value": "fallback"}
        assert engine._apply_transform([None, None], t) == "fallback"

    def test_coalesce_first_value(self, engine: WorkflowEngine) -> None:
        t = {"type": "coalesce"}
        assert engine._apply_transform(["first", "second"], t) == "first"


# ── _apply_field_mapping — integration tests ──


class TestApplyFieldMapping:
    def test_simple_mapping(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"from": "buyer.first_name", "to": "name"}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"name": "Jan"}

    def test_nested_target(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"from": "buyer.email", "to": "contact.email"}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"contact": {"email": "jan@example.com"}}

    def test_custom_source_and_target(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"from": "__custom__", "from_custom": "FIXED", "to": "__custom__", "to_custom": "meta.source"}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"meta": {"source": "FIXED"}}

    def test_multi_source_default_join(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"sources": ["buyer.first_name", "buyer.last_name"], "to": "full_name"}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"full_name": "Jan Kowalski"}

    def test_multi_source_with_template(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "sources": ["buyer.last_name", "buyer.first_name"],
                "to": "full_name",
                "transform": {"type": "template", "template": "{0}, {1}"},
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"full_name": "Kowalski, Jan"}

    def test_single_transform(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"from": "buyer.first_name", "to": "name", "transform": {"type": "uppercase"}}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"name": "JAN"}

    def test_transform_chain(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "from": "address.street",
                "to": "street",
                "transform": [
                    {"type": "trim"},
                    {"type": "uppercase"},
                ],
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"street": "MARSZAŁKOWSKA 1"}

    def test_transform_chain_three_steps(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "from": "description",
                "to": "ref",
                "transform": [
                    {"type": "regex_extract", "pattern": r"#(\d+)", "group": 1},
                    {"type": "prepend", "value": "REF-"},
                    {"type": "uppercase"},
                ],
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"ref": "REF-123"}

    def test_transform_chain_multi_source(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "sources": ["buyer.first_name", "buyer.last_name"],
                "to": "display",
                "transform": [
                    {"type": "join", "separator": " "},
                    {"type": "uppercase"},
                ],
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"display": "JAN KOWALSKI"}

    def test_none_value_skipped(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"from": "empty_field", "to": "out"}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {}

    def test_missing_to_field_skipped(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"from": "buyer.first_name", "to": ""}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {}

    def test_multiple_mappings(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {"from": "buyer.first_name", "to": "first_name"},
            {"from": "buyer.last_name", "to": "last_name"},
            {"from": "buyer.email", "to": "email"},
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"first_name": "Jan", "last_name": "Kowalski", "email": "jan@example.com"}

    def test_math_in_mapping(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "from": "amount",
                "to": "amount_with_tax",
                "transform": [
                    {"type": "to_float"},
                    {"type": "math", "operation": "mul", "operand": 1.23},
                ],
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result["amount_with_tax"] == pytest.approx(245.9877)

    def test_date_format_in_mapping(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "from": "date",
                "to": "formatted_date",
                "transform": {"type": "date_format", "input_format": "%Y-%m-%d", "output_format": "%d/%m/%Y"},
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"formatted_date": "25/02/2026"}

    def test_split_tags(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [{"from": "tags", "to": "tag_list", "transform": {"type": "split", "separator": ","}}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"tag_list": ["electronics", "fragile", "express"]}

    def test_regex_phone_cleanup(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "from": "phone",
                "to": "clean_phone",
                "transform": {"type": "regex_replace", "pattern": r"[\s+]", "replacement": ""},
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"clean_phone": "48123456789"}

    def test_map_status(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        mappings = [
            {
                "from": "status",
                "to": "mapped_status",
                "transform": {"type": "map", "values": {"new": "PENDING", "done": "COMPLETE"}},
            }
        ]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"mapped_status": "PENDING"}

    def test_variable_resolution(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        ctx.variables["courier"] = "DHL"
        mappings = [{"from": "vars.courier", "to": "provider"}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"provider": "DHL"}

    def test_node_output_resolution(self, engine: WorkflowEngine, ctx: WorkflowContext) -> None:
        ctx.set_node_output("node_1", {"price": 29.99})
        mappings = [{"from": "nodes.node_1.price", "to": "price"}]
        result = engine._apply_field_mapping(mappings, ctx)
        assert result == {"price": 29.99}

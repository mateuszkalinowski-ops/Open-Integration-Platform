"""Tests for shared BaseMapper: _resolve_sources, _apply_transform, map().

Covers the Pydantic-based FieldMapping model, all TransformType enum values,
multi-source resolution, extra_transforms chaining, static values, required
fields, and default values.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from pinquark_common.mapping.base import BaseMapper, MappingError
from pinquark_common.mapping.config import (
    FieldMapping,
    MappingProfile,
    TransformType,
)


def _profile(*mappings: FieldMapping, static: dict | None = None) -> MappingProfile:
    return MappingProfile(
        profile_id="test",
        client_id="test-client",
        system="test-system",
        category="test",
        entity="order",
        field_mappings=list(mappings),
        static_values=static or {},
    )


@pytest.fixture()
def source_data() -> dict:
    return {
        "buyer": {
            "first_name": "Jan",
            "last_name": "Kowalski",
            "email": "jan@example.com",
        },
        "amount": "199.99",
        "quantity": "5",
        "status": "new",
        "date_str": "2026-02-25",
        "datetime_str": "2026-02-25T14:30:00",
        "flag": "true",
        "address": {
            "street": "  Marszałkowska 1  ",
            "city": "Warszawa",
            "zip": "00-001",
        },
        "description": "Order #123 — priority",
        "tags": "electronics,fragile",
        "phone": "+48 123 456 789",
        "empty_field": None,
    }


# ── _resolve_sources ──


class TestBaseMapperResolveSources:
    def test_single_source_field(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="buyer.first_name", target_field="name")
        mapper = BaseMapper(_profile(fm))
        assert mapper._resolve_sources(fm, source_data) == ["Jan"]

    def test_multi_source_fields(self, source_data: dict) -> None:
        fm = FieldMapping(
            source_fields=["buyer.first_name", "buyer.last_name"],
            target_field="full_name",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._resolve_sources(fm, source_data) == ["Jan", "Kowalski"]

    def test_source_fields_takes_priority(self, source_data: dict) -> None:
        fm = FieldMapping(
            source_field="buyer.email",
            source_fields=["buyer.first_name"],
            target_field="name",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._resolve_sources(fm, source_data) == ["Jan"]

    def test_no_source_returns_empty(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="", target_field="out")
        mapper = BaseMapper(_profile(fm))
        assert mapper._resolve_sources(fm, source_data) == []

    def test_missing_field_returns_none(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="no.such.field", target_field="out")
        mapper = BaseMapper(_profile(fm))
        assert mapper._resolve_sources(fm, source_data) == [None]


# ── _apply_transform — type conversion transforms ──


class TestBaseMapperTypeTransforms:
    def test_none_single_value(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="buyer.first_name", target_field="name", transform=TransformType.NONE)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Jan"]) == "Jan"

    def test_none_multi_value(self, source_data: dict) -> None:
        fm = FieldMapping(
            source_fields=["buyer.first_name", "buyer.last_name"],
            target_field="name",
            transform=TransformType.NONE,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Jan", "Kowalski"]) == "Jan Kowalski"

    def test_string(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.STRING)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [42]) == "42"

    def test_integer(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.INTEGER)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["42"]) == 42

    def test_decimal(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.DECIMAL)
        mapper = BaseMapper(_profile(fm))
        result = mapper._apply_transform(fm, ["199.99"])
        assert result == Decimal("199.99")

    def test_decimal_invalid(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.DECIMAL, default_value="N/A")
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["not-a-number"]) == "N/A"

    def test_boolean_true_variants(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.BOOLEAN)
        mapper = BaseMapper(_profile(fm))
        for val in ["true", "1", "yes", "tak", True]:
            assert mapper._apply_transform(fm, [val]) is True

    def test_boolean_false(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.BOOLEAN)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["false"]) is False

    def test_date(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.DATE)
        mapper = BaseMapper(_profile(fm))
        result = mapper._apply_transform(fm, ["2026-02-25"])
        assert result == date(2026, 2, 25)

    def test_date_passthrough(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.DATE)
        mapper = BaseMapper(_profile(fm))
        d = date(2026, 1, 1)
        assert mapper._apply_transform(fm, [d]) is d

    def test_datetime(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.DATETIME)
        mapper = BaseMapper(_profile(fm))
        result = mapper._apply_transform(fm, ["2026-02-25T14:30:00"])
        assert result == datetime(2026, 2, 25, 14, 30, 0)


# ── _apply_transform — string transforms ──


class TestBaseMapperStringTransforms:
    def test_uppercase(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.UPPERCASE)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["hello"]) == "HELLO"

    def test_lowercase(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.LOWERCASE)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["HELLO"]) == "hello"

    def test_strip(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.STRIP)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["  hello  "]) == "hello"

    def test_trim_alias(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.TRIM)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["  hello  "]) == "hello"

    def test_prepend(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.PREPEND, prepend_value="PRE-")
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["val"]) == "PRE-val"

    def test_prepend_none(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.PREPEND, prepend_value="X")
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None]) is None

    def test_append(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.APPEND, append_value="-SUF")
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["val"]) == "val-SUF"

    def test_append_none(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.APPEND, append_value="X")
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None]) is None

    def test_split(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.SPLIT, separator=",")
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["a,b,c"]) == ["a", "b", "c"]

    def test_split_none(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.SPLIT)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None]) == []

    def test_replace(self) -> None:
        fm = FieldMapping(
            source_field="x",
            target_field="y",
            transform=TransformType.REPLACE,
            regex_pattern="-",
            regex_replacement="_",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["a-b-c"]) == "a_b_c"

    def test_replace_none(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.REPLACE, regex_pattern="-", regex_replacement="_")
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None]) is None

    def test_substring(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.SUBSTRING, substring_start=0, substring_end=5)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Hello World"]) == "Hello"

    def test_substring_start_only(self) -> None:
        fm = FieldMapping(source_field="x", target_field="y", transform=TransformType.SUBSTRING, substring_start=6)
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Hello World"]) == "World"


# ── _apply_transform — regex transforms ──


class TestBaseMapperRegexTransforms:
    def test_regex_extract(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.REGEX_EXTRACT,
            regex_pattern=r"#(\d+)", regex_group=1,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Order #123"]) == "123"

    def test_regex_extract_no_match(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.REGEX_EXTRACT,
            regex_pattern=r"\d+",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["no digits"]) is None

    def test_regex_extract_none(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.REGEX_EXTRACT,
            regex_pattern=r"\d+",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None]) is None

    def test_regex_extract_invalid_group(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.REGEX_EXTRACT,
            regex_pattern=r"(\d+)", regex_group=5,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["test 123"]) == "123"

    def test_regex_replace(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.REGEX_REPLACE,
            regex_pattern=r"\s+", regex_replacement="-",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["a  b  c"]) == "a-b-c"

    def test_regex_replace_none(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.REGEX_REPLACE,
            regex_pattern=r"\d", regex_replacement="",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None]) is None


# ── _apply_transform — map / lookup ──


class TestBaseMapperMapTransforms:
    def test_map_value(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MAP_VALUE,
            value_map={"new": "NOWY", "done": "GOTOWY"},
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["new"]) == "NOWY"

    def test_map_value_missing_returns_default(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MAP_VALUE,
            value_map={"a": "1"},
            default_value="UNKNOWN",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["missing"]) == "UNKNOWN"

    def test_lookup_alias(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.LOOKUP,
            value_map={"a": "1"},
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["a"]) == "1"


# ── _apply_transform — multi-source transforms ──


class TestBaseMapperMultiSourceTransforms:
    def test_template(self) -> None:
        fm = FieldMapping(
            source_fields=["x", "y"], target_field="out",
            transform=TransformType.TEMPLATE,
            template="{{0}} {{1}}",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Jan", "Kowalski"]) == "Jan Kowalski"

    def test_template_with_none(self) -> None:
        fm = FieldMapping(
            source_fields=["x", "y"], target_field="out",
            transform=TransformType.TEMPLATE,
            template="{{0}} {{1}}",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Jan", None]) == "Jan "

    def test_join(self) -> None:
        fm = FieldMapping(
            source_fields=["x", "y"], target_field="out",
            transform=TransformType.JOIN,
            separator=", ",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["Warszawa", "Polska"]) == "Warszawa, Polska"

    def test_join_filters_none(self) -> None:
        fm = FieldMapping(
            source_fields=["x", "y", "z"], target_field="out",
            transform=TransformType.JOIN,
            separator="-",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["a", None, "c"]) == "a-c"

    def test_coalesce(self) -> None:
        fm = FieldMapping(
            source_fields=["x", "y", "z"], target_field="out",
            transform=TransformType.COALESCE,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None, None, "found"]) == "found"

    def test_coalesce_all_none(self) -> None:
        fm = FieldMapping(
            source_fields=["x", "y"], target_field="out",
            transform=TransformType.COALESCE,
            default_value="fallback",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [None, None]) == "fallback"


# ── _apply_transform — date_format, math ──


class TestBaseMapperDateMathTransforms:
    def test_date_format(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.DATE_FORMAT,
            input_format="%Y-%m-%d",
            output_format="%d.%m.%Y",
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["2026-02-25"]) == "25.02.2026"

    def test_date_format_invalid(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.DATE_FORMAT,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["bad"]) == "bad"

    def test_math_add(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MATH,
            math_operation="add", math_operand=10,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [5]) == pytest.approx(15.0)

    def test_math_sub(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MATH,
            math_operation="sub", math_operand=3,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [10]) == pytest.approx(7.0)

    def test_math_mul(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MATH,
            math_operation="mul", math_operand=4,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [5]) == pytest.approx(20.0)

    def test_math_div(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MATH,
            math_operation="div", math_operand=2,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [10]) == pytest.approx(5.0)

    def test_math_div_zero(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MATH,
            math_operation="div", math_operand=0,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, [10]) == 10

    def test_math_invalid_value(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.MATH,
            math_operation="add", math_operand=5,
        )
        mapper = BaseMapper(_profile(fm))
        assert mapper._apply_transform(fm, ["abc"]) == "abc"


# ── _apply_transform — custom transform ──


class TestBaseMapperCustomTransform:
    def test_custom_registered(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.CUSTOM,
            custom_transform_name="double_it",
        )
        mapper = BaseMapper(_profile(fm))
        mapper.register_custom_transform("double_it", lambda v: v * 2)
        assert mapper._apply_transform(fm, [5]) == 10

    def test_custom_not_registered(self) -> None:
        fm = FieldMapping(
            source_field="x", target_field="y",
            transform=TransformType.CUSTOM,
            custom_transform_name="missing_func",
        )
        mapper = BaseMapper(_profile(fm))
        with pytest.raises(MappingError, match="not registered"):
            mapper._apply_transform(fm, [5])


# ── map() — full integration tests ──


class TestBaseMapperMap:
    def test_simple_mapping(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="buyer.first_name", target_field="name")
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert result == {"name": "Jan"}

    def test_multi_source_mapping(self, source_data: dict) -> None:
        fm = FieldMapping(
            source_fields=["buyer.first_name", "buyer.last_name"],
            target_field="full_name",
            transform=TransformType.JOIN,
            separator=" ",
        )
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert result == {"full_name": "Jan Kowalski"}

    def test_static_values(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="buyer.first_name", target_field="name")
        mapper = BaseMapper(_profile(fm, static={"source": "ECOMMERCE", "type": "ZK"}))
        result = mapper.map(source_data)
        assert result == {"name": "Jan", "source": "ECOMMERCE", "type": "ZK"}

    def test_default_value(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="nonexistent", target_field="out", default_value="N/A")
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert result == {"out": "N/A"}

    def test_required_field_missing(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="nonexistent", target_field="out", required=True)
        mapper = BaseMapper(_profile(fm))
        with pytest.raises(MappingError, match="Required"):
            mapper.map(source_data)

    def test_nested_target(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="buyer.email", target_field="contact.email")
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert result == {"contact": {"email": "jan@example.com"}}

    def test_extra_transforms_chain(self, source_data: dict) -> None:
        fm = FieldMapping(
            source_field="address.street",
            target_field="clean_street",
            transform=TransformType.TRIM,
            extra_transforms=[
                FieldMapping(source_field="", target_field="", transform=TransformType.UPPERCASE),
            ],
        )
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert result == {"clean_street": "MARSZAŁKOWSKA 1"}

    def test_extra_transforms_three_steps(self, source_data: dict) -> None:
        fm = FieldMapping(
            source_field="description",
            target_field="ref",
            transform=TransformType.REGEX_EXTRACT,
            regex_pattern=r"#(\d+)",
            regex_group=1,
            extra_transforms=[
                FieldMapping(source_field="", target_field="", transform=TransformType.PREPEND, prepend_value="REF-"),
                FieldMapping(source_field="", target_field="", transform=TransformType.UPPERCASE),
            ],
        )
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert result == {"ref": "REF-123"}

    def test_multiple_mappings(self, source_data: dict) -> None:
        mappings = [
            FieldMapping(source_field="buyer.first_name", target_field="first"),
            FieldMapping(source_field="buyer.last_name", target_field="last"),
            FieldMapping(
                source_field="amount",
                target_field="price",
                transform=TransformType.DECIMAL,
            ),
        ]
        mapper = BaseMapper(_profile(*mappings))
        result = mapper.map(source_data)
        assert result == {"first": "Jan", "last": "Kowalski", "price": Decimal("199.99")}

    def test_map_list(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="buyer.first_name", target_field="name")
        mapper = BaseMapper(_profile(fm))
        items = [source_data, {**source_data, "buyer": {"first_name": "Anna", "last_name": "Nowak", "email": "a@b.com"}}]
        results = mapper.map_list(items)
        assert len(results) == 2
        assert results[0] == {"name": "Jan"}
        assert results[1] == {"name": "Anna"}

    def test_math_chain_with_extra_transforms(self, source_data: dict) -> None:
        fm = FieldMapping(
            source_field="amount",
            target_field="total_vat",
            transform=TransformType.DECIMAL,
            extra_transforms=[
                FieldMapping(
                    source_field="", target_field="",
                    transform=TransformType.STRING,
                ),
            ],
        )
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert result == {"total_vat": "199.99"}

    def test_none_field_with_no_default_skipped(self, source_data: dict) -> None:
        fm = FieldMapping(source_field="empty_field", target_field="out")
        mapper = BaseMapper(_profile(fm))
        result = mapper.map(source_data)
        assert "out" not in result


# ── FieldMapping / MappingProfile model tests ──


class TestMappingModels:
    def test_field_mapping_defaults(self) -> None:
        fm = FieldMapping(target_field="out")
        assert fm.source_field == ""
        assert fm.source_fields == []
        assert fm.transform == TransformType.NONE
        assert fm.default_value is None
        assert fm.required is False
        assert fm.extra_transforms == []

    def test_field_mapping_extra_transforms(self) -> None:
        fm = FieldMapping(
            source_field="x",
            target_field="y",
            extra_transforms=[
                FieldMapping(source_field="", target_field="", transform=TransformType.UPPERCASE),
                FieldMapping(source_field="", target_field="", transform=TransformType.TRIM),
            ],
        )
        assert len(fm.extra_transforms) == 2
        assert fm.extra_transforms[0].transform == TransformType.UPPERCASE

    def test_mapping_profile_defaults(self) -> None:
        p = _profile()
        assert p.field_mappings == []
        assert p.static_values == {}
        assert p.ignore_unmapped is True
        assert p.enabled is True

    def test_all_transform_types_exist(self) -> None:
        expected = {
            "none", "string", "integer", "decimal", "date", "datetime", "boolean",
            "uppercase", "lowercase", "strip", "map_value", "template", "custom",
            "regex_extract", "regex_replace", "coalesce", "join", "substring",
            "date_format", "math", "prepend", "append", "lookup", "split", "replace", "trim",
        }
        actual = {t.value for t in TransformType}
        assert expected == actual

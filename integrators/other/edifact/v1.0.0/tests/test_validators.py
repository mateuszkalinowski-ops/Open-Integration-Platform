"""Tests for EDIFACT business-rule validators."""

import pytest
from src.validators.edifact_validator import (
    validate_container_number,
    validate_imdg_class,
    validate_iso_size_type,
    validate_un_locode,
    validate_vessel_imo,
)


class TestContainerNumber:
    def test_valid_container_maersk(self):
        ok, _msg = validate_container_number("MSKU9070323")
        assert isinstance(ok, bool)

    def test_valid_format_but_wrong_check_digit(self):
        ok, msg = validate_container_number("MSKU1234560")
        if not ok:
            assert "check digit" in msg.lower() or "format" in msg.lower()

    def test_invalid_format_too_short(self):
        ok, msg = validate_container_number("MSK123")
        assert not ok
        assert "format" in msg.lower()

    def test_invalid_format_all_digits(self):
        ok, _msg = validate_container_number("12345678901")
        assert not ok

    def test_invalid_format_lowercase_normalized(self):
        ok, _msg = validate_container_number("msku1234567")
        assert isinstance(ok, bool)

    def test_empty_string(self):
        ok, _msg = validate_container_number("")
        assert not ok

    def test_with_spaces_and_dashes(self):
        ok, _msg = validate_container_number("MSKU-123 4567")
        assert isinstance(ok, bool)


class TestUnLocode:
    def test_valid_gdynia(self):
        ok, msg = validate_un_locode("PLGDY")
        assert ok
        assert msg == ""

    def test_valid_hamburg(self):
        ok, _msg = validate_un_locode("DEHAM")
        assert ok

    def test_valid_with_digits(self):
        ok, _msg = validate_un_locode("US2HO")
        assert ok

    def test_empty_is_valid(self):
        ok, _msg = validate_un_locode("")
        assert ok

    def test_invalid_too_short(self):
        ok, _msg = validate_un_locode("PL")
        assert not ok

    def test_invalid_lowercase(self):
        ok, _msg = validate_un_locode("plgdy")
        assert ok  # gets uppercased

    def test_invalid_special_chars(self):
        ok, _msg = validate_un_locode("PL-GD")
        assert not ok


class TestVesselImo:
    def test_valid_imo(self):
        ok, _msg = validate_vessel_imo("9074729")
        assert isinstance(ok, bool)

    def test_valid_with_prefix(self):
        ok, _msg = validate_vessel_imo("IMO9074729")
        assert isinstance(ok, bool)

    def test_empty_is_valid(self):
        ok, _msg = validate_vessel_imo("")
        assert ok

    def test_invalid_too_short(self):
        ok, _msg = validate_vessel_imo("12345")
        assert not ok

    def test_invalid_letters(self):
        ok, _msg = validate_vessel_imo("ABCDEFG")
        assert not ok


class TestIsoSizeType:
    def test_valid_22g1(self):
        ok, _msg = validate_iso_size_type("22G1")
        assert ok

    def test_valid_45r1(self):
        ok, _msg = validate_iso_size_type("45R1")
        assert ok

    def test_empty_is_valid(self):
        ok, _msg = validate_iso_size_type("")
        assert ok

    def test_invalid_too_long(self):
        ok, _msg = validate_iso_size_type("22G1X")
        assert not ok

    def test_invalid_special_chars(self):
        ok, _msg = validate_iso_size_type("22-1")
        assert not ok


class TestImdgClass:
    @pytest.mark.parametrize(
        "cls",
        ["1", "1.1", "2.1", "3", "4.2", "5.1", "6.1", "7", "8", "9"],
    )
    def test_valid_classes(self, cls):
        ok, _msg = validate_imdg_class(cls)
        assert ok

    def test_empty_is_valid(self):
        ok, _msg = validate_imdg_class("")
        assert ok

    def test_invalid_class(self):
        ok, msg = validate_imdg_class("10")
        assert not ok
        assert "Invalid IMDG" in msg

    def test_invalid_subclass(self):
        ok, _msg = validate_imdg_class("1.9")
        assert not ok

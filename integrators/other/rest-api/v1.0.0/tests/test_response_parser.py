"""Tests for ResponseParser."""

from __future__ import annotations

from src.schemas.account import AccountConfig, ResponseMappingConfig
from src.services.response_parser import ResponseParser


def _make_account(mapping: ResponseMappingConfig, profile: str = "auto") -> AccountConfig:
    return AccountConfig(
        name="test",
        base_url="https://example.com",
        profile=profile,
        response_mapping=mapping,
    )


def test_http_status_mode_success():
    account = _make_account(ResponseMappingConfig(use_http_status=True))
    parser = ResponseParser(account)
    result = parser.parse(200, {"items": [1, 2]}, 42, "test/endpoint")
    assert result.status == "success"
    assert result.http_status == 200
    assert result.data == {"items": [1, 2]}
    assert result.elapsed_ms == 42


def test_http_status_mode_error():
    account = _make_account(ResponseMappingConfig(use_http_status=True))
    parser = ResponseParser(account)
    result = parser.parse(500, {"error": "fail"}, 100, "test/endpoint")
    assert result.status == "error"
    assert result.http_status == 500


def test_pinquark_profile_ok():
    account = _make_account(
        ResponseMappingConfig(
            status_field="status",
            status_ok_values=["OK"],
            message_field="message",
            data_field="data",
        )
    )
    parser = ResponseParser(account)
    body = {"status": "OK", "message": "AWK created", "data": {"doc_id": 123}}
    result = parser.parse(200, body, 55, "tos_notification_rail_save")
    assert result.status == "success"
    assert result.response_status == "OK"
    assert result.message == "AWK created"
    assert result.data == {"doc_id": 123}


def test_pinquark_profile_error():
    account = _make_account(
        ResponseMappingConfig(
            status_field="status",
            status_ok_values=["OK"],
            status_error_values=["ERROR"],
            message_field="message",
            data_field="data",
        )
    )
    parser = ResponseParser(account)
    body = {"status": "ERROR", "message": "Invalid train number"}
    result = parser.parse(200, body, 30, "tos_notification_rail_save")
    assert result.status == "error"
    assert result.response_status == "ERROR"
    assert result.message == "Invalid train number"


def test_nested_status_field():
    account = _make_account(
        ResponseMappingConfig(
            status_field="d.Status",
            status_ok_values=["SUCCESS"],
            data_field="d",
        )
    )
    parser = ResponseParser(account)
    body = {"d": {"Status": "SUCCESS", "results": [{"id": 1}]}}
    result = parser.parse(200, body, 80, "materials")
    assert result.status == "success"
    assert result.data == {"Status": "SUCCESS", "results": [{"id": 1}]}


def test_auto_detect_pinquark():
    account = _make_account(ResponseMappingConfig(use_http_status=True))
    parser = ResponseParser(account)
    profile = parser.auto_detect_profile({"status": "OK", "message": "test", "data": {}})
    assert profile == "pinquark"


def test_auto_detect_sap():
    account = _make_account(ResponseMappingConfig(use_http_status=True))
    parser = ResponseParser(account)
    profile = parser.auto_detect_profile({"d": {"results": []}})
    assert profile == "sap"


def test_auto_detect_generic():
    account = _make_account(ResponseMappingConfig(use_http_status=True))
    parser = ResponseParser(account)
    profile = parser.auto_detect_profile({"items": [1, 2, 3]})
    assert profile == "generic"

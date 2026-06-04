"""Tests for SellAsist Pydantic schemas."""

import pytest
from pydantic import ValidationError
from src.schemas import ErrorResponse, LabelRequest, SellAsistCredentials


class TestSellAsistCredentials:
    def test_create_credentials(self):
        creds = SellAsistCredentials(login="myshop", api_key="key-123")
        assert creds.login == "myshop"
        assert creds.api_key == "key-123"

    def test_credentials_serialization(self):
        creds = SellAsistCredentials(login="shop", api_key="k")
        data = creds.model_dump()
        assert data["login"] == "shop"
        assert data["api_key"] == "k"

    def test_credentials_missing_login_raises(self):
        with pytest.raises(ValidationError):
            SellAsistCredentials(api_key="key")

    def test_credentials_missing_api_key_raises(self):
        with pytest.raises(ValidationError):
            SellAsistCredentials(login="shop")


class TestLabelRequest:
    def test_create_label_request(self):
        req = LabelRequest(
            credentials=SellAsistCredentials(login="shop", api_key="key"),
            waybill_numbers=["WB001"],
            external_id="EXT-001",
        )
        assert req.waybill_numbers == ["WB001"]
        assert req.external_id == "EXT-001"

    def test_label_request_multiple_waybills(self):
        req = LabelRequest(
            credentials=SellAsistCredentials(login="shop", api_key="key"),
            waybill_numbers=["WB001", "WB002", "WB003"],
            external_id="EXT-002",
        )
        assert len(req.waybill_numbers) == 3

    def test_label_request_empty_waybills_raises(self):
        with pytest.raises(ValidationError):
            LabelRequest(
                credentials=SellAsistCredentials(login="shop", api_key="key"),
                waybill_numbers=[],
                external_id="EXT",
            )

    def test_label_request_missing_external_id_raises(self):
        with pytest.raises(ValidationError):
            LabelRequest(
                credentials=SellAsistCredentials(login="shop", api_key="key"),
                waybill_numbers=["WB001"],
            )

    def test_label_request_serialization(self):
        req = LabelRequest(
            credentials=SellAsistCredentials(login="s", api_key="k"),
            waybill_numbers=["WB001"],
            external_id="E1",
        )
        data = req.model_dump()
        assert "credentials" in data
        assert "waybill_numbers" in data
        assert "external_id" in data


class TestErrorResponse:
    def test_error_response(self):
        resp = ErrorResponse(error={"code": "FAIL", "message": "Something went wrong"})
        assert resp.error["code"] == "FAIL"

    def test_error_response_serialization(self):
        resp = ErrorResponse(
            error={
                "code": "LABEL_RETRIEVAL_FAILED",
                "message": "Not found",
                "details": {},
                "trace_id": "abc123",
            }
        )
        data = resp.model_dump()
        assert data["error"]["code"] == "LABEL_RETRIEVAL_FAILED"
        assert data["error"]["trace_id"] == "abc123"

    def test_error_response_empty_error_dict(self):
        resp = ErrorResponse(error={})
        assert resp.error == {}

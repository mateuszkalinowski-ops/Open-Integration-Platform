"""Tests for EDIFACT raw parser."""

from __future__ import annotations

from pathlib import Path

import pytest
from src.services.edifact_parser import EdifactParseError, parse_edifact

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "edifact"


def _read_fixture(subdir: str, filename: str) -> str:
    return (FIXTURES_DIR / subdir / filename).read_text(encoding="utf-8")


def test_parse_coprar_basic():
    content = _read_fixture("coprar", "coprar_hhla_basic.edi")
    result = parse_edifact(content)

    assert result["msg_type"] == "COPRAR"
    assert result["sender_id"] == "HHLA"
    assert result["receiver_id"] == "PLMSCMAL01"
    assert result["message_ref"] == "MSG001"

    payload = result["payload"]
    assert payload["document_id"] == "COPRAR-HHLA-001"
    assert payload["function_code"] == "original"
    assert payload["train_no"] == "MET-204"

    wagons = payload["wagons"]
    assert len(wagons) == 2

    assert wagons[0]["wagon_no"] == "31805476432"
    assert len(wagons[0]["containers"]) == 2

    container1 = wagons[0]["containers"][0]
    assert container1["container_no"] == "MEDU1234567"
    assert container1["weight_kg"] == 25400.0
    assert container1["is_empty"] is False
    assert container1["seal_no"] == "SEAL001"


def test_parse_coprar_cancel():
    content = _read_fixture("coprar", "coprar_cancel.edi")
    result = parse_edifact(content)

    assert result["msg_type"] == "COPRAR"
    assert result["payload"]["function_code"] == "cancel"
    assert result["payload"]["document_id"] == "COPRAR-HHLA-001"


def test_parse_coparn_release():
    content = _read_fixture("coparn", "coparn_release.edi")
    result = parse_edifact(content)

    assert result["msg_type"] == "COPARN"
    payload = result["payload"]
    assert payload["document_id"] == "COPARN-MET-001"
    assert payload["function_code"] == "original"
    assert payload["container_no"] == "MEDU1234567"
    assert payload["carrier"]["code"] == "METRANS"
    assert payload["haulier"]["code"] == "TRANSPORT-PL"


def test_parse_cohaor_load():
    content = _read_fixture("cohaor", "cohaor_load.edi")
    result = parse_edifact(content)

    assert result["msg_type"] == "COHAOR"
    payload = result["payload"]
    assert payload["document_id"] == "COHAOR-KOM-001"
    assert payload["container_no"] == "TRLU8765432"
    assert len(payload["special_instructions"]) == 1


def test_parse_coarri_partial():
    content = _read_fixture("coarri", "coarri_partial.edi")
    result = parse_edifact(content)

    assert result["msg_type"] == "COARRI"
    payload = result["payload"]
    assert payload["document_id"] == "COARRI-MAL-001"
    assert len(payload["containers"]) == 3
    assert payload["containers"][0]["container_no"] == "MEDU1234567"
    assert payload["containers"][0]["weight_kg"] == 25400.0


def test_parse_iftsta_gtin():
    content = _read_fixture("iftsta", "iftsta_gtin.edi")
    result = parse_edifact(content)

    assert result["msg_type"] == "IFTSTA"
    payload = result["payload"]
    assert payload["document_id"] == "IFTSTA-MAL-001"
    assert payload["status_code"] == "GTI"
    assert payload["container_no"] == "MEDU1234567"
    assert len(payload["references"]) == 1


def test_parse_empty_content():
    with pytest.raises(EdifactParseError, match="Empty"):
        parse_edifact("")


def test_parse_invalid_content():
    with pytest.raises(EdifactParseError):
        parse_edifact("NOT_EDIFACT_CONTENT")


def test_parse_bytes_input():
    content = _read_fixture("coprar", "coprar_cancel.edi")
    result = parse_edifact(content.encode("utf-8"))
    assert result["msg_type"] == "COPRAR"

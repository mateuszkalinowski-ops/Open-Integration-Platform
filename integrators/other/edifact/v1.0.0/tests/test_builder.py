"""Tests for EDIFACT raw builder — including round-trip tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from src.services.edifact_builder import SequenceProvider, build_edifact
from src.services.edifact_parser import parse_edifact

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "edifact"


@pytest.fixture
def seq() -> SequenceProvider:
    return SequenceProvider()


def test_build_coprar_basic(seq: SequenceProvider):
    payload = {
        "document_id": "TEST-COPRAR-001",
        "function_code": "original",
        "train_no": "MET-100",
        "eta": "202604201000",
        "carrier": {"code": "HHLA"},
        "pol": {"un_locode": "DEHAM"},
        "pod": {"un_locode": "PLMAL"},
        "wagons": [
            {
                "wagon_no": "31805476432",
                "wagon_type": "Sgnss",
                "containers": [
                    {
                        "container_no": "MEDU1234567",
                        "iso_size_type": "22G1",
                        "weight_kg": 25400,
                        "is_empty": False,
                        "seal_no": "SEAL001",
                    }
                ],
            }
        ],
    }

    result = build_edifact("COPRAR", "D00B", "PLMSC", "HHLA", payload, seq)

    assert "UNB+" in result
    assert "UNH+" in result
    assert "COPRAR" in result
    assert "MET-100" in result
    assert "MEDU1234567" in result
    assert "UNT+" in result
    assert "UNZ+" in result


def test_build_aperak_accepted(seq: SequenceProvider):
    payload = {
        "document_id": "APK-001",
        "referenced_interchange_ref": "REF12345",
        "referenced_message_ref": "MSG001",
        "response_type": "accepted",
    }

    result = build_edifact("APERAK", "D00B", "PLMSC", "HHLA", payload, seq)
    assert "APERAK" in result
    assert "ACW" in result
    assert "REF12345" in result


def test_build_aperak_rejected(seq: SequenceProvider):
    payload = {
        "document_id": "APK-002",
        "referenced_interchange_ref": "REF12345",
        "referenced_message_ref": "MSG001",
        "response_type": "rejected",
        "errors": [
            {"error_code": "12", "free_text": "Invalid container number"},
        ],
    }

    result = build_edifact("APERAK", "D00B", "PLMSC", "HHLA", payload, seq)
    assert "ERC+12" in result
    assert "Invalid container number" in result


def test_build_contrl_ok(seq: SequenceProvider):
    payload = {
        "referenced_interchange_ref": "REF12345",
        "sender_id": "PLMSC",
        "receiver_id": "HHLA",
        "syntax_status": "ok",
    }

    result = build_edifact("CONTRL", "D00B", "PLMSC", "HHLA", payload, seq)
    assert "CONTRL" in result
    assert "UCI+" in result


def test_build_iftsta_with_tos_status(seq: SequenceProvider):
    payload = {
        "document_id": "STA-001",
        "function_code": "original",
        "tos_status": "WJAZD_TIR_POTWIERDZONY",
        "status_time": "202604201430",
        "container_no": "MEDU1234567",
    }

    result = build_edifact("IFTSTA", "D00B", "PLMSC", "METRANS", payload, seq)
    assert "IFTSTA" in result
    assert "GTI" in result
    assert "MEDU1234567" in result


def test_build_coarri(seq: SequenceProvider):
    payload = {
        "document_id": "ARR-001",
        "function_code": "original",
        "transport": {"voyage_no": "MET-204"},
        "completion_time": "202604201100",
        "containers": [
            {"container_no": "MEDU1234567", "weight_kg": 25400, "seal_no": "SEAL001"},
            {"container_no": "TRLU8765432", "weight_kg": 12000},
        ],
    }

    result = build_edifact("COARRI", "D00B", "PLMSC", "HHLA", payload, seq)
    assert "COARRI" in result
    assert "MEDU1234567" in result
    assert "TRLU8765432" in result


def test_round_trip_coprar(seq: SequenceProvider):
    """Build COPRAR then parse it back — key fields should survive."""
    payload = {
        "document_id": "RT-COPRAR-001",
        "function_code": "original",
        "train_no": "RT-100",
        "eta": "202604201000",
        "carrier": {"code": "HHLA"},
        "wagons": [
            {
                "wagon_no": "31805476432",
                "wagon_type": "Sgnss",
                "containers": [
                    {
                        "container_no": "MEDU1234567",
                        "iso_size_type": "22G1",
                        "weight_kg": 25000,
                        "is_empty": False,
                    }
                ],
            }
        ],
    }

    built = build_edifact("COPRAR", "D00B", "PLMSC", "HHLA", payload, seq)
    parsed = parse_edifact(built)

    assert parsed["msg_type"] == "COPRAR"
    assert parsed["payload"]["document_id"] == "RT-COPRAR-001"
    assert parsed["payload"]["function_code"] == "original"
    assert parsed["payload"]["train_no"] == "RT-100"
    assert len(parsed["payload"]["wagons"]) >= 1


def test_round_trip_coarri(seq: SequenceProvider):
    payload = {
        "document_id": "RT-COARRI-001",
        "function_code": "original",
        "transport": {"voyage_no": "MET-204"},
        "containers": [
            {"container_no": "MEDU1234567", "weight_kg": 25400},
        ],
    }

    built = build_edifact("COARRI", "D00B", "PLMSC", "HHLA", payload, seq)
    parsed = parse_edifact(built)

    assert parsed["msg_type"] == "COARRI"
    assert parsed["payload"]["document_id"] == "RT-COARRI-001"
    assert len(parsed["payload"]["containers"]) == 1


def test_sequence_provider_increments(seq: SequenceProvider):
    ref1 = seq.next_interchange_ref("TEST_PARTNER")
    ref2 = seq.next_interchange_ref("TEST_PARTNER")
    assert int(ref1) < int(ref2)


def test_smdg2_version_in_unh(seq: SequenceProvider):
    payload = {"document_id": "V-001", "function_code": "original"}
    result = build_edifact("APERAK", "SMDG2.0", "PLMSC", "HHLA", payload, seq)
    assert "SMDG20" in result

"""Raw EDIFACT builder — converts structured JSON dict to .edi content string.

Generates valid UNB/UNH/UNT/UNZ envelopes with proper segment counting
and sequence numbering per partner.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.services.edifact_segments import (
    FUNCTION_CODE_REVERSE,
    SMDG_STATUS_CODES,
    TOS_STATUS_TO_SMDG,
)

logger = logging.getLogger(__name__)

SEGMENT_TERMINATOR = "'"
ELEMENT_SEPARATOR = "+"
COMPONENT_SEPARATOR = ":"


class EdifactBuildError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class SequenceProvider:
    """Manages UNB/UNH sequence numbers per partner. Persists to JSON on disk."""

    def __init__(self, state_dir: str = "") -> None:
        self._state_dir = state_dir
        self._counters: dict[str, dict[str, int]] = {}

    def next_interchange_ref(self, partner_id: str) -> str:
        state = self._load_state(partner_id)
        state["interchange"] = state.get("interchange", 0) + 1
        self._save_state(partner_id, state)
        return str(state["interchange"]).zfill(14)

    def next_message_ref(self, partner_id: str) -> str:
        state = self._load_state(partner_id)
        state["message"] = state.get("message", 0) + 1
        self._save_state(partner_id, state)
        return str(state["message"]).zfill(14)

    def _load_state(self, partner_id: str) -> dict[str, int]:
        if partner_id in self._counters:
            return self._counters[partner_id]

        if self._state_dir:
            state_file = Path(self._state_dir) / f"{partner_id}.json"
            if state_file.exists():
                with open(state_file, encoding="utf-8") as f:
                    state = json.load(f)
                self._counters[partner_id] = state
                return state

        self._counters[partner_id] = {"interchange": 0, "message": 0}
        return self._counters[partner_id]

    def _save_state(self, partner_id: str, state: dict[str, int]) -> None:
        self._counters[partner_id] = state
        if self._state_dir:
            state_dir = Path(self._state_dir)
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / f"{partner_id}.json"
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state, f)


_default_sequence = SequenceProvider()


def build_edifact(
    msg_type: str,
    version: str,
    sender_id: str,
    receiver_id: str,
    payload: dict[str, Any],
    sequence_provider: SequenceProvider | None = None,
) -> str:
    """Build a complete EDIFACT interchange string from message type and payload.

    Returns raw EDI content ready to be written to a .edi file.
    """
    sp = sequence_provider or _default_sequence
    partner_id = f"{sender_id}_{receiver_id}"

    interchange_ref = sp.next_interchange_ref(partner_id)
    message_ref = sp.next_message_ref(partner_id)

    now = datetime.now(UTC)
    date_str = now.strftime("%y%m%d")
    time_str = now.strftime("%H%M")

    version_parts = _split_version(version)

    body_segments = _build_message_body(msg_type, payload)

    segments: list[str] = []

    segments.append(
        _seg(
            "UNB",
            [
                f"UNOC{COMPONENT_SEPARATOR}3",
                sender_id,
                receiver_id,
                f"{date_str}{COMPONENT_SEPARATOR}{time_str}",
                interchange_ref,
            ],
        )
    )

    segments.append(
        _seg(
            "UNH",
            [
                message_ref,
                f"{msg_type}{COMPONENT_SEPARATOR}{version_parts[0]}{COMPONENT_SEPARATOR}"
                f"{version_parts[1]}{COMPONENT_SEPARATOR}UN{COMPONENT_SEPARATOR}SMDG20"
                if version == "SMDG2.0"
                else f"{msg_type}{COMPONENT_SEPARATOR}{version_parts[0]}{COMPONENT_SEPARATOR}"
                f"{version_parts[1]}{COMPONENT_SEPARATOR}UN",
            ],
        )
    )

    segments.extend(body_segments)

    segment_count = len(body_segments) + 2  # UNH + body + UNT
    segments.append(_seg("UNT", [str(segment_count), message_ref]))
    segments.append(_seg("UNZ", ["1", interchange_ref]))

    return "\n".join(segments) + "\n"


def _split_version(version: str) -> tuple[str, str]:
    """Split version string into directory/release parts."""
    version_map = {
        "D95B": ("D", "95B"),
        "D00B": ("D", "00B"),
        "D03B": ("D", "03B"),
        "SMDG2.0": ("D", "00B"),
    }
    return version_map.get(version, ("D", "00B"))


def _seg(tag: str, elements: list[str]) -> str:
    """Build a single EDIFACT segment string."""
    return tag + ELEMENT_SEPARATOR + ELEMENT_SEPARATOR.join(elements) + SEGMENT_TERMINATOR


def _build_message_body(msg_type: str, payload: dict[str, Any]) -> list[str]:
    """Dispatch to message-specific builder."""
    builders = {
        "COPRAR": _build_coprar,
        "COPARN": _build_coparn,
        "COHAOR": _build_cohaor,
        "COARRI": _build_coarri,
        "CODECO": _build_codeco,
        "IFTSTA": _build_iftsta,
        "IFTMIN": _build_iftmin,
        "APERAK": _build_aperak,
        "CONTRL": _build_contrl,
    }
    builder_fn = builders.get(msg_type)
    if not builder_fn:
        raise EdifactBuildError(f"Unsupported message type: {msg_type}")
    return builder_fn(payload)


def _build_coprar(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    fc = FUNCTION_CODE_REVERSE.get(p.get("function_code", "original"), "9")
    segs.append(_seg("BGM", ["266", p.get("document_id", ""), fc]))

    if p.get("eta"):
        segs.append(_seg("DTM", [f"132{COMPONENT_SEPARATOR}{p['eta']}{COMPONENT_SEPARATOR}203"]))
    if p.get("etd"):
        segs.append(_seg("DTM", [f"133{COMPONENT_SEPARATOR}{p['etd']}{COMPONENT_SEPARATOR}203"]))

    if p.get("train_no"):
        carrier_code = _nested(p, "carrier.code", "")
        segs.append(_seg("TDT", ["20", p["train_no"], "2", "", carrier_code]))

    if p.get("pol"):
        pol = p["pol"] if isinstance(p["pol"], dict) else {"un_locode": p["pol"]}
        segs.append(_seg("LOC", ["9", f"{pol.get('un_locode', '')}{COMPONENT_SEPARATOR}139{COMPONENT_SEPARATOR}6"]))
    if p.get("pod"):
        pod = p["pod"] if isinstance(p["pod"], dict) else {"un_locode": p["pod"]}
        segs.append(_seg("LOC", ["11", f"{pod.get('un_locode', '')}{COMPONENT_SEPARATOR}139{COMPONENT_SEPARATOR}6"]))

    carrier = p.get("carrier", {})
    if isinstance(carrier, dict) and carrier.get("code"):
        segs.append(_seg("NAD", ["CA", carrier["code"]]))

    for wagon in p.get("wagons", []):
        segs.append(_seg("EQD", ["RR", wagon.get("wagon_no", ""), wagon.get("wagon_type", "")]))
        for container in wagon.get("containers", []):
            segs.append(
                _seg(
                    "EQD",
                    [
                        "CN",
                        container.get("container_no", ""),
                        container.get("iso_size_type", ""),
                    ],
                )
            )
            weight = container.get("weight_kg", 0)
            if weight:
                segs.append(_seg("MEA", ["AAE", "G", f"KGM{COMPONENT_SEPARATOR}{weight}"]))
            fe_code = "4" if container.get("is_empty") else "5"
            segs.append(_seg("EQN", [fe_code]))
            if container.get("seal_no"):
                segs.append(_seg("SEL", [container["seal_no"]]))

    return segs


def _build_coparn(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    fc = FUNCTION_CODE_REVERSE.get(p.get("function_code", "original"), "9")
    segs.append(_seg("BGM", ["267", p.get("document_id", ""), fc]))

    if p.get("container_no"):
        segs.append(_seg("EQD", ["CN", p["container_no"], p.get("iso_size_type", "")]))

    if p.get("pickup_window_from"):
        segs.append(_seg("DTM", [f"200{COMPONENT_SEPARATOR}{p['pickup_window_from']}{COMPONENT_SEPARATOR}203"]))
    if p.get("pickup_window_to"):
        segs.append(_seg("DTM", [f"63{COMPONENT_SEPARATOR}{p['pickup_window_to']}{COMPONENT_SEPARATOR}203"]))

    carrier = p.get("carrier", {})
    if isinstance(carrier, dict) and carrier.get("code"):
        segs.append(_seg("NAD", ["CA", carrier["code"]]))

    haulier = p.get("haulier", {})
    if isinstance(haulier, dict) and haulier.get("code"):
        segs.append(_seg("NAD", ["HE", haulier["code"]]))

    for ref in p.get("references", []):
        segs.append(_seg("RFF", [f"{ref.get('qualifier', 'BN')}{COMPONENT_SEPARATOR}{ref.get('value', '')}"]))

    return segs


def _build_cohaor(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    fc = FUNCTION_CODE_REVERSE.get(p.get("function_code", "original"), "9")
    segs.append(_seg("BGM", ["268", p.get("document_id", ""), fc]))

    if p.get("container_no"):
        segs.append(_seg("EQD", ["CN", p["container_no"]]))

    if p.get("requested_time"):
        segs.append(_seg("DTM", [f"2{COMPONENT_SEPARATOR}{p['requested_time']}{COMPONENT_SEPARATOR}203"]))

    for instruction in p.get("special_instructions", []):
        segs.append(_seg("FTX", ["AAA", "", "", instruction]))

    return segs


def _build_coarri(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    fc = FUNCTION_CODE_REVERSE.get(p.get("function_code", "original"), "9")
    segs.append(_seg("BGM", ["236", p.get("document_id", ""), fc]))

    transport = p.get("transport", {})
    if transport:
        segs.append(_seg("TDT", ["20", transport.get("voyage_no", ""), "2"]))

    if p.get("completion_time"):
        segs.append(_seg("DTM", [f"178{COMPONENT_SEPARATOR}{p['completion_time']}{COMPONENT_SEPARATOR}203"]))

    for container in p.get("containers", []):
        segs.append(_seg("EQD", ["CN", container.get("container_no", "")]))
        weight = container.get("weight_kg")
        if weight:
            segs.append(_seg("MEA", ["AAE", "G", f"KGM{COMPONENT_SEPARATOR}{weight}"]))
        if container.get("seal_no"):
            segs.append(_seg("SEL", [container["seal_no"]]))

    return segs


def _build_codeco(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    fc = FUNCTION_CODE_REVERSE.get(p.get("function_code", "original"), "9")
    segs.append(_seg("BGM", ["281", p.get("document_id", ""), fc]))

    if p.get("event_timestamp"):
        segs.append(_seg("DTM", [f"137{COMPONENT_SEPARATOR}{p['event_timestamp']}{COMPONENT_SEPARATOR}203"]))

    for container in p.get("containers", []):
        segs.append(
            _seg(
                "EQD",
                [
                    "CN",
                    container.get("container_no", ""),
                    container.get("iso_size_type", ""),
                ],
            )
        )
        weight = container.get("weight_kg")
        if weight:
            segs.append(_seg("MEA", ["AAE", "G", f"KGM{COMPONENT_SEPARATOR}{weight}"]))

    return segs


def _build_iftsta(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    fc = FUNCTION_CODE_REVERSE.get(p.get("function_code", "original"), "9")
    segs.append(_seg("BGM", ["77", p.get("document_id", ""), fc]))

    status_code = p.get("status_code", "")
    if not status_code and p.get("tos_status"):
        status_code = TOS_STATUS_TO_SMDG.get(p["tos_status"], "")

    if status_code:
        description = SMDG_STATUS_CODES.get(status_code, "")
        segs.append(_seg("STS", ["", f"{status_code}{COMPONENT_SEPARATOR}{description}"]))

    if p.get("status_time"):
        segs.append(_seg("DTM", [f"178{COMPONENT_SEPARATOR}{p['status_time']}{COMPONENT_SEPARATOR}203"]))

    if p.get("container_no"):
        segs.append(_seg("EQD", ["CN", p["container_no"]]))

    for ref in p.get("references", []):
        segs.append(_seg("RFF", [f"{ref.get('qualifier', 'BN')}{COMPONENT_SEPARATOR}{ref.get('value', '')}"]))

    for text in p.get("free_text", []):
        segs.append(_seg("FTX", ["AAA", "", "", text]))

    return segs


def _build_iftmin(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    fc = FUNCTION_CODE_REVERSE.get(p.get("function_code", "original"), "9")
    segs.append(_seg("BGM", ["335", p.get("document_id", ""), fc]))

    for stage in p.get("transport_stages", []):
        segs.append(_seg("TDT", ["20", stage.get("voyage_no", ""), "2"]))

    for good in p.get("goods", []):
        segs.append(_seg("GID", [str(good.get("package_count", 1)), good.get("description", "")]))

    return segs


def _build_aperak(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    segs.append(_seg("BGM", ["11", p.get("document_id", ""), "9"]))

    if p.get("referenced_interchange_ref"):
        segs.append(_seg("RFF", [f"ACW{COMPONENT_SEPARATOR}{p['referenced_interchange_ref']}"]))
    if p.get("referenced_message_ref"):
        segs.append(_seg("RFF", [f"ACX{COMPONENT_SEPARATOR}{p['referenced_message_ref']}"]))

    response_type = p.get("response_type", "accepted")
    if response_type == "rejected":
        for error in p.get("errors", []):
            segs.append(_seg("ERC", [error.get("error_code", "27")]))
            if error.get("free_text"):
                segs.append(_seg("FTX", ["AAO", "", "", error["free_text"]]))

    return segs


def _build_contrl(p: dict[str, Any]) -> list[str]:
    segs: list[str] = []
    action = "4" if p.get("syntax_status", "ok") == "ok" else "8"
    segs.append(
        _seg(
            "UCI",
            [
                p.get("referenced_interchange_ref", ""),
                p.get("sender_id", ""),
                p.get("receiver_id", ""),
                action,
            ],
        )
    )
    return segs


def _nested(d: dict, path: str, default: Any = "") -> Any:
    """Get a nested value using dot notation."""
    parts = path.split(".")
    current = d
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current

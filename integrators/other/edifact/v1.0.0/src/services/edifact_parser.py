"""Raw EDIFACT parser — converts .edi content (UNB+...UNZ) to structured JSON dict.

Uses pydifact for low-level segment splitting and element parsing.
High-level message logic (COPRAR/CODECO/etc.) uses segment iteration patterns
per SMDG/UNECE message guides.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from pydifact.segmentcollection import Interchange
from pydifact.segments import Segment

from src.services.edifact_segments import (
    DTM_QUALIFIER,
    EQUIPMENT_STATUS_CODES,
    FULL_EMPTY_CODES,
    FUNCTION_CODES,
    LOCATION_QUALIFIER,
    MSG_TYPES,
    PARTY_QUALIFIER,
    TRANSPORT_MODE_CODES,
)

logger = logging.getLogger(__name__)


class EdifactParseError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


def parse_edifact(content: bytes | str) -> dict[str, Any]:
    """Parse raw EDIFACT content into a structured dict.

    Returns dict with keys: msg_type, version, interchange_ref, message_ref,
    sender_id, receiver_id, payload.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    content = content.strip()
    if not content:
        raise EdifactParseError("Empty EDIFACT content")

    try:
        interchange = Interchange.from_str(content)
    except Exception as exc:
        raise EdifactParseError(f"Failed to parse EDIFACT structure: {exc}") from exc

    segments = list(interchange.segments)
    if not segments:
        raise EdifactParseError("No segments found in EDIFACT content")

    envelope = _parse_envelope(segments)
    msg_type = envelope["msg_type"]

    sender_id = str(interchange.sender) if interchange.sender else envelope.get("sender_id", "")
    receiver_id = str(interchange.recipient) if interchange.recipient else envelope.get("receiver_id", "")
    interchange_ref = (
        str(interchange.control_reference) if interchange.control_reference else envelope.get("interchange_ref", "")
    )

    if msg_type not in MSG_TYPES:
        logger.warning("Unknown EDIFACT message type: %s", msg_type)

    payload = _parse_message_body(msg_type, segments)

    return {
        "msg_type": msg_type,
        "version": envelope["version"],
        "interchange_ref": interchange_ref,
        "message_ref": envelope["message_ref"],
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "payload": payload,
    }


def _parse_envelope(segments: list[Segment]) -> dict[str, str]:
    """Extract envelope info from UNB/UNH segments."""
    result = {
        "msg_type": "",
        "version": "",
        "interchange_ref": "",
        "message_ref": "",
        "sender_id": "",
        "receiver_id": "",
    }

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "UNB":
            if len(elements) >= 4:
                result["sender_id"] = _el(elements, 1, 0)
                result["receiver_id"] = _el(elements, 2, 0)
                result["interchange_ref"] = _el(elements, 4)
            version_id = _el(elements, 0, 0)
            if version_id:
                result["version"] = version_id

        elif tag == "UNH":
            result["message_ref"] = _el(elements, 0)
            msg_id = elements[1] if len(elements) > 1 else None
            if isinstance(msg_id, list) and msg_id:
                result["msg_type"] = msg_id[0]
                if len(msg_id) >= 3:
                    result["version"] = msg_id[1] + msg_id[2]
            elif isinstance(msg_id, str):
                result["msg_type"] = msg_id
            break

    return result


def _parse_message_body(msg_type: str, segments: list[Segment]) -> dict[str, Any]:
    """Dispatch to message-specific parser based on msg_type."""
    body_segments = [s for s in segments if s.tag not in ("UNA", "UNB", "UNH", "UNT", "UNZ")]

    parsers = {
        "COPRAR": _parse_coprar_body,
        "COPARN": _parse_coparn_body,
        "COHAOR": _parse_cohaor_body,
        "COARRI": _parse_coarri_body,
        "CODECO": _parse_codeco_body,
        "IFTSTA": _parse_iftsta_body,
        "IFTMIN": _parse_iftmin_body,
        "APERAK": _parse_aperak_body,
        "CONTRL": _parse_contrl_body,
    }

    parser_fn = parsers.get(msg_type, _parse_generic_body)
    return parser_fn(body_segments)


def _parse_coprar_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "function_code": "original",
        "train_no": "",
        "carrier": {},
        "pol": {},
        "pod": {},
        "eta": "",
        "etd": "",
        "wagons": [],
    }

    current_equipment: dict[str, Any] | None = None
    current_wagon: dict[str, Any] | None = None

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)
            fc = _el(elements, 2)
            result["function_code"] = FUNCTION_CODES.get(fc, fc)

        elif tag == "TDT":
            result["train_no"] = _el(elements, 1)
            mode = _el(elements, 2)
            if mode:
                result["transport_mode"] = TRANSPORT_MODE_CODES.get(mode, mode)
            carrier_id = _el(elements, 4, 0) if len(elements) > 4 else ""
            if carrier_id:
                result["carrier"] = {"code": carrier_id}

        elif tag == "DTM":
            _apply_dtm(result, elements)

        elif tag == "LOC":
            _apply_loc(result, elements)

        elif tag == "NAD":
            _apply_nad(result, elements)

        elif tag == "EQD":
            eq_type = _el(elements, 0)
            eq_id = _el(elements, 1)
            if eq_type == "CN":
                current_equipment = {
                    "container_no": eq_id,
                    "iso_size_type": _el(elements, 2, 0) if len(elements) > 2 else "",
                    "weight_kg": 0.0,
                    "is_empty": True,
                    "seal_no": "",
                    "dangerous_goods": [],
                }
                if current_wagon is not None:
                    current_wagon.setdefault("containers", []).append(current_equipment)
            elif eq_type in ("RR", "WG"):
                if current_wagon:
                    result["wagons"].append(current_wagon)
                current_wagon = {
                    "wagon_no": eq_id,
                    "wagon_type": _el(elements, 2) if len(elements) > 2 else "",
                    "sequence_no": len(result["wagons"]) + 1,
                    "containers": [],
                }
                current_equipment = None

        elif tag == "MEA" and current_equipment:
            weight = _el(elements, 2, 1) if len(elements) > 2 else ""
            if weight:
                with contextlib.suppress(ValueError):
                    current_equipment["weight_kg"] = float(weight)

        elif tag == "EQN" and current_equipment:
            fe = _el(elements, 0, 0) if elements else ""
            current_equipment["is_empty"] = FULL_EMPTY_CODES.get(fe, fe) == "empty"

        elif tag == "SEL" and current_equipment:
            current_equipment["seal_no"] = _el(elements, 0)

        elif tag == "FTX" and current_equipment:
            current_equipment.setdefault("free_text", []).append(_el(elements, 3))

        elif tag == "RFF":
            ref_qual = _el(elements, 0, 0)
            ref_val = _el(elements, 0, 1) if isinstance(elements[0], list) and len(elements[0]) > 1 else ""
            if ref_qual == "BN":
                if current_equipment:
                    current_equipment["booking_ref"] = ref_val
                else:
                    result["booking_ref"] = ref_val
            elif ref_qual == "BM" and current_equipment:
                current_equipment["bl_ref"] = ref_val

    if current_wagon:
        result["wagons"].append(current_wagon)

    return result


def _parse_coparn_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "function_code": "original",
        "operation_type": "release",
        "container_no": "",
        "iso_size_type": "",
        "is_empty": True,
        "carrier": {},
        "haulier": {},
        "references": [],
    }

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)
            fc = _el(elements, 2)
            result["function_code"] = FUNCTION_CODES.get(fc, fc)

        elif tag == "EQD":
            result["container_no"] = _el(elements, 1)
            result["iso_size_type"] = _el(elements, 2, 0) if len(elements) > 2 else ""

        elif tag == "DTM":
            _apply_dtm(result, elements)

        elif tag == "LOC":
            _apply_loc(result, elements)

        elif tag == "NAD":
            _apply_nad(result, elements)

        elif tag == "RFF":
            ref_qual = _el(elements, 0, 0)
            ref_val = _el(elements, 0, 1) if isinstance(elements[0], list) and len(elements[0]) > 1 else ""
            result["references"].append({"qualifier": ref_qual, "value": ref_val})

        elif tag == "FTX":
            code = _el(elements, 0)
            if code in ("AAA", "AAC", "ZZZ"):
                result["operation_type"] = _el(elements, 3) or result["operation_type"]

    return result


def _parse_cohaor_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "function_code": "original",
        "operation_code": "load",
        "container_no": "",
        "location_from": {},
        "location_to": {},
        "requested_time": "",
        "priority": 5,
        "special_instructions": [],
    }

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)
            fc = _el(elements, 2)
            result["function_code"] = FUNCTION_CODES.get(fc, fc)

        elif tag == "EQD":
            result["container_no"] = _el(elements, 1)

        elif tag == "DTM":
            _apply_dtm(result, elements)

        elif tag == "LOC":
            qualifier = _el(elements, 0)
            loc_code = _el(elements, 1, 0) if len(elements) > 1 and isinstance(elements[1], list) else _el(elements, 1)
            role = LOCATION_QUALIFIER.get(qualifier, qualifier)
            if "load" in role or "receipt" in role:
                result["location_from"] = {"un_locode": loc_code, "role": role}
            elif "discharge" in role or "delivery" in role:
                result["location_to"] = {"un_locode": loc_code, "role": role}

        elif tag == "FTX":
            result["special_instructions"].append(_el(elements, 3))

    return result


def _parse_coarri_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "function_code": "original",
        "operation_type": "discharge",
        "transport": {},
        "completion_time": "",
        "containers": [],
    }

    current_container: dict[str, Any] | None = None

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)
            fc = _el(elements, 2)
            result["function_code"] = FUNCTION_CODES.get(fc, fc)

        elif tag == "TDT":
            result["transport"] = {
                "voyage_no": _el(elements, 1),
                "mode": TRANSPORT_MODE_CODES.get(_el(elements, 2), _el(elements, 2)),
            }

        elif tag == "DTM":
            _apply_dtm(result, elements)

        elif tag == "EQD":
            if current_container:
                result["containers"].append(current_container)
            current_container = {
                "container_no": _el(elements, 1),
                "status": "completed",
                "weight_kg": None,
                "seal_no": "",
                "damages": [],
            }

        elif tag == "MEA" and current_container:
            weight = _el(elements, 2, 1) if len(elements) > 2 else ""
            if weight:
                with contextlib.suppress(ValueError):
                    current_container["weight_kg"] = float(weight)

        elif tag == "SEL" and current_container:
            current_container["seal_no"] = _el(elements, 0)

        elif tag == "DAM" and current_container:
            current_container["damages"].append({"code": _el(elements, 0), "description": _el(elements, 1)})

    if current_container:
        result["containers"].append(current_container)

    return result


def _parse_codeco_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "function_code": "original",
        "event_type": "gate_in",
        "containers": [],
    }

    current_container: dict[str, Any] | None = None

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)
            fc = _el(elements, 2)
            result["function_code"] = FUNCTION_CODES.get(fc, fc)

        elif tag == "EQD":
            if current_container:
                result["containers"].append(current_container)
            status_code = _el(elements, 3) if len(elements) > 3 else ""
            current_container = {
                "container_no": _el(elements, 1),
                "iso_size_type": _el(elements, 2, 0) if len(elements) > 2 else "",
                "status": EQUIPMENT_STATUS_CODES.get(status_code, status_code),
                "weight_kg": None,
                "seal_no": "",
            }

        elif tag == "DTM":
            _apply_dtm(result, elements)

        elif tag == "LOC":
            _apply_loc(result, elements)

        elif tag == "MEA" and current_container:
            weight = _el(elements, 2, 1) if len(elements) > 2 else ""
            if weight:
                with contextlib.suppress(ValueError):
                    current_container["weight_kg"] = float(weight)

    if current_container:
        result["containers"].append(current_container)

    return result


def _parse_iftsta_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "function_code": "original",
        "status_code": "",
        "status_time": "",
        "container_no": "",
        "transport": {},
        "location": {},
        "references": [],
        "free_text": [],
    }

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)
            fc = _el(elements, 2)
            result["function_code"] = FUNCTION_CODES.get(fc, fc)

        elif tag == "STS":
            result["status_code"] = _el(elements, 1, 0) if len(elements) > 1 else _el(elements, 0)

        elif tag == "DTM":
            _apply_dtm(result, elements)

        elif tag == "EQD":
            result["container_no"] = _el(elements, 1)

        elif tag == "LOC":
            _apply_loc(result, elements)

        elif tag == "TDT":
            result["transport"] = {"voyage_no": _el(elements, 1)}

        elif tag == "RFF":
            ref_qual = _el(elements, 0, 0)
            ref_val = _el(elements, 0, 1) if isinstance(elements[0], list) and len(elements[0]) > 1 else ""
            result["references"].append({"qualifier": ref_qual, "value": ref_val})

        elif tag == "FTX":
            result["free_text"].append(_el(elements, 3))

    return result


def _parse_iftmin_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "function_code": "original",
        "transport_stages": [],
        "goods": [],
    }

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)
            fc = _el(elements, 2)
            result["function_code"] = FUNCTION_CODES.get(fc, fc)

        elif tag == "TDT":
            result["transport_stages"].append(
                {
                    "voyage_no": _el(elements, 1),
                    "mode": TRANSPORT_MODE_CODES.get(_el(elements, 2), _el(elements, 2)),
                }
            )

        elif tag == "DTM":
            _apply_dtm(result, elements)

        elif tag == "LOC":
            _apply_loc(result, elements)

        elif tag == "NAD":
            _apply_nad(result, elements)

        elif tag == "GID":
            result["goods"].append({"package_count": _el(elements, 0), "description": _el(elements, 1)})

    return result


def _parse_aperak_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": "",
        "referenced_message_ref": "",
        "referenced_interchange_ref": "",
        "response_type": "accepted",
        "errors": [],
    }

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "BGM":
            result["document_id"] = _el(elements, 1)

        elif tag == "RFF":
            ref_qual = _el(elements, 0, 0)
            ref_val = _el(elements, 0, 1) if isinstance(elements[0], list) and len(elements[0]) > 1 else ""
            if ref_qual == "ACW":
                result["referenced_interchange_ref"] = ref_val
            elif ref_qual == "ACX":
                result["referenced_message_ref"] = ref_val

        elif tag == "FTX":
            code = _el(elements, 0)
            text = _el(elements, 3)
            if code == "AAO":
                result["response_type"] = "rejected"
            result.setdefault("error_details", []).append({"code": code, "text": text})

        elif tag == "ERC":
            error_code = _el(elements, 0, 0) if isinstance(elements[0], list) else _el(elements, 0)
            result["errors"].append(
                {
                    "error_code": error_code,
                    "segment_position": None,
                    "free_text": "",
                }
            )

    if result["errors"]:
        result["response_type"] = "rejected"

    return result


def _parse_contrl_body(segments: list[Segment]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "syntax_status": "ok",
        "referenced_interchange_ref": "",
        "errors": [],
    }

    for seg in segments:
        tag = seg.tag
        elements = seg.elements

        if tag == "UCI":
            result["referenced_interchange_ref"] = _el(elements, 0)
            action_code = _el(elements, 3) if len(elements) > 3 else ""
            result["syntax_status"] = "ok" if action_code in ("4", "7") else "error"

        elif tag == "UCM":
            msg_ref = _el(elements, 0)
            action_code = _el(elements, 2) if len(elements) > 2 else ""
            result["errors"].append(
                {
                    "message_ref": msg_ref,
                    "action_code": action_code,
                    "status": "ok" if action_code in ("4", "7") else "error",
                }
            )

    if any(e.get("status") == "error" for e in result["errors"]):
        result["syntax_status"] = "error"

    return result


def _parse_generic_body(segments: list[Segment]) -> dict[str, Any]:
    """Fallback parser that returns all segments as raw data."""
    result: dict[str, Any] = {"segments": []}
    for seg in segments:
        result["segments"].append({"tag": seg.tag, "elements": _elements_to_list(seg.elements)})
    return result


# ── Helpers ──


def _el(elements: list, index: int, sub_index: int | None = None) -> str:
    """Safely extract an element value from a segment's element list."""
    if index >= len(elements):
        return ""
    val = elements[index]
    if sub_index is not None:
        if isinstance(val, list) and sub_index < len(val):
            return str(val[sub_index]) if val[sub_index] is not None else ""
        if isinstance(val, str) and sub_index == 0:
            return val
        return ""
    if isinstance(val, list):
        return str(val[0]) if val else ""
    return str(val) if val is not None else ""


def _apply_dtm(result: dict, elements: list) -> None:
    """Apply DTM (Date/Time) segment data to result dict."""
    dtm_data = elements[0] if elements else None
    if isinstance(dtm_data, list) and len(dtm_data) >= 2:
        qualifier = dtm_data[0]
        value = dtm_data[1]
        role = DTM_QUALIFIER.get(qualifier, qualifier)
        if "arrival" in role:
            result["eta"] = str(value) if value else ""
        elif "departure" in role:
            result["etd"] = str(value) if value else ""
        elif "document" in role:
            result["document_date"] = str(value) if value else ""
        else:
            result.setdefault("dates", {})[role] = str(value) if value else ""


def _apply_loc(result: dict, elements: list) -> None:
    """Apply LOC (Location) segment data to result dict."""
    qualifier = _el(elements, 0)
    loc_code = _el(elements, 1, 0) if len(elements) > 1 and isinstance(elements[1], list) else _el(elements, 1)
    role = LOCATION_QUALIFIER.get(qualifier, qualifier)

    if "loading" in role or "receipt" in role:
        result["pol"] = {"un_locode": loc_code, "role": role}
    elif "discharge" in role or "delivery" in role:
        result["pod"] = {"un_locode": loc_code, "role": role}
    elif "terminal" in role:
        result["terminal"] = {"un_locode": loc_code}
    elif "stowage" in role:
        result["stowage_position"] = loc_code


def _apply_nad(result: dict, elements: list) -> None:
    """Apply NAD (Name and Address) segment data to result dict."""
    qualifier = _el(elements, 0)
    party_id = _el(elements, 1, 0) if len(elements) > 1 and isinstance(elements[1], list) else _el(elements, 1)
    role = PARTY_QUALIFIER.get(qualifier, qualifier)

    party = {"code": party_id, "role": role}
    if role == "carrier":
        result["carrier"] = party
    elif role == "consignee":
        result["consignee"] = party
    elif role == "shipper":
        result["shipper"] = party
    elif role == "haulier":
        result["haulier"] = party
    else:
        result.setdefault("parties", []).append(party)


def _elements_to_list(elements: list) -> list:
    """Convert segment elements to serializable list."""
    result = []
    for el in elements:
        if isinstance(el, list):
            result.append([str(x) if x is not None else "" for x in el])
        else:
            result.append(str(el) if el is not None else "")
    return result

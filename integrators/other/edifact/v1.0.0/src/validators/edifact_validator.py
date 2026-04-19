"""Validators for EDIFACT-specific data elements (ISO 6346, UN/LOCODE, IMDG)."""

from __future__ import annotations

import re

_CONTAINER_RE = re.compile(r"^[A-Z]{4}\d{7}$")
_UN_LOCODE_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}$")
_IMO_RE = re.compile(r"^\d{7}$")
_ISO_SIZE_TYPE_RE = re.compile(r"^[0-9A-Z]{4}$")

VALID_IMDG_CLASSES = frozenset(
    {
        "1",
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
        "1.6",
        "2",
        "2.1",
        "2.2",
        "2.3",
        "3",
        "4",
        "4.1",
        "4.2",
        "4.3",
        "5",
        "5.1",
        "5.2",
        "6",
        "6.1",
        "6.2",
        "7",
        "8",
        "9",
    }
)

_OWNER_CODE_WEIGHTS = [
    1,
    2,
    4,
    8,
    16,
    32,
    64,
    128,
    256,
    512,
]

_ALPHA_VALUES: dict[str, int] = {}
_val = 10
for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    _ALPHA_VALUES[ch] = _val
    _val += 1
    if _val % 11 == 0:
        _val += 1


def _compute_check_digit(prefix_and_serial: str) -> int:
    """Compute ISO 6346 check digit for a 10-character container prefix+serial."""
    total = 0
    for i, ch in enumerate(prefix_and_serial):
        value = int(ch) if ch.isdigit() else _ALPHA_VALUES.get(ch, 0)
        total += value * _OWNER_CODE_WEIGHTS[i]
    return total % 11 % 10


def validate_container_number(container_id: str) -> tuple[bool, str]:
    """Validate container number per ISO 6346 / BIC standard.

    Format: 4 alpha (owner code + category) + 6 digits (serial) + 1 check digit.
    Returns (is_valid, error_message).
    """
    container_id = container_id.upper().replace(" ", "").replace("-", "")

    if not _CONTAINER_RE.match(container_id):
        return False, f"Invalid format: expected 4 letters + 7 digits, got '{container_id}'"

    expected_check = _compute_check_digit(container_id[:10])
    actual_check = int(container_id[10])

    if expected_check != actual_check:
        return False, f"Check digit mismatch: expected {expected_check}, got {actual_check}"

    return True, ""


def validate_un_locode(locode: str) -> tuple[bool, str]:
    """Validate UN/LOCODE format (5 chars: 2 country + 3 location)."""
    locode = locode.upper().replace(" ", "")

    if not locode:
        return True, ""

    if not _UN_LOCODE_RE.match(locode):
        return False, f"Invalid UN/LOCODE format: expected 2 alpha + 3 alphanumeric, got '{locode}'"

    return True, ""


def validate_vessel_imo(imo: str) -> tuple[bool, str]:
    """Validate IMO vessel number (7 digits with check digit)."""
    imo = imo.strip()

    if not imo:
        return True, ""

    if imo.upper().startswith("IMO"):
        imo = imo[3:].strip()

    if not _IMO_RE.match(imo):
        return False, f"Invalid IMO number format: expected 7 digits, got '{imo}'"

    digits = [int(d) for d in imo]
    checksum = sum(d * (7 - i) for i, d in enumerate(digits[:6]))
    if checksum % 10 != digits[6]:
        return False, f"IMO check digit mismatch for '{imo}'"

    return True, ""


def validate_iso_size_type(code: str) -> tuple[bool, str]:
    """Validate ISO 6346 container size/type code (4 chars)."""
    code = code.upper().strip()

    if not code:
        return True, ""

    if not _ISO_SIZE_TYPE_RE.match(code):
        return False, f"Invalid ISO size/type code: expected 4 alphanumeric chars, got '{code}'"

    return True, ""


def validate_imdg_class(imdg_class: str) -> tuple[bool, str]:
    """Validate IMDG dangerous goods class."""
    imdg_class = imdg_class.strip()

    if not imdg_class:
        return True, ""

    if imdg_class not in VALID_IMDG_CLASSES:
        return False, f"Invalid IMDG class '{imdg_class}'. Valid: {sorted(VALID_IMDG_CLASSES)}"

    return True, ""

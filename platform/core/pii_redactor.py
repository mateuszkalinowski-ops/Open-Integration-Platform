"""PII Redactor -- GDPR/RODO-compliant data masking for operation logs.

Recursively traverses dicts/lists and redacts personally identifiable
information before returning execution details to the API consumer.
Keys whose names suggest sensitive content are masked; email addresses
and phone numbers found in string values are obfuscated.
"""

import re
from typing import Any

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-]{7,14}\d")

_PII_KEY_PATTERNS: set[str] = {
    "email",
    "e_mail",
    "email_address",
    "mail",
    "recipient",
    "recipients",
    "to",
    "cc",
    "bcc",
    "from",
    "sender",
    "reply_to",
    "name",
    "first_name",
    "last_name",
    "full_name",
    "phone",
    "phone_number",
    "telephone",
    "mobile",
    "address",
    "street",
    "city",
    "zip",
    "zip_code",
    "postal_code",
    "pesel",
    "nip",
    "regon",
    "ssn",
    "id_number",
    "passport",
    "password",
    "secret",
    "token",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "set-cookie",
    "proxy-authorization",
    "x-api-key",
    "x-admin-secret",
    "x-internal-secret",
}

_SAFE_KEYS: set[str] = {
    "imap_host",
    "smtp_host",
    "connector",
    "connector_name",
    "action",
    "event",
    "status",
    "message_id",
    "account_name",
    "node_id",
    "node_type",
    "label",
    "duration_ms",
    "error",
    "type",
    "handle",
    "condition_result",
    "switch_value",
    "matched_case",
    "variable",
    "status_code",
    "_truncated",
    "_preview",
    "dispatched",
}

_REDACTION_MARKER = "[REDACTED-PII]"


def mask_email(email: str) -> str:
    """m***@domain.com"""
    local, _, domain = email.partition("@")
    if not domain:
        return _REDACTION_MARKER
    return f"{local[0]}***@{domain}" if local else f"***@{domain}"


def mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return _REDACTION_MARKER
    return digits[:2] + "*" * (len(digits) - 4) + digits[-2:]


_PII_SEGMENT_PATTERNS: set[str] = {
    "email",
    "phone",
    "name",
    "address",
    "pesel",
    "password",
    "secret",
    "token",
}


def _is_pii_key(key: str) -> bool:
    normalized = key.lower().strip()
    if normalized in _SAFE_KEYS:
        return False
    if normalized in _PII_KEY_PATTERNS:
        return True
    segments = set(normalized.replace("-", "_").split("_"))
    return bool(segments & _PII_SEGMENT_PATTERNS)


def _redact_string_value(value: str) -> str:
    """Mask emails and phones found inside an arbitrary string."""
    result = value
    for match in _EMAIL_RE.finditer(value):
        result = result.replace(match.group(), mask_email(match.group()))
    for match in _PHONE_RE.finditer(result):
        result = result.replace(match.group(), mask_phone(match.group()))
    return result


def redact(data: Any, *, depth: int = 0) -> Any:
    """Recursively redact PII from a data structure.

    - Dict keys matching PII patterns have their values masked.
    - String values are scanned for inline emails / phone numbers.
    - Recursion is capped at depth 20 to avoid pathological inputs.
    """
    if depth > 20:
        return _REDACTION_MARKER

    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for key, value in data.items():
            if _is_pii_key(key):
                if isinstance(value, str):
                    emails = _EMAIL_RE.findall(value)
                    if emails:
                        masked = value
                        for email in emails:
                            masked = masked.replace(email, mask_email(email))
                        out[key] = masked
                    elif _PHONE_RE.fullmatch(value.strip()):
                        out[key] = mask_phone(value)
                    else:
                        out[key] = _REDACTION_MARKER
                elif isinstance(value, list):
                    out[key] = [
                        mask_email(v) if isinstance(v, str) and _EMAIL_RE.fullmatch(v) else _REDACTION_MARKER
                        for v in value
                    ]
                else:
                    out[key] = _REDACTION_MARKER
                out[f"__{key}_redacted"] = True
            else:
                out[key] = redact(value, depth=depth + 1)
        return out

    if isinstance(data, list):
        return [redact(item, depth=depth + 1) for item in data]

    if isinstance(data, str):
        return _redact_string_value(data)

    return data


def redact_execution_detail(
    execution_data: dict[str, Any],
    *,
    include_raw: bool = False,
) -> dict[str, Any]:
    """Redact an entire execution record for API output.

    Adds a ``_gdpr`` metadata block so the consumer knows data was sanitised.
    """
    redacted = redact(execution_data)
    redacted["_gdpr"] = {
        "redacted": True,
        "policy": "RODO/GDPR — personally identifiable information has been masked",
        "include_raw": include_raw,
    }
    return redacted

"""Validators for REST API Gateway requests."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
_HEADER_NAME_RE = re.compile(r"^[a-zA-Z0-9\-_]+$")

VALID_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})


def validate_url(url: str) -> tuple[bool, str]:
    """Validate that a string is a well-formed HTTP(S) URL."""
    if not url:
        return False, "URL is required"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid scheme '{parsed.scheme}', expected http or https"
    if not parsed.netloc:
        return False, "URL must include a host"

    return True, ""


def validate_http_method(method: str) -> tuple[bool, str]:
    """Validate HTTP method."""
    upper = method.upper()
    if upper not in VALID_METHODS:
        return False, f"Invalid HTTP method '{method}'. Valid: {sorted(VALID_METHODS)}"
    return True, ""


def validate_header_name(name: str) -> tuple[bool, str]:
    """Validate that a header name contains only allowed characters."""
    if not _HEADER_NAME_RE.match(name):
        return False, f"Invalid header name '{name}': only alphanumeric, dash, underscore allowed"
    return True, ""


def validate_timeout(timeout_s: int | float) -> tuple[bool, str]:
    """Validate timeout value."""
    if timeout_s <= 0:
        return False, "Timeout must be positive"
    if timeout_s > 300:
        return False, "Timeout exceeds maximum (300s)"
    return True, ""

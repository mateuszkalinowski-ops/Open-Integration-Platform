"""Structured JSON logging with PII redaction."""

import logging
import json
import sys
import re
from datetime import datetime, timezone


SENSITIVE_PATTERNS = [
    re.compile(r"(password|token|secret|key|authorization|credential)", re.IGNORECASE),
]


def obfuscate(value: str, visible_chars: int = 4) -> str:
    """Obfuscate a sensitive value, keeping only the last N characters visible."""
    if len(value) <= visible_chars:
        return "***"
    return "***" + value[-visible_chars:]


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str = "integrator"):
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self._service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
            log_entry["exception_type"] = type(record.exc_info[1]).__name__
        return json.dumps(log_entry, default=str)


def setup_logging(service_name: str, level: str = "INFO") -> None:
    """Configure structured JSON logging for the service."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service_name=service_name))
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

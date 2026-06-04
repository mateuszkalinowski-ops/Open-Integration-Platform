"""Response parser — interprets target system responses per profile/mapping."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar

import yaml

from src.schemas.account import AccountConfig, ResponseMappingConfig
from src.schemas.common import RestCallResponse

logger = logging.getLogger(__name__)


class ResponseParser:
    """Parses HTTP responses according to account's response mapping or profile."""

    _profiles: ClassVar[dict[str, ResponseMappingConfig]] = {}

    @classmethod
    def load_profiles(cls, profiles_dir: str) -> None:
        profiles_path = Path(profiles_dir)
        if not profiles_path.exists():
            logger.warning("Profiles directory not found: %s", profiles_dir)
            return

        for profile_file in profiles_path.glob("*.yaml"):
            try:
                with open(profile_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "name" in data:
                    cls._profiles[data["name"]] = ResponseMappingConfig(
                        use_http_status=data.get("use_http_status", False),
                        status_field=data.get("status_field", ""),
                        status_ok_values=data.get("status_ok_values", ["OK"]),
                        status_error_values=data.get("status_error_values", ["ERROR"]),
                        message_field=data.get("message_field", ""),
                        data_field=data.get("data_field"),
                        error_code_field=data.get("error_code_field", ""),
                    )
                    logger.info("Loaded response profile: %s", data["name"])
            except Exception:
                logger.warning("Failed to load profile %s", profile_file, exc_info=True)

    def __init__(self, account: AccountConfig) -> None:
        self._account = account
        self._mapping = self._resolve_mapping()

    def _resolve_mapping(self) -> ResponseMappingConfig:
        if self._account.response_mapping.status_field or self._account.response_mapping.use_http_status:
            return self._account.response_mapping

        profile_name = self._account.profile
        if profile_name and profile_name != "auto" and profile_name in self._profiles:
            return self._profiles[profile_name]

        return ResponseMappingConfig(use_http_status=True)

    def parse(
        self,
        http_status: int,
        response_body: Any,
        elapsed_ms: int,
        endpoint: str,
    ) -> RestCallResponse:
        mapping = self._mapping

        if mapping.use_http_status:
            return RestCallResponse(
                status="success" if 200 <= http_status < 400 else "error",
                http_status=http_status,
                data=response_body,
                raw_response=response_body,
                elapsed_ms=elapsed_ms,
                account=self._account.name,
                endpoint=endpoint,
            )

        response_status = _get_nested(response_body, mapping.status_field, "")
        message = _get_nested(response_body, mapping.message_field, "")
        data = _get_nested(response_body, mapping.data_field, response_body) if mapping.data_field else response_body

        is_ok = str(response_status) in mapping.status_ok_values
        status = "success" if is_ok else "error"

        return RestCallResponse(
            status=status,
            http_status=http_status,
            response_status=str(response_status),
            message=str(message) if message else "",
            data=data,
            raw_response=response_body,
            elapsed_ms=elapsed_ms,
            account=self._account.name,
            endpoint=endpoint,
        )

    def auto_detect_profile(self, response_body: Any) -> str | None:
        """Try to auto-detect the response profile from a sample response."""
        if not isinstance(response_body, dict):
            return "generic"

        if "status" in response_body and response_body.get("status") in ("OK", "ERROR") and "message" in response_body:
            return "pinquark"

        if "d" in response_body and isinstance(response_body.get("d"), dict):
            return "sap"

        return "generic"


def _get_nested(obj: Any, path: str, default: Any = None) -> Any:
    """Get a nested value from a dict using dot notation."""
    if not path or not isinstance(obj, dict):
        return default

    parts = path.split(".")
    current = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current

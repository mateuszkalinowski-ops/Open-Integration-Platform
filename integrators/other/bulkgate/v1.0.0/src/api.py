"""BulkGate SMS Gateway — HTTP API client.

Implements BulkGate Simple API v1.0 and Advanced API v2.0.
All calls use httpx (async).

API base: https://portal.bulkgate.com
- Simple transactional: POST /api/1.0/simple/transactional
- Simple promotional:   POST /api/1.0/simple/promotional
- Advanced transactional: POST /api/2.0/advanced/transactional
- Credit balance:       POST /api/2.0/advanced/info
"""

from __future__ import annotations

import functools
import logging
from typing import Any

import httpx

from src.config import settings
from src.schemas import (
    BulkGateCredentials,
    ChannelCascade,
    SenderIdType,
)

logger = logging.getLogger("automation-bulkgate")

CONNECT_TIMEOUT = settings.rest_timeout
READ_TIMEOUT = 60


def handle_errors(func):
    """Decorator: standardize error handling for BulkGate API calls."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> tuple[dict[str, Any], int]:
        try:
            return await func(*args, **kwargs)
        except httpx.TimeoutException:
            logger.error("BulkGate API timeout in %s", func.__name__)
            return {"error": {"code": "TIMEOUT", "message": "BulkGate API request timed out"}}, 504
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            try:
                body = exc.response.json()
            except Exception:
                body = {"error": exc.response.text}
            logger.error("BulkGate API error %d in %s: %s", status, func.__name__, body)
            return body, status
        except Exception as exc:
            logger.exception("Unexpected error in %s", func.__name__)
            return {"error": {"code": "INTERNAL_ERROR", "message": str(exc)}}, 500

    return wrapper


class BulkGateApiClient:
    """Async client for BulkGate HTTP SMS APIs."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=READ_TIMEOUT, pool=READ_TIMEOUT),
        )

    async def close(self) -> None:
        await self._client.aclose()

    def _base_payload(self, credentials: BulkGateCredentials) -> dict[str, Any]:
        return {
            "application_id": credentials.application_id,
            "application_token": credentials.application_token,
        }

    @handle_errors
    async def send_transactional_sms(
        self,
        credentials: BulkGateCredentials,
        number: str,
        text: str,
        *,
        unicode: bool = False,
        sender_id: SenderIdType = SenderIdType.SYSTEM,
        sender_id_value: str | None = None,
        country: str | None = None,
        schedule: str | None = None,
        duplicates_check: bool = False,
        tag: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        payload = self._base_payload(credentials)
        payload["number"] = number
        payload["text"] = text
        payload["unicode"] = unicode
        payload["sender_id"] = sender_id.value
        if sender_id_value is not None:
            payload["sender_id_value"] = sender_id_value
        if country is not None:
            payload["country"] = country
        if schedule is not None:
            payload["schedule"] = schedule
        payload["duplicates_check"] = "on" if duplicates_check else "off"
        if tag is not None:
            payload["tag"] = tag

        response = await self._client.post(
            settings.simple_transactional_url,
            json=payload,
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def send_promotional_sms(
        self,
        credentials: BulkGateCredentials,
        number: str,
        text: str,
        *,
        unicode: bool = False,
        sender_id: SenderIdType = SenderIdType.SYSTEM,
        sender_id_value: str | None = None,
        country: str | None = None,
        schedule: str | None = None,
        duplicates_check: bool = False,
        tag: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        payload = self._base_payload(credentials)
        payload["number"] = number
        payload["text"] = text
        payload["unicode"] = unicode
        payload["sender_id"] = sender_id.value
        if sender_id_value is not None:
            payload["sender_id_value"] = sender_id_value
        if country is not None:
            payload["country"] = country
        if schedule is not None:
            payload["schedule"] = schedule
        payload["duplicates_check"] = "on" if duplicates_check else "off"
        if tag is not None:
            payload["tag"] = tag

        response = await self._client.post(
            settings.simple_promotional_url,
            json=payload,
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def send_advanced_transactional(
        self,
        credentials: BulkGateCredentials,
        number: list[str],
        text: str,
        *,
        variables: dict[str, str] | None = None,
        channel: ChannelCascade | None = None,
        country: str | None = None,
        schedule: str | None = None,
        duplicates_check: bool = False,
        tag: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        payload = self._base_payload(credentials)
        payload["number"] = number
        payload["text"] = text
        if variables:
            payload["variables"] = variables
        if channel:
            channel_dict: dict[str, Any] = {}
            if channel.sms:
                sms_obj: dict[str, Any] = {"sender_id": channel.sms.sender_id.value, "unicode": channel.sms.unicode}
                if channel.sms.text:
                    sms_obj["text"] = channel.sms.text
                if channel.sms.sender_id_value:
                    sms_obj["sender_id_value"] = channel.sms.sender_id_value
                channel_dict["sms"] = sms_obj
            if channel.viber:
                viber_obj: dict[str, Any] = {"sender": channel.viber.sender, "expiration": channel.viber.expiration}
                if channel.viber.text:
                    viber_obj["text"] = channel.viber.text
                channel_dict["viber"] = viber_obj
            payload["channel"] = channel_dict
        if country is not None:
            payload["country"] = country
        if schedule is not None:
            payload["schedule"] = schedule
        payload["duplicates_check"] = "on" if duplicates_check else "off"
        if tag is not None:
            payload["tag"] = tag

        response = await self._client.post(
            settings.advanced_transactional_url,
            json=payload,
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def check_credit_balance(
        self,
        credentials: BulkGateCredentials,
    ) -> tuple[dict[str, Any], int]:
        payload = self._base_payload(credentials)
        response = await self._client.post(
            settings.credit_balance_url,
            json=payload,
        )
        response.raise_for_status()
        return response.json(), response.status_code

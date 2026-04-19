"""Generic async REST client with auth, retry, and response parsing."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

import httpx

from src.schemas.account import AccountConfig
from src.schemas.common import RestCallResponse
from src.services.auth_provider import AuthProvider, AuthProviderError
from src.services.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class RestClientError(Exception):
    def __init__(self, status_code: int, message: str, details: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class RestClient:
    """Generic async HTTP client with auth, retry, and response parsing."""

    def __init__(
        self,
        account: AccountConfig,
        auth_provider: AuthProvider,
        response_parser: ResponseParser,
    ) -> None:
        self.account = account
        self.auth_provider = auth_provider
        self.response_parser = response_parser
        self._client: httpx.AsyncClient | None = None

    async def call(
        self,
        endpoint: str,
        method: str = "",
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        timeout_s: int | None = None,
    ) -> RestCallResponse:
        """Execute a REST request with auth, retry, and response parsing."""
        resolved_method = method or self.account.default_method
        url = self._build_url(endpoint)

        auth_headers = await self.auth_provider.get_headers()
        auth_query = self.auth_provider.get_query_params()

        merged_headers = {
            "Content-Type": self.account.default_content_type,
            **auth_headers,
            **(headers or {}),
        }
        merged_params = {**auth_query, **(query_params or {})}
        effective_timeout = timeout_s or self.account.timeouts.read_s

        start = time.monotonic()
        http_status, response_body = await self._request_with_retry(
            method=resolved_method,
            url=url,
            json_body=body,
            headers=merged_headers,
            params=merged_params if merged_params else None,
            timeout=effective_timeout,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        return self.response_parser.parse(
            http_status=http_status,
            response_body=response_body,
            elapsed_ms=elapsed_ms,
            endpoint=endpoint,
        )

    async def call_named(
        self,
        named_action: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        timeout_s: int | None = None,
    ) -> RestCallResponse:
        """Resolve a named action from action_registry and call it."""
        action_def = self.account.action_registry.get(named_action)
        if not action_def:
            raise RestClientError(
                status_code=400,
                message=f"Unknown action '{named_action}' in account '{self.account.name}'",
                details={"available_actions": list(self.account.action_registry.keys())},
            )
        return await self.call(
            endpoint=action_def.endpoint,
            method=action_def.method or "",
            body=body,
            headers=headers,
            query_params=query_params,
            timeout_s=timeout_s,
        )

    async def check_health(self) -> dict[str, Any]:
        try:
            client = await self._get_client()
            auth_headers = await self.auth_provider.get_headers()
            start = time.monotonic()
            response = await client.get(
                self._build_url(""),
                headers=auth_headers,
                timeout=10.0,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return {
                "status": "healthy" if response.status_code < 500 else "unhealthy",
                "http_status": response.status_code,
                "elapsed_ms": elapsed_ms,
            }
        except AuthProviderError as exc:
            return {"status": "unhealthy", "error": f"Auth error: {exc.message}"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    def _build_url(self, endpoint: str) -> str:
        base = self.account.base_url.rstrip("/")
        prefix = self.account.path_prefix.rstrip("/") if self.account.path_prefix else ""
        if not endpoint:
            return f"{base}{prefix}" if prefix else base
        endpoint = endpoint.lstrip("/")
        return f"{base}{prefix}/{endpoint}"

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None,
        headers: dict[str, str],
        params: dict[str, str] | None,
        timeout: float,
    ) -> tuple[int, Any]:
        client = await self._get_client()
        retry_cfg = self.account.retry
        last_exc: Exception | None = None

        for attempt in range(1, retry_cfg.max_attempts + 1):
            try:
                response = await client.request(
                    method,
                    url,
                    json=json_body,
                    headers=headers,
                    params=params,
                    timeout=timeout,
                )

                if response.status_code in retry_cfg.retryable_status_codes and attempt < retry_cfg.max_attempts:
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    logger.warning(
                        "Attempt %d/%d retryable status %d for %s %s",
                        attempt,
                        retry_cfg.max_attempts,
                        response.status_code,
                        method,
                        url,
                    )
                else:
                    try:
                        body = response.json()
                    except Exception:
                        body = {"raw_text": response.text[:2000]}
                    return response.status_code, body

            except httpx.RequestError as exc:
                last_exc = exc
                logger.warning(
                    "Attempt %d/%d connection error for %s %s: %s",
                    attempt,
                    retry_cfg.max_attempts,
                    method,
                    url,
                    exc,
                )

            if attempt < retry_cfg.max_attempts:
                jitter = random.uniform(0, 0.5)
                backoff = min(
                    retry_cfg.backoff_initial_s * (retry_cfg.backoff_multiplier ** (attempt - 1)) + jitter,
                    60.0,
                )
                await asyncio.sleep(backoff)

        raise RestClientError(
            status_code=502,
            message=f"All {retry_cfg.max_attempts} attempts failed for {method} {url}",
            details={"last_error": str(last_exc)},
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.account.timeouts.connect_s,
                    read=self.account.timeouts.read_s,
                    write=self.account.timeouts.read_s,
                    pool=self.account.timeouts.connect_s,
                ),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        await self.auth_provider.close()

"""FastAPI routes for REST API Gateway connector."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from src.api.dependencies import app_state
from src.schemas.account import ActionDefinition, DiscoveryInfo
from src.schemas.common import (
    BatchCallItem,
    BatchResultItem,
    HealthResponse,
    RestBatchRequest,
    RestBatchResponse,
    RestCallRequest,
    RestCallResponse,
    RestDiscoverRequest,
    RestDiscoverResponse,
    RestPollRequest,
    RestPollResponse,
)
from src.services.rest_client import RestClient, RestClientError

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_client(account_name: str) -> RestClient:
    try:
        return app_state.account_manager.get_client(account_name)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found") from err


def _client_error_to_http(exc: RestClientError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"error": exc.message, "details": exc.details},
    )


# ── Health & readiness ──


@router.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "rest-api-connector",
        "version": "1.0.0",
    }


@router.get("/readiness")
async def readiness() -> dict:
    accounts = app_state.account_manager.list_accounts()
    return {
        "status": "ready",
        "accounts_count": len(accounts),
    }


# ── Account management ──


@router.get("/accounts")
async def list_accounts() -> list[dict]:
    return app_state.account_manager.list_accounts()


@router.get("/accounts/{account_name}")
async def get_account(account_name: str) -> dict:
    try:
        account = app_state.account_manager.get_account(account_name)
        return {
            "name": account.name,
            "description": account.description,
            "base_url": account.base_url,
            "path_prefix": account.path_prefix,
            "profile": account.profile,
            "auth_type": account.auth.type.value,
            "actions_count": len(account.action_registry),
        }
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@router.get("/accounts/{account_name}/actions")
async def list_account_actions(account_name: str) -> dict:
    try:
        return app_state.account_manager.get_account_actions(account_name)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


# ── REST Call ──


@router.post("/rest/call", response_model=RestCallResponse)
async def rest_call(request: RestCallRequest) -> RestCallResponse:
    client = _get_client(request.account)
    try:
        if request.named_action:
            return await client.call_named(
                named_action=request.named_action,
                body=request.body,
                headers=request.headers or None,
                query_params=request.query_params or None,
                timeout_s=request.timeout_s,
            )
        if request.endpoint:
            return await client.call(
                endpoint=request.endpoint,
                method=request.method,
                body=request.body,
                headers=request.headers or None,
                query_params=request.query_params or None,
                timeout_s=request.timeout_s,
            )
        raise HTTPException(
            status_code=400,
            detail="Either 'endpoint' or 'named_action' must be provided",
        )
    except RestClientError as exc:
        raise _client_error_to_http(exc) from exc


# ── REST Poll ──


@router.post("/rest/poll", response_model=RestPollResponse)
async def rest_poll(request: RestPollRequest) -> RestPollResponse:
    client = _get_client(request.account)

    body = {request.cursor_field: request.cursor_value, "limit": request.limit}
    try:
        if request.named_action:
            response = await client.call_named(
                named_action=request.named_action,
                body=body,
            )
        elif request.endpoint:
            response = await client.call(
                endpoint=request.endpoint,
                method=request.method,
                body=body,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'endpoint' or 'named_action' must be provided",
            )
    except RestClientError as exc:
        raise _client_error_to_http(exc) from exc

    raw = response.raw_response if isinstance(response.raw_response, dict) else {}
    items = _get_nested(raw, request.items_field, [])
    cursor_value = _get_nested(raw, request.cursor_response_field)

    return RestPollResponse(
        status=response.status,
        items=items if isinstance(items, list) else [],
        cursor_value=cursor_value,
        count=len(items) if isinstance(items, list) else 0,
        http_status=response.http_status,
        elapsed_ms=response.elapsed_ms,
        account=request.account,
        endpoint=request.endpoint or request.named_action,
    )


# ── REST Batch ──


@router.post("/rest/batch", response_model=RestBatchResponse)
async def rest_batch(request: RestBatchRequest) -> RestBatchResponse:
    client = _get_client(request.account)
    start = time.monotonic()

    if request.parallel:
        results = await _batch_parallel(client, request.calls, request.stop_on_error)
    else:
        results = await _batch_sequential(client, request.calls, request.stop_on_error)

    elapsed_ms = int((time.monotonic() - start) * 1000)
    succeeded = sum(1 for r in results if r.status == "success")
    failed = len(results) - succeeded

    return RestBatchResponse(
        status="success" if failed == 0 else "partial",
        results=results,
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        elapsed_ms=elapsed_ms,
    )


async def _batch_sequential(
    client: RestClient,
    calls: list[BatchCallItem],
    stop_on_error: bool,
) -> list[BatchResultItem]:
    results: list[BatchResultItem] = []
    for i, call_item in enumerate(calls):
        result = await _execute_batch_item(client, call_item, i)
        results.append(result)
        if result.status == "error" and stop_on_error:
            break
    return results


async def _batch_parallel(
    client: RestClient,
    calls: list[BatchCallItem],
    stop_on_error: bool,
) -> list[BatchResultItem]:
    tasks = [_execute_batch_item(client, call_item, i) for i, call_item in enumerate(calls)]
    return list(await asyncio.gather(*tasks))


async def _execute_batch_item(
    client: RestClient,
    call_item: BatchCallItem,
    index: int,
) -> BatchResultItem:
    try:
        if call_item.named_action:
            response = await client.call_named(
                named_action=call_item.named_action,
                body=call_item.body,
            )
        else:
            response = await client.call(
                endpoint=call_item.endpoint,
                method=call_item.method,
                body=call_item.body,
            )
        return BatchResultItem(
            index=index,
            status=response.status,
            http_status=response.http_status,
            data=response.data,
            endpoint=call_item.endpoint or call_item.named_action,
            elapsed_ms=response.elapsed_ms,
        )
    except RestClientError as exc:
        return BatchResultItem(
            index=index,
            status="error",
            http_status=exc.status_code,
            error=exc.message,
            endpoint=call_item.endpoint or call_item.named_action,
        )


# ── REST Discover ──


@router.post("/rest/discover", response_model=RestDiscoverResponse)
async def rest_discover(request: RestDiscoverRequest) -> RestDiscoverResponse:
    try:
        account = app_state.account_manager.get_account(request.account)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err

    from src.services.auth_provider import AuthProvider

    auth_provider = AuthProvider(account)
    try:
        auth_headers = await auth_provider.get_headers()
    finally:
        await auth_provider.close()

    result = await app_state.discovery.discover(
        base_url=account.base_url,
        path_prefix=account.path_prefix,
        auth_headers=auth_headers,
        openapi_url=request.openapi_url,
        generate_aliases=request.generate_aliases,
    )

    if result.found:
        actions: dict[str, ActionDefinition] = {}
        for ep in result.endpoints:
            alias = ep.alias or ep.endpoint
            actions[alias] = ActionDefinition(
                endpoint=ep.endpoint,
                method=ep.method,
                description=ep.description,
                input_schema=ep.input_schema,
                output_schema=ep.output_schema,
                source="openapi_discovery",
            )
        app_state.account_manager.update_action_registry(request.account, actions)

        account.discovery = DiscoveryInfo(
            openapi_url=result.openapi_url,
            last_discovered_at=_now_iso(),
            endpoints_count=result.count,
            openapi_version=result.openapi_version,
        )

    return result


# ── REST Health Check ──


@router.get("/rest/health/{account_name}", response_model=HealthResponse)
async def rest_health(account_name: str) -> HealthResponse:
    client = _get_client(account_name)
    result = await client.check_health()
    account = app_state.account_manager.get_account(account_name)

    return HealthResponse(
        status=result.get("status", "unknown"),
        account=account_name,
        base_url=account.base_url,
        http_status=result.get("http_status"),
        elapsed_ms=result.get("elapsed_ms", 0),
        error=result.get("error", ""),
    )


# ── Validate connection ──


@router.post("/validate-connection/{account_name}")
async def validate_connection(account_name: str) -> dict:
    client = _get_client(account_name)
    health_result = await client.check_health()

    discovery_result = None
    if health_result.get("status") != "unhealthy":
        try:
            account = app_state.account_manager.get_account(account_name)
            from src.services.auth_provider import AuthProvider

            auth_provider = AuthProvider(account)
            try:
                auth_headers = await auth_provider.get_headers()
            finally:
                await auth_provider.close()

            discovery_result = await app_state.discovery.discover(
                base_url=account.base_url,
                path_prefix=account.path_prefix,
                auth_headers=auth_headers,
            )
        except Exception:
            logger.debug("Discovery failed during validation", exc_info=True)

    return {
        "connection": health_result,
        "discovery": {
            "found": discovery_result.found if discovery_result else False,
            "endpoints_count": discovery_result.count if discovery_result else 0,
            "openapi_version": discovery_result.openapi_version if discovery_result else "",
        },
    }


# ── Helpers ──


def _get_nested(obj: dict, path: str, default=None):
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


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()

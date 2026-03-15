"""Flow Engine -- executes any-to-any integration flows.

A flow connects a source connector event to a destination connector action,
with field mapping and optional transformation in between.
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import structlog
from db.models import Flow, FlowExecution
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.mapping_resolver import MappingResolver

logger = structlog.get_logger()

_RETRY_BASE_DELAY = 1.0
_RETRY_MAX_DELAY = 30.0


class FlowEngine:
    def __init__(self, mapping_resolver: MappingResolver) -> None:
        self._mapping_resolver = mapping_resolver

    async def get_flows_for_event(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        event: str,
    ) -> list[Flow]:
        result = await db.execute(
            select(Flow).where(
                Flow.tenant_id == tenant_id,
                Flow.source_connector == connector_name,
                Flow.source_event == event,
                Flow.is_enabled.is_(True),
            )
        )
        return list(result.scalars().all())

    async def execute_flow(
        self,
        db: AsyncSession,
        flow: Flow,
        event_data: dict[str, Any],
        execute_action_fn: "Callable[..., Any]",
    ) -> FlowExecution:
        start_time = time.monotonic()

        execution = FlowExecution(
            flow_id=flow.id,
            tenant_id=flow.tenant_id,
            status="running",
            source_event_data=event_data,
        )
        db.add(execution)
        await db.flush()

        try:
            if not self._matches_filter(event_data, flow.source_filter):
                execution.status = "skipped"
                execution.completed_at = datetime.now(UTC)
                execution.duration_ms = int((time.monotonic() - start_time) * 1000)
                await db.flush()
                return execution

            mapped_data = await self._mapping_resolver.resolve(
                db=db,
                tenant_id=flow.tenant_id,
                connector_name=flow.destination_connector,
                mapping_type="field",
                source_data=event_data,
                flow_field_mapping=flow.field_mapping,
            )

            if flow.transform:
                mapped_data = self._apply_transform(mapped_data, flow.transform)

            execution.destination_action_data = mapped_data

            max_attempts = flow.max_retries + 1 if flow.on_error == "retry" else 1
            last_exc: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    result = await execute_action_fn(
                        connector_name=flow.destination_connector,
                        action=flow.destination_action,
                        payload=mapped_data,
                        tenant_id=flow.tenant_id,
                        connector_version=getattr(flow, "destination_connector_version", None),
                    )

                    execution.status = "success"
                    execution.retry_count = attempt
                    execution.result = result if isinstance(result, dict) else {"result": str(result)}
                    execution.completed_at = datetime.now(UTC)
                    execution.duration_ms = int((time.monotonic() - start_time) * 1000)

                    await logger.ainfo(
                        "flow_executed",
                        flow_id=str(flow.id),
                        flow_name=flow.name,
                        status="success",
                        attempt=attempt + 1,
                        duration_ms=execution.duration_ms,
                    )
                    last_exc = None
                    break
                except Exception as exc:
                    last_exc = exc
                    execution.retry_count = attempt
                    if attempt < max_attempts - 1:
                        delay = min(_RETRY_BASE_DELAY * (2**attempt), _RETRY_MAX_DELAY)
                        await logger.awarning(
                            "flow_action_retry",
                            flow_id=str(flow.id),
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            delay=delay,
                            error=str(exc),
                        )
                        await asyncio.sleep(delay)

            if last_exc is not None:
                raise last_exc

        except Exception as exc:
            execution.status = "failed"
            execution.error = str(exc)
            execution.completed_at = datetime.now(UTC)
            execution.duration_ms = int((time.monotonic() - start_time) * 1000)

            await logger.aerror(
                "flow_execution_failed",
                flow_id=str(flow.id),
                flow_name=flow.name,
                error=str(exc),
                retries=execution.retry_count,
                duration_ms=execution.duration_ms,
            )

        await db.flush()
        return execution

    async def process_event(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        event: str,
        event_data: dict[str, Any],
        execute_action_fn: "Callable[..., Any]",
    ) -> list[FlowExecution]:
        flows = await self.get_flows_for_event(db, tenant_id, connector_name, event)
        executions = []

        for flow in flows:
            execution = await self.execute_flow(db, flow, event_data, execute_action_fn)
            executions.append(execution)

        return executions

    def _matches_filter(self, event_data: dict[str, Any], source_filter: dict | None) -> bool:
        if not source_filter:
            return True

        for key, expected_value in source_filter.items():
            actual_value = self._get_nested(event_data, key)
            if actual_value != expected_value:
                return False
        return True

    def _get_nested(self, data: dict, key: str) -> Any:
        parts = key.split(".")
        current: Any = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    @staticmethod
    def _apply_transform(data: dict[str, Any], transform: str) -> dict[str, Any]:
        """Apply a JMESPath transform expression to mapped data."""
        try:
            import jmespath

            result = jmespath.search(transform, data)
            if isinstance(result, dict):
                return result
            return {"result": result}
        except ImportError:
            logger.warning("jmespath not installed — skipping flow transform")
            return data
        except Exception as exc:
            logger.warning("flow_transform_failed", transform=transform, error=str(exc))
            return data

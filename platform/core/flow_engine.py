"""Flow Engine -- executes any-to-any integration flows.

A flow connects a source connector event to a destination connector action,
with field mapping and optional transformation in between.
"""

import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.mapping_resolver import MappingResolver
from db.models import Flow, FlowExecution

logger = structlog.get_logger()


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
                execution.completed_at = datetime.now(timezone.utc)
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
            execution.destination_action_data = mapped_data

            result = await execute_action_fn(
                connector_name=flow.destination_connector,
                action=flow.destination_action,
                payload=mapped_data,
                tenant_id=flow.tenant_id,
            )

            execution.status = "success"
            execution.result = result if isinstance(result, dict) else {"result": str(result)}
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_ms = int((time.monotonic() - start_time) * 1000)

            await logger.ainfo(
                "flow_executed",
                flow_id=str(flow.id),
                flow_name=flow.name,
                status="success",
                duration_ms=execution.duration_ms,
            )

        except Exception as exc:
            execution.status = "failed"
            execution.error = str(exc)
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_ms = int((time.monotonic() - start_time) * 1000)

            await logger.aerror(
                "flow_execution_failed",
                flow_id=str(flow.id),
                flow_name=flow.name,
                error=str(exc),
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

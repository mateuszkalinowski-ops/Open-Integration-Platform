"""Audit trail — records entity mutations and manages workflow versioning.

Captures before/after state on create, update, and delete operations.
Automatically snapshots workflow nodes/edges/variables on every update.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AuditLog, Workflow, WorkflowVersion

logger = structlog.get_logger(__name__)


async def record_audit(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    user_id: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Write a single audit log entry."""
    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry


async def snapshot_workflow_version(
    db: AsyncSession,
    workflow: Workflow,
    *,
    created_by: str | None = None,
) -> WorkflowVersion:
    """Create a versioned snapshot of the current workflow state."""
    await db.execute(
        select(Workflow.id)
        .where(Workflow.id == workflow.id)
        .with_for_update()
    )
    result = await db.execute(
        select(func.coalesce(func.max(WorkflowVersion.version), 0))
        .where(WorkflowVersion.workflow_id == workflow.id)
    )
    max_version = result.scalar() or 0

    version = WorkflowVersion(
        tenant_id=workflow.tenant_id,
        workflow_id=workflow.id,
        version=max_version + 1,
        nodes=workflow.nodes or [],
        edges=workflow.edges or [],
        variables=workflow.variables or {},
        created_by=created_by,
    )
    db.add(version)
    await db.flush()

    workflow.version = version.version
    await db.flush()

    logger.info(
        "workflow_version_created",
        workflow_id=str(workflow.id),
        version=version.version,
        created_by=created_by,
    )
    return version


async def get_workflow_versions(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[WorkflowVersion]:
    """List version history for a workflow."""
    result = await db.execute(
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_workflow_version(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    version: int,
) -> WorkflowVersion | None:
    """Get a specific workflow version."""
    result = await db.execute(
        select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == workflow_id,
            WorkflowVersion.version == version,
        )
    )
    return result.scalar_one_or_none()


async def rollback_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    target_version: int,
    *,
    user_id: str | None = None,
    ip_address: str | None = None,
) -> Workflow | None:
    """Restore a workflow to a previous version, creating a new version snapshot."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        return None

    version = await get_workflow_version(db, workflow_id, target_version)
    if version is None:
        return None

    old_state = {
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "variables": workflow.variables,
        "version": workflow.version,
    }

    workflow.nodes = version.nodes
    workflow.edges = version.edges
    workflow.variables = version.variables

    new_snapshot = await snapshot_workflow_version(db, workflow, created_by=user_id)

    new_state = {
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "variables": workflow.variables,
        "version": new_snapshot.version,
        "rolled_back_from": target_version,
    }

    await record_audit(
        db,
        tenant_id=workflow.tenant_id,
        entity_type="workflow",
        entity_id=workflow.id,
        action="rollback",
        old_value=old_state,
        new_value=new_state,
        user_id=user_id,
        ip_address=ip_address,
    )

    await db.flush()
    return workflow


async def get_audit_log(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    """Query audit log with optional filters."""
    query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if action:
        query = query.where(AuditLog.action == action)

    query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())

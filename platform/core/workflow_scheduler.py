"""Workflow scheduler — runs workflows on cron schedules using APScheduler.

Loads all enabled workflows with ``trigger_type: schedule`` on startup,
registers APScheduler ``CronTrigger`` jobs, and re-schedules whenever
a workflow is toggled or updated.
"""

from datetime import datetime, timezone
from typing import Any, Callable

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from db.models import Workflow

logger = structlog.get_logger()


class WorkflowScheduler:
    """Manages cron-based schedule triggers for workflows."""

    def __init__(
        self,
        session_factory: Callable[..., Any],
        workflow_engine: Any,
    ) -> None:
        self._session_factory = session_factory
        self._engine = workflow_engine
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}

    async def start(self) -> None:
        """Load all scheduled workflows and start the APScheduler."""
        async with self._session_factory() as db:
            from db.base import set_rls_bypass
            await set_rls_bypass(db)
            result = await db.execute(
                select(Workflow).where(Workflow.is_enabled.is_(True))
            )
            workflows = list(result.scalars().all())

        for wf in workflows:
            self._register_if_scheduled(wf)

        self._scheduler.start()
        await logger.ainfo(
            "workflow_scheduler_started",
            scheduled_jobs=len(self._jobs),
        )

    async def stop(self) -> None:
        self._scheduler.shutdown(wait=False)

    def register_workflow(self, workflow: Workflow) -> None:
        """Register or update a workflow's schedule. Call after toggle/update."""
        self.unregister_workflow(str(workflow.id))
        if workflow.is_enabled:
            self._register_if_scheduled(workflow)

    def unregister_workflow(self, workflow_id: str) -> None:
        """Remove a workflow's scheduled job."""
        job_id = self._jobs.pop(workflow_id, None)
        if job_id:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass

    def list_scheduled(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        """Return metadata about all active scheduled jobs."""
        out: list[dict[str, Any]] = []
        for wf_id, job_id in self._jobs.items():
            job = self._scheduler.get_job(job_id)
            if tenant_id and (not job or len(job.args) < 2 or str(job.args[1]) != tenant_id):
                continue
            out.append({
                "workflow_id": wf_id,
                "job_id": job_id,
                "tenant_id": str(job.args[1]) if job and len(job.args) >= 2 else None,
                "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
            })
        return out

    # ── internal ──

    def _register_if_scheduled(self, workflow: Workflow) -> None:
        trigger_config = self._get_schedule_config(workflow)
        if not trigger_config:
            return

        cron_expr = trigger_config.get("cron", "")
        tz = trigger_config.get("timezone", "UTC")

        if not cron_expr:
            return

        job_id = f"wf_schedule_{workflow.id}"

        try:
            parts = cron_expr.split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                    timezone=tz,
                )
            else:
                trigger = CronTrigger.from_crontab(cron_expr, timezone=tz)

            self._scheduler.add_job(
                self._run_scheduled_workflow,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                args=[str(workflow.id), str(workflow.tenant_id)],
            )
            self._jobs[str(workflow.id)] = job_id
        except Exception as exc:
            logger.warning(
                "schedule_registration_failed",
                workflow_id=str(workflow.id),
                cron=cron_expr,
                error=str(exc),
            )

    @staticmethod
    def _get_schedule_config(workflow: Workflow) -> dict[str, Any] | None:
        for node in workflow.nodes or []:
            if node.get("type") == "trigger":
                config = node.get("config", {})
                if config.get("trigger_type") == "schedule":
                    return config
        return None

    async def _run_scheduled_workflow(
        self, workflow_id: str, tenant_id: str,
    ) -> None:
        try:
            async with self._session_factory() as db:
                from db.base import set_rls_bypass
                await set_rls_bypass(db)

                result = await db.execute(
                    select(Workflow).where(
                        Workflow.id == workflow_id,
                        Workflow.is_enabled.is_(True),
                    )
                )
                workflow = result.scalar_one_or_none()
                if not workflow:
                    await logger.ainfo(
                        "scheduled_workflow_skipped",
                        workflow_id=workflow_id,
                        reason="not_found_or_disabled",
                    )
                    return

                trigger_data = {
                    "trigger_type": "schedule",
                    "scheduled_at": datetime.now(timezone.utc).isoformat(),
                    "cron_expression": self._get_schedule_config(workflow).get("cron", ""),
                    "workflow_id": workflow_id,
                }

                execution = await self._engine.execute_workflow(db, workflow, trigger_data)
                await self._engine.record_execution_sync(db, workflow, execution, trigger_data)
                await db.commit()

                await logger.ainfo(
                    "scheduled_workflow_executed",
                    workflow_id=workflow_id,
                    workflow_name=workflow.name,
                    execution_id=str(execution.id),
                    status=execution.status,
                )
        except Exception as exc:
            await logger.aerror(
                "scheduled_workflow_failed",
                workflow_id=workflow_id,
                error=str(exc),
            )

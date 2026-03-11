"""Regression tests for Phase 3 workflow engine features."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from core.workflow_engine import WorkflowContext, WorkflowEngine, WorkflowError
from core.workflow_scheduler import WorkflowScheduler


class _DummyResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _DummyDb:
    def __init__(self, execute_value=None) -> None:
        self._execute_value = execute_value
        self.added = []

    async def execute(self, *args, **kwargs):
        return _DummyResult(self._execute_value)

    def add(self, value) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        return None

    async def refresh(self, value) -> None:
        return None


class _DummyAsyncSessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _DummyExecuteResult:
    def __init__(self, workflow):
        self._workflow = workflow

    def scalar_one_or_none(self):
        return self._workflow

    def scalars(self):
        return _DummyScalarResult([self._workflow] if self._workflow is not None else [])


@pytest.mark.asyncio
async def test_dry_run_action_uses_manifest_output_schema() -> None:
    engine = WorkflowEngine()
    engine.set_mock_output_schema_resolver(
        lambda connector_name, connector_version, action: [
            {"field": "shipment_id", "type": "string"},
            {"field": "success", "type": "boolean"},
            {"field": "parcels", "type": "object[]"},
        ]
    )
    ctx = WorkflowContext({"order_id": "ORD-1"})
    ctx.dry_run = True
    workflow = SimpleNamespace(tenant_id=uuid.uuid4())

    result = await engine._exec_action(
        {
            "connector_name": "inpost",
            "action": "shipment.create",
            "field_mapping": [{"from": "order_id", "to": "reference"}],
        },
        ctx,
        workflow,
    )

    assert result["dry_run"] is True
    assert result["would_send"] == {"reference": "ORD-1"}
    assert result["shipment_id"] == "mock_string"
    assert result["success"] is True
    assert result["parcels"] == [{}]


@pytest.mark.asyncio
async def test_subworkflow_detects_circular_reference_from_parent_chain() -> None:
    engine = WorkflowEngine()
    parent_id = uuid.uuid4()
    current_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    child_workflow = SimpleNamespace(id=parent_id, tenant_id=tenant_id, name="parent")
    db = _DummyDb(execute_value=child_workflow)

    ctx = WorkflowContext({"order": {"id": "1"}})
    ctx._workflow_chain = [str(parent_id), str(current_id)]
    workflow = SimpleNamespace(id=current_id, tenant_id=tenant_id)

    with pytest.raises(WorkflowError, match="Circular sub-workflow reference detected"):
        await engine._exec_sub_workflow(
            db,
            {"workflow_id": str(parent_id)},
            ctx,
            workflow,
            depth=0,
        )


@pytest.mark.asyncio
async def test_rerun_from_node_restores_replay_state_before_target_node() -> None:
    engine = WorkflowEngine()
    workflow_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    db = _DummyDb()
    workflow = SimpleNamespace(
        id=workflow_id,
        tenant_id=tenant_id,
        name="Replay Workflow",
        variables={},
        nodes=[{"id": "node-2", "type": "transform", "config": {}}],
        edges=[],
        timeout_seconds=30,
    )
    original_execution = SimpleNamespace(
        id=uuid.uuid4(),
        trigger_data={"start": "value"},
        node_results=[
            {
                "node_id": "node-2",
                "_replay_state": {
                    "data": {"full_payload": {"a": 1, "b": 2}},
                    "variables": {"status": "before"},
                    "node_outputs": {"node-1": {"source": "ok"}},
                },
            }
        ],
        context_snapshot={
            "data": {"wrong": "final"},
            "variables": {"status": "after"},
        },
    )

    async def _fake_execute_single_node(db_session, graph, node, ctx, wf, depth):
        assert ctx.data == {"full_payload": {"a": 1, "b": 2}}
        assert ctx.variables == {"status": "before"}
        assert ctx.node_outputs == {"node-1": {"source": "ok"}}
        ctx.set_node_output(node["id"], {"rerun": True})
        ctx.data = {**ctx.data, "rerun": True}
        ctx.node_results.append(
            {
                "node_id": node["id"],
                "node_type": node["type"],
                "status": "success",
                "output": {"rerun": True},
                "_raw_output": {"rerun": True},
                "_replay_state": {
                    "data": {"full_payload": {"a": 1, "b": 2}},
                    "variables": {"status": "before"},
                    "node_outputs": {"node-1": {"source": "ok"}},
                },
                "duration_ms": 1,
            }
        )

    engine._execute_single_node = _fake_execute_single_node  # type: ignore[method-assign]

    execution = await engine.rerun_from_node(
        db,
        workflow,
        original_execution,
        from_node_id="node-2",
    )

    assert execution.status == "success"
    assert execution.context_snapshot["data"]["full_payload"] == {"a": 1, "b": 2}
    assert execution.context_snapshot["data"]["rerun"] is True
    assert execution.context_snapshot["variables"] == {"status": "before"}


def test_workflow_scheduler_filters_jobs_by_tenant() -> None:
    scheduler = WorkflowScheduler(lambda: None, workflow_engine=None)
    scheduler._jobs = {
        "wf-a": "job-a",
        "wf-b": "job-b",
    }

    scheduler._scheduler = SimpleNamespace(
        get_job=lambda job_id: SimpleNamespace(
            args=["wf-a", "tenant-a"] if job_id == "job-a" else ["wf-b", "tenant-b"],
            next_run_time=None,
        )
    )

    assert scheduler.list_scheduled("tenant-a") == [
        {"workflow_id": "wf-a", "job_id": "job-a", "tenant_id": "tenant-a", "next_run": None}
    ]


@pytest.mark.asyncio
async def test_scheduled_workflow_trigger_data_includes_cron_expression(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}
    workflow = SimpleNamespace(
        id="wf-1",
        tenant_id="tenant-1",
        name="Scheduled Workflow",
        is_enabled=True,
        nodes=[
            {
                "id": "trigger-1",
                "type": "trigger",
                "config": {
                    "trigger_type": "schedule",
                    "cron": "0 */1 * * *",
                    "timezone": "Europe/Warsaw",
                },
            }
        ],
    )

    class _SchedulerDb:
        async def execute(self, *args, **kwargs):
            return _DummyExecuteResult(workflow)

        async def commit(self):
            return None

    def _session_factory():
        return _DummyAsyncSessionContext(_SchedulerDb())

    async def _fake_set_rls_bypass(_db):
        return None

    class _Engine:
        async def execute_workflow(self, db, workflow_obj, trigger_data):
            captured["trigger_data"] = trigger_data
            return SimpleNamespace(id="exec-1", status="success")

        async def record_execution_sync(self, db, workflow_obj, execution, trigger_data):
            captured["sync_trigger_data"] = trigger_data
            return None

    monkeypatch.setattr("db.base.set_rls_bypass", _fake_set_rls_bypass)

    scheduler = WorkflowScheduler(_session_factory, workflow_engine=_Engine())
    await scheduler._run_scheduled_workflow("wf-1", "tenant-1")

    assert captured["trigger_data"]["trigger_type"] == "schedule"
    assert captured["trigger_data"]["cron_expression"] == "0 */1 * * *"
    assert captured["sync_trigger_data"]["cron_expression"] == "0 */1 * * *"


@pytest.mark.asyncio
async def test_error_handler_notify_uses_action_executor() -> None:
    engine = WorkflowEngine()
    sent = {}

    async def _fake_action_executor(**kwargs):
        sent.update(kwargs)
        return {"ok": True}

    engine.set_action_executor(_fake_action_executor)
    ctx = WorkflowContext({"order_id": "ORD-1"})
    ctx.variables["_error"] = {
        "error": "boom",
        "failed_node_id": "node-3",
    }
    workflow = SimpleNamespace(tenant_id=uuid.uuid4())

    result = await engine._exec_error_handler(
        {
            "actions": [
                {"type": "notify", "channel": "slack", "message": "Flow failed: {{vars._error.error}}"},
            ]
        },
        ctx,
        workflow,
    )

    assert sent["connector_name"] == "slack"
    assert sent["action"] == "message.send"
    assert sent["payload"] == {"text": "Flow failed: boom"}
    assert result["handler_actions"][0]["type"] == "notify"
    assert result["handler_actions"][0]["status"] == "sent"


@pytest.mark.asyncio
async def test_batch_node_supports_body_nodes_config_without_body_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = WorkflowEngine()
    tenant_id = uuid.uuid4()
    workflow = SimpleNamespace(tenant_id=tenant_id)
    ctx = WorkflowContext({"orders": [{"id": "ORD-1"}]})
    db = _DummyDb()
    graph = type(
        "_Graph",
        (),
        {
            "get_successors": staticmethod(lambda *_args, **_kwargs: []),
            "get_node": staticmethod(lambda node_id: {"id": node_id, "type": "transform", "config": {}}),
        },
    )()

    item_db = _DummyDb()

    def _fake_session_factory():
        return _DummyAsyncSessionContext(item_db)

    async def _fake_set_rls_bypass(_db):
        return None

    async def _fake_execute_nodes(db_session, graph_obj, nodes, item_ctx, wf, depth):
        assert nodes[0]["id"] == "node-body"
        item_ctx.data["processed"] = item_ctx.variables["batch_item"]["id"]

    monkeypatch.setattr("db.base.async_session_factory", _fake_session_factory)
    monkeypatch.setattr("db.base.set_rls_bypass", _fake_set_rls_bypass)
    engine._execute_nodes = _fake_execute_nodes  # type: ignore[method-assign]

    result = await engine._exec_batch(
        db,
        graph,
        {"id": "batch-1", "type": "batch"},
        {"source": "{{orders}}", "body_nodes": ["node-body"]},
        ctx,
        workflow,
        depth=0,
    )

    assert result["batch_succeeded"] == 1
    assert result["batch_results"] == [{"processed": "ORD-1"}]

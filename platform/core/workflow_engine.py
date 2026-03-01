"""Workflow Engine -- executes graph-based workflows (DAGs).

Supports node types: trigger, action, condition, switch, think, transform,
filter, delay, loop, merge, parallel, aggregate, http_request, set_variable,
response.

The engine traverses the DAG starting from the trigger node, executing
each node and routing data along edges based on node outputs.
"""

import asyncio
import copy
import operator
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Workflow, WorkflowExecution

logger = structlog.get_logger()

OPERATOR_MAP: dict[str, Callable[[Any, Any], bool]] = {
    "eq": operator.eq,
    "neq": operator.ne,
    "gt": operator.gt,
    "lt": operator.lt,
    "gte": operator.ge,
    "lte": operator.le,
}


def _coerce_types(a: Any, b: Any) -> tuple[Any, Any]:
    """Coerce two values to compatible types for comparison.

    Handles the common case where one side is a number and the other
    is a string representation of a number (e.g. AI returns int 1 but
    the condition value is stored as string "1").
    """
    if type(a) is type(b):
        return a, b
    if isinstance(a, (int, float)) and isinstance(b, str):
        try:
            return a, type(a)(b)
        except (ValueError, TypeError):
            return str(a), b
    if isinstance(b, (int, float)) and isinstance(a, str):
        try:
            return type(b)(a), b
        except (ValueError, TypeError):
            return a, str(b)
    return str(a), str(b)


class WorkflowContext:
    """Mutable context passed through the workflow DAG."""

    def __init__(self, trigger_data: dict[str, Any]) -> None:
        self.data: dict[str, Any] = copy.deepcopy(trigger_data)
        self.variables: dict[str, Any] = {}
        self.node_outputs: dict[str, Any] = {}
        self.node_results: list[dict[str, Any]] = []

    def set_node_output(self, node_id: str, output: Any) -> None:
        self.node_outputs[node_id] = output

    def get_node_output(self, node_id: str) -> Any:
        return self.node_outputs.get(node_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "data": copy.deepcopy(self.data),
            "variables": copy.deepcopy(self.variables),
        }


ExecuteActionFn = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


class WorkflowEngine:
    def __init__(self) -> None:
        self._action_executor: ExecuteActionFn | None = None

    def set_action_executor(self, fn: ExecuteActionFn) -> None:
        self._action_executor = fn

    async def get_workflows_for_event(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        event: str,
    ) -> list[Workflow]:
        result = await db.execute(
            select(Workflow).where(
                Workflow.tenant_id == tenant_id,
                Workflow.trigger_connector == connector_name,
                Workflow.trigger_event == event,
                Workflow.is_enabled.is_(True),
            )
        )
        return list(result.scalars().all())

    async def execute_workflow(
        self,
        db: AsyncSession,
        workflow: Workflow,
        trigger_data: dict[str, Any],
    ) -> WorkflowExecution:
        start_time = time.monotonic()
        ctx = WorkflowContext(trigger_data)

        for var_name, var_def in (workflow.variables or {}).items():
            ctx.variables[var_name] = var_def.get("default")

        execution = WorkflowExecution(
            workflow_id=workflow.id,
            tenant_id=workflow.tenant_id,
            workflow_name=workflow.name,
            status="running",
            trigger_data=trigger_data,
            workflow_nodes_snapshot=workflow.nodes,
            workflow_edges_snapshot=workflow.edges,
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        try:
            graph = WorkflowGraph(workflow.nodes, workflow.edges)
            trigger_node = graph.find_trigger()
            if not trigger_node:
                raise WorkflowError("No trigger node found in workflow")

            ctx.set_node_output(trigger_node["id"], trigger_data)
            ctx.data = copy.deepcopy(trigger_data)
            ctx.node_results.append({
                "node_id": trigger_node["id"],
                "node_type": "trigger",
                "label": trigger_node.get("label", trigger_node["id"]),
                "status": "success",
                "output": _safe_truncate(trigger_data),
                "duration_ms": 0,
            })

            successors = graph.get_successors(trigger_node["id"])
            await self._execute_nodes(db, graph, successors, ctx, workflow)

            execution.status = "success"
        except WorkflowError as exc:
            execution.status = "failed"
            execution.error = str(exc)
            execution.error_node_id = getattr(exc, "node_id", None)
        except Exception as exc:
            execution.status = "failed"
            execution.error = str(exc)

        execution.node_results = ctx.node_results
        execution.context_snapshot = ctx.snapshot()
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration_ms = int((time.monotonic() - start_time) * 1000)

        await db.flush()
        await logger.ainfo(
            "workflow_executed",
            workflow_id=str(workflow.id),
            workflow_name=workflow.name,
            status=execution.status,
            duration_ms=execution.duration_ms,
            nodes_executed=len(ctx.node_results),
        )
        return execution

    async def _execute_nodes(
        self,
        db: AsyncSession,
        graph: "WorkflowGraph",
        nodes: list[dict[str, Any]],
        ctx: WorkflowContext,
        workflow: Workflow,
        depth: int = 0,
    ) -> None:
        if depth > 200:
            raise WorkflowError("Maximum workflow depth exceeded (possible cycle)")

        for node in nodes:
            await self._execute_single_node(db, graph, node, ctx, workflow, depth)

    async def _execute_single_node(
        self,
        db: AsyncSession,
        graph: "WorkflowGraph",
        node: dict[str, Any],
        ctx: WorkflowContext,
        workflow: Workflow,
        depth: int,
    ) -> None:
        node_id = node["id"]
        node_type = node["type"]
        config = node.get("config", {})
        node_start = time.monotonic()

        result_entry: dict[str, Any] = {
            "node_id": node_id,
            "node_type": node_type,
            "label": node.get("label", ""),
            "status": "running",
        }

        try:
            output: Any = None
            next_handle: str | None = None

            if node_type == "action":
                output = await self._exec_action(config, ctx, workflow)
            elif node_type == "think":
                output = await self._exec_think(config, ctx, workflow)
            elif node_type == "condition":
                output, next_handle = self._exec_condition(config, ctx)
            elif node_type == "switch":
                output, next_handle = self._exec_switch(config, ctx)
            elif node_type == "transform":
                output = self._exec_transform(config, ctx)
            elif node_type == "filter":
                passed = self._exec_filter(config, ctx)
                if not passed:
                    result_entry["status"] = "filtered"
                    result_entry["duration_ms"] = int((time.monotonic() - node_start) * 1000)
                    ctx.node_results.append(result_entry)
                    return
                output = ctx.data
            elif node_type == "delay":
                seconds = config.get("seconds", 0)
                if 0 < seconds <= 60:
                    await asyncio.sleep(seconds)
                output = ctx.data
            elif node_type == "loop":
                output = await self._exec_loop(db, graph, node, config, ctx, workflow, depth)
                next_handle = "done"
            elif node_type == "http_request":
                output = await self._exec_http_request(config, ctx)
            elif node_type == "set_variable":
                output = self._exec_set_variable(config, ctx)
            elif node_type == "merge":
                output = ctx.data
            elif node_type == "parallel":
                output = await self._exec_parallel(db, graph, node, config, ctx, workflow, depth)
                next_handle = "done"
            elif node_type == "aggregate":
                output = self._exec_aggregate(config, ctx)
            elif node_type == "response":
                output = self._exec_response(config, ctx)
                ctx.set_node_output(node_id, output)
                result_entry["status"] = "success"
                result_entry["output"] = _safe_truncate(output)
                result_entry["duration_ms"] = int((time.monotonic() - node_start) * 1000)
                ctx.node_results.append(result_entry)
                return

            ctx.set_node_output(node_id, output)
            if isinstance(output, dict):
                ctx.data = {**ctx.data, **output}

            result_entry["status"] = "success"
            result_entry["output"] = _safe_truncate(output)
            result_entry["duration_ms"] = int((time.monotonic() - node_start) * 1000)
            ctx.node_results.append(result_entry)

            if next_handle is not None:
                successors = graph.get_successors(node_id, handle=next_handle)
            else:
                successors = graph.get_successors(node_id)

            if successors:
                await self._execute_nodes(db, graph, successors, ctx, workflow, depth + 1)

        except Exception as exc:
            result_entry["status"] = "failed"
            result_entry["error"] = str(exc)
            result_entry["duration_ms"] = int((time.monotonic() - node_start) * 1000)
            ctx.node_results.append(result_entry)

            on_error = config.get("on_error", workflow.on_error)
            if on_error == "continue":
                successors = graph.get_successors(node_id)
                if successors:
                    await self._execute_nodes(db, graph, successors, ctx, workflow, depth + 1)
            else:
                error = WorkflowError(f"Node '{node.get('label', node_id)}' failed: {exc}")
                error.node_id = node_id  # type: ignore[attr-defined]
                raise error from exc

    # ── Node executors ──

    async def _exec_action(
        self, config: dict, ctx: WorkflowContext, workflow: Workflow
    ) -> dict[str, Any]:
        connector_name = config.get("connector_name", "")
        action = config.get("action", "")
        credential_name = config.get("credential_name", "default")
        if not connector_name or not action:
            raise WorkflowError("Action node missing connector_name or action")

        payload = self._apply_field_mapping(config.get("field_mapping", []), ctx)

        if self._action_executor:
            return await self._action_executor(
                connector_name=connector_name,
                action=action,
                payload=payload,
                tenant_id=workflow.tenant_id,
                credential_name=credential_name,
            )
        return {"dispatched": True, "connector": connector_name, "action": action, "payload": payload}

    async def _exec_think(
        self, config: dict, ctx: WorkflowContext, workflow: Workflow
    ) -> dict[str, Any]:
        """Execute a Think (AI Agent) node — sends prompt + data to ai-agent connector."""
        import json as _json

        action = config.get("action", "agent.analyze")
        credential_name = config.get("credential_name", "default")
        prompt = config.get("prompt", "")
        temperature = config.get("temperature", 0.1)

        output_schema_json = config.get("output_schema_json", "")
        output_schema = None
        if output_schema_json:
            try:
                output_schema = _json.loads(output_schema_json)
            except _json.JSONDecodeError:
                pass

        if not prompt:
            raise WorkflowError("Think node requires a prompt")

        prompt = self._interpolate_string(prompt, ctx)

        redact = config.get("redact_pii", True)
        if redact:
            send_data = await _redact_pii(
                ctx.data, self._action_executor, workflow.tenant_id, credential_name
            )
        else:
            send_data = ctx.data

        payload: dict[str, Any] = {
            "prompt": prompt,
            "data": send_data,
            "temperature": temperature,
        }
        if output_schema:
            payload["output_schema"] = output_schema

        if self._action_executor:
            result = await self._action_executor(
                connector_name="ai-agent",
                action=action,
                payload=payload,
                tenant_id=workflow.tenant_id,
                credential_name=credential_name,
            )
            if isinstance(result, dict) and "result" in result:
                ai_output = result["result"]
                if isinstance(ai_output, dict):
                    ai_output["_confidence"] = result.get("confidence")
                    ai_output["_analysis_id"] = result.get("analysis_id")
                    ai_output["_model_used"] = result.get("model_used")
                    return ai_output
            return result

        return {"dispatched": True, "connector": "ai-agent", "action": action, "prompt": prompt}

    def _exec_condition(
        self, config: dict, ctx: WorkflowContext
    ) -> tuple[dict[str, Any], str]:
        conditions = config.get("conditions", [])
        logic = config.get("logic", "and")

        results = [self._evaluate_condition(c, ctx) for c in conditions]

        if logic == "or":
            passed = any(results)
        else:
            passed = all(results)

        handle = "true" if passed else "false"
        return {"condition_result": passed, "handle": handle}, handle

    def _exec_switch(
        self, config: dict, ctx: WorkflowContext
    ) -> tuple[dict[str, Any], str]:
        field = config.get("field", "")
        cases = config.get("cases", [])
        default_handle = config.get("default_handle", "default")

        value = self._resolve_value(field, ctx)

        for case in cases:
            if str(value) == str(case.get("value", "")):
                handle = case.get("handle", str(case.get("value", "")))
                return {"switch_value": value, "matched_case": handle}, handle

        return {"switch_value": value, "matched_case": default_handle}, default_handle

    def _exec_transform(self, config: dict, ctx: WorkflowContext) -> dict[str, Any]:
        mappings = config.get("mappings", [])
        result = self._apply_field_mapping(mappings, ctx)

        expressions = config.get("expressions", {})
        for key, expr in expressions.items():
            result[key] = self._evaluate_expression(expr, ctx)

        return result

    def _exec_filter(self, config: dict, ctx: WorkflowContext) -> bool:
        conditions = config.get("conditions", [])
        logic = config.get("logic", "and")
        results = [self._evaluate_condition(c, ctx) for c in conditions]
        return all(results) if logic == "and" else any(results)

    async def _exec_loop(
        self,
        db: AsyncSession,
        graph: "WorkflowGraph",
        node: dict[str, Any],
        config: dict,
        ctx: WorkflowContext,
        workflow: Workflow,
        depth: int,
    ) -> dict[str, Any]:
        array_field = config.get("array_field", "")
        item_var = config.get("item_variable", "item")
        index_var = config.get("index_variable", "index")
        max_iterations = min(config.get("max_iterations", 100), 1000)

        array_data = self._resolve_value(array_field, ctx)
        if not isinstance(array_data, list):
            return {"loop_iterations": 0, "loop_results": []}

        loop_body_nodes = graph.get_successors(node["id"], handle="default")
        loop_results: list[Any] = []

        for i, item in enumerate(array_data[:max_iterations]):
            ctx.variables[item_var] = item
            ctx.variables[index_var] = i
            if loop_body_nodes:
                await self._execute_nodes(db, graph, loop_body_nodes, ctx, workflow, depth + 1)
            loop_results.append(copy.deepcopy(ctx.variables.get(item_var)))

        ctx.variables[f"{item_var}_results"] = loop_results
        return {"loop_iterations": len(loop_results), "loop_results": loop_results}

    async def _exec_parallel(
        self,
        db: AsyncSession,
        graph: "WorkflowGraph",
        node: dict[str, Any],
        config: dict,
        ctx: WorkflowContext,
        workflow: Workflow,
        depth: int,
    ) -> dict[str, Any]:
        """Execute all successor branches in parallel (scatter-gather).

        Each successor gets a copy of the current context. Results are
        collected into ``ctx.variables["parallel_results"]`` keyed by
        node id so downstream aggregate nodes can compare them.
        """
        successors = graph.get_successors(node["id"], handle="branch")
        if not successors:
            return {"parallel_branches": 0, "results": {}}

        timeout = min(config.get("timeout_seconds", 60), 120)

        async def _run_branch(branch_node: dict[str, Any]) -> tuple[str, Any]:
            branch_ctx = WorkflowContext(copy.deepcopy(ctx.data))
            branch_ctx.variables = copy.deepcopy(ctx.variables)
            branch_ctx.node_outputs = copy.deepcopy(ctx.node_outputs)

            try:
                await self._execute_single_node(db, graph, branch_node, branch_ctx, workflow, depth + 1)
                output = branch_ctx.get_node_output(branch_node["id"])
                ctx.node_results.extend(branch_ctx.node_results)
                return branch_node["id"], output
            except Exception as exc:
                ctx.node_results.extend(branch_ctx.node_results)
                return branch_node["id"], {"error": str(exc)}

        tasks = [asyncio.create_task(_run_branch(s)) for s in successors]

        try:
            done = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        except asyncio.TimeoutError:
            for t in tasks:
                t.cancel()
            raise WorkflowError(f"Parallel node timed out after {timeout}s")

        results: dict[str, Any] = {}
        for item in done:
            if isinstance(item, tuple):
                node_id, output = item
                results[node_id] = output
                ctx.set_node_output(node_id, output)

        ctx.variables["parallel_results"] = results
        return {"parallel_branches": len(successors), "results": results}

    def _exec_aggregate(self, config: dict, ctx: WorkflowContext) -> dict[str, Any]:
        """Aggregate results from parallel branches.

        Supports strategies: min_price, max_price, first, concat.
        """
        strategy = config.get("strategy", "min_price")
        source_var = config.get("source_variable", "parallel_results")
        price_field = config.get("price_field", "price")
        name_field = config.get("name_field", "name")

        parallel_results: dict[str, Any] = ctx.variables.get(source_var, {})
        if not parallel_results:
            return {"aggregated": [], "winner": None}

        flat_products: list[dict[str, Any]] = []
        for branch_id, branch_output in parallel_results.items():
            if isinstance(branch_output, dict):
                products = branch_output.get("products", [])
                if isinstance(products, list):
                    for p in products:
                        if isinstance(p, dict):
                            p["_branch_id"] = branch_id
                            p["_source"] = p.get("attributes", {}).get("source", branch_id)
                            flat_products.append(p)

        if not flat_products:
            return {"aggregated": [], "winner": None}

        if strategy == "min_price":
            valid = [p for p in flat_products if isinstance(p.get(price_field), (int, float)) and p[price_field] > 0]
            if valid:
                valid.sort(key=lambda p: p[price_field])
                return {
                    "aggregated": valid,
                    "winner": valid[0],
                    "cheapest_price": valid[0][price_field],
                    "cheapest_source": valid[0].get("_source", ""),
                    "cheapest_name": valid[0].get(name_field, ""),
                    "total_results": len(valid),
                }
        elif strategy == "max_price":
            valid = [p for p in flat_products if isinstance(p.get(price_field), (int, float)) and p[price_field] > 0]
            if valid:
                valid.sort(key=lambda p: p[price_field], reverse=True)
                return {
                    "aggregated": valid,
                    "winner": valid[0],
                    "highest_price": valid[0][price_field],
                    "highest_source": valid[0].get("_source", ""),
                    "total_results": len(valid),
                }
        elif strategy == "concat":
            return {"aggregated": flat_products, "winner": None, "total_results": len(flat_products)}

        return {"aggregated": flat_products, "winner": flat_products[0] if flat_products else None, "total_results": len(flat_products)}

    async def _exec_http_request(
        self, config: dict, ctx: WorkflowContext
    ) -> dict[str, Any]:
        import httpx

        url = self._interpolate_string(config.get("url", ""), ctx)
        method = config.get("method", "GET").upper()
        headers = {
            k: self._interpolate_string(v, ctx)
            for k, v in config.get("headers", {}).items()
        }
        body_template = config.get("body", {})
        body = self._interpolate_dict(body_template, ctx) if body_template else None
        timeout = min(config.get("timeout_seconds", 30), 60)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, url, headers=headers, json=body)
            try:
                response_data = response.json()
            except Exception:
                response_data = {"text": response.text[:2000]}

        return {
            "status_code": response.status_code,
            "body": response_data,
            "headers": dict(response.headers),
        }

    def _exec_set_variable(self, config: dict, ctx: WorkflowContext) -> dict[str, Any]:
        variable_name = config.get("variable_name", "")
        value_expr = config.get("value", "")

        if isinstance(value_expr, str) and value_expr.startswith("{{") and value_expr.endswith("}}"):
            resolved = self._resolve_value(value_expr[2:-2].strip(), ctx)
        elif isinstance(value_expr, (dict, list)):
            resolved = self._interpolate_dict(value_expr, ctx)
        else:
            resolved = value_expr

        ctx.variables[variable_name] = resolved
        return {"variable": variable_name, "value": resolved}

    def _exec_response(self, config: dict, ctx: WorkflowContext) -> dict[str, Any]:
        body_template = config.get("body", {})
        return self._interpolate_dict(body_template, ctx) if body_template else ctx.data

    # ── Helpers ──

    def _evaluate_condition(self, condition: dict, ctx: WorkflowContext) -> bool:
        field = condition.get("field", "")
        op = condition.get("operator", "eq")
        expected = condition.get("value")

        if isinstance(expected, str) and "{{" in expected:
            expected = self._interpolate_string(expected, ctx)

        actual = self._resolve_value(field, ctx)

        if op in OPERATOR_MAP:
            try:
                if OPERATOR_MAP[op](actual, expected):
                    return True
            except TypeError:
                pass
            actual_c, expected_c = _coerce_types(actual, expected)
            try:
                return OPERATOR_MAP[op](actual_c, expected_c)
            except TypeError:
                return False
        elif op == "contains":
            return expected in actual if actual else False
        elif op == "not_contains":
            return expected not in actual if actual else True
        elif op == "starts_with":
            return str(actual).startswith(str(expected)) if actual else False
        elif op == "ends_with":
            return str(actual).endswith(str(expected)) if actual else False
        elif op == "exists":
            return actual is not None
        elif op == "not_exists":
            return actual is None
        elif op == "in":
            return actual in (expected if isinstance(expected, list) else [expected])
        elif op == "not_in":
            return actual not in (expected if isinstance(expected, list) else [expected])
        elif op == "regex":
            return bool(re.search(str(expected), str(actual))) if actual is not None else False
        elif op == "is_empty":
            return not actual
        elif op == "is_not_empty":
            return bool(actual)
        return False

    def _resolve_value(self, path: str, ctx: WorkflowContext) -> Any:
        if not path:
            return None

        if path.startswith("vars."):
            var_path = path[5:]
            return _get_nested(ctx.variables, var_path)
        if path.startswith("nodes."):
            parts = path[6:].split(".", 1)
            node_id = parts[0]
            node_output = ctx.get_node_output(node_id)
            if len(parts) > 1 and isinstance(node_output, dict):
                return _get_nested(node_output, parts[1])
            return node_output

        return _get_nested(ctx.data, path)

    def _resolve_sources(
        self, m: dict, ctx: WorkflowContext
    ) -> list[Any]:
        """Resolve all source values for a mapping rule.

        Supports both legacy single-source (``from``) and multi-source
        (``sources``) modes.  Returns a list of resolved values.
        """
        sources: list[str] = m.get("sources", [])
        if sources:
            return [self._resolve_value(s, ctx) for s in sources]

        from_field = m.get("from", "")
        if not from_field:
            return []
        if from_field == "__custom__":
            return [m.get("from_custom", "")]
        return [self._resolve_value(from_field, ctx)]

    def _apply_field_mapping(
        self, mappings: list[dict], ctx: WorkflowContext
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        body_text_extras: list[str] = []
        subject_extras: list[str] = []

        for m in mappings:
            to_field = m.get("to", "")
            if to_field == "__custom__":
                to_field = m.get("to_custom", "")
            if not to_field:
                continue

            resolved = self._resolve_sources(m, ctx)
            if not resolved and not m.get("from", "") and not m.get("sources"):
                continue

            raw_transform = m.get("transform")
            if raw_transform:
                steps = raw_transform if isinstance(raw_transform, list) else [raw_transform]
                pipe: list[Any] = resolved
                for step in steps:
                    pipe = [self._apply_transform(pipe, step, ctx)]
                value = pipe[0]
            elif len(resolved) == 1:
                value = resolved[0]
            else:
                value = " ".join(str(v) for v in resolved if v is not None)

            if value is None:
                continue

            is_concat = to_field in result
            _set_nested(result, to_field, value)
            if is_concat and isinstance(value, (str, int, float)):
                if to_field == "body_text":
                    body_text_extras.append(str(value))
                elif to_field == "subject":
                    subject_extras.append(str(value))

        if body_text_extras and "body_text" in result:
            original = result["body_text"]
            for e in body_text_extras:
                original = original.replace(f"{e} ", "", 1)
            result["body_text"] = "\n\n".join(body_text_extras) + "\n\n---\n\n" + original

        if body_text_extras and "body_html" in result and result["body_html"]:
            extra_html = "".join(
                f'<div style="background:#f0f4ff;border-left:4px solid #1565c0;'
                f'padding:12px;margin-bottom:16px;font-family:sans-serif;">'
                f'<strong>AI:</strong> {_html_escape(e)}</div>'
                for e in body_text_extras
            )
            result["body_html"] = extra_html + result["body_html"]

        if subject_extras and "subject" in result:
            prefix = " | ".join(str(e) for e in subject_extras)
            original_subject = result["subject"]
            for e in subject_extras:
                original_subject = original_subject.replace(f"{e} ", "", 1)
            result["subject"] = f"[{prefix}] {original_subject.strip()}"

        return result

    def _apply_transform(self, values: list[Any], transform: dict, ctx: WorkflowContext | None = None) -> Any:
        """Apply a transform to resolved source values.

        ``values`` is always a list (single-element for 1:1 mappings).
        Most single-value transforms operate on ``values[0]``.
        Multi-source transforms (template, join, coalesce) use the full list.
        """
        t = transform.get("type", "")
        val = values[0] if values else None

        # -- multi-source transforms --
        if t == "template":
            tpl = transform.get("template", "")
            for i, v in enumerate(values):
                tpl = tpl.replace(f"{{{{{i}}}}}", str(v) if v is not None else "")
            return tpl
        if t == "join":
            sep = transform.get("separator", " ")
            return sep.join(str(v) for v in values if v is not None)
        if t == "coalesce":
            for v in values:
                if v is not None:
                    return v
            return transform.get("default_value")

        # -- single-value transforms --
        if t == "map" or t == "lookup":
            table = transform.get("values") or transform.get("table", {})
            return table.get(str(val), transform.get("default", val))
        if t == "format":
            return transform.get("template", "{}").format(val)
        if t == "uppercase":
            return str(val).upper() if val is not None else None
        if t == "lowercase":
            return str(val).lower() if val is not None else None
        if t == "to_int":
            try:
                return int(val)
            except (ValueError, TypeError):
                return val
        if t == "to_float":
            try:
                return float(val)
            except (ValueError, TypeError):
                return val
        if t == "to_string":
            return str(val) if val is not None else None
        if t == "default":
            return val if val is not None else transform.get("default_value")
        if t == "concat":
            separator = transform.get("separator", "")
            parts = transform.get("parts", [])
            return separator.join(str(p) for p in parts)
        if t == "split":
            separator = transform.get("separator", ",")
            return str(val).split(separator) if val is not None else []
        if t == "trim":
            return str(val).strip() if val is not None else None
        if t == "replace":
            old = transform.get("old", "")
            new = transform.get("new", "")
            return str(val).replace(old, new) if val is not None else None
        if t == "regex_extract":
            pattern = transform.get("pattern", "")
            group = transform.get("group", 0)
            if val is None or not pattern:
                return val
            match = re.search(pattern, str(val))
            if match:
                try:
                    return match.group(group)
                except IndexError:
                    return match.group(0)
            return None
        if t == "field_resolve":
            if val is None or val == "":
                fallback_field = transform.get("fallback_field")
                if fallback_field and ctx is not None:
                    return self._resolve_value(fallback_field, ctx)
                return transform.get("default", val)
            field_path = str(val)
            if ctx is not None:
                resolved = self._resolve_value(field_path, ctx)
                if resolved is not None:
                    return resolved
            fallback_field = transform.get("fallback_field")
            if fallback_field and ctx is not None:
                return self._resolve_value(fallback_field, ctx)
            return transform.get("default", val)
        if t == "regex_replace":
            pattern = transform.get("pattern", "")
            replacement = transform.get("replacement", "")
            if val is None or not pattern:
                return val
            return re.sub(pattern, replacement, str(val))
        if t == "substring":
            start = transform.get("start", 0)
            end = transform.get("end")
            s = str(val) if val is not None else ""
            return s[start:end] if end is not None else s[start:]
        if t == "date_format":
            in_fmt = transform.get("input_format", "%Y-%m-%d")
            out_fmt = transform.get("output_format", "%d.%m.%Y")
            try:
                return datetime.strptime(str(val), in_fmt).strftime(out_fmt)
            except (ValueError, TypeError):
                return val
        if t == "math":
            op = transform.get("operation", "add")
            operand = transform.get("operand", 0)
            operand_field = transform.get("operand_field")
            if operand_field and ctx is not None:
                resolved = self._resolve_value(operand_field, ctx)
                try:
                    operand = float(resolved)
                except (ValueError, TypeError):
                    return val
            try:
                n = float(val)
            except (ValueError, TypeError):
                return val
            if op == "add":
                return n + operand
            if op == "sub":
                return n - operand
            if op == "mul":
                return n * operand
            if op == "div":
                return n / operand if operand != 0 else val
            return val
        if t == "prepend":
            prefix = transform.get("value", "")
            return f"{prefix}{val}" if val is not None else None
        if t == "append":
            suffix = transform.get("value", "")
            return f"{val}{suffix}" if val is not None else None

        return val

    def _evaluate_expression(self, expr: str, ctx: WorkflowContext) -> Any:
        if not isinstance(expr, str):
            return expr
        return self._interpolate_string(expr, ctx)

    def _interpolate_string(self, template: str, ctx: WorkflowContext) -> str:
        def replacer(match: re.Match) -> str:  # type: ignore[type-arg]
            path = match.group(1).strip()
            val = self._resolve_value(path, ctx)
            return str(val) if val is not None else ""

        return re.sub(r"\{\{(.+?)\}\}", replacer, template)

    def _interpolate_dict(self, template: dict | list | str | Any, ctx: WorkflowContext) -> Any:
        if isinstance(template, dict):
            return {k: self._interpolate_dict(v, ctx) for k, v in template.items()}
        if isinstance(template, list):
            return [self._interpolate_dict(item, ctx) for item in template]
        if isinstance(template, str):
            if template.startswith("{{") and template.endswith("}}"):
                return self._resolve_value(template[2:-2].strip(), ctx)
            if "{{" in template:
                return self._interpolate_string(template, ctx)
        return template

    async def process_event(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        connector_name: str,
        event: str,
        event_data: dict[str, Any],
    ) -> list[WorkflowExecution]:
        workflows = await self.get_workflows_for_event(
            db, tenant_id, connector_name, event
        )
        await logger.ainfo(
            "workflow_event_received",
            connector=connector_name,
            event_name=event,
            tenant_id=str(tenant_id),
            matching_workflows=len(workflows),
            workflow_names=[w.name for w in workflows],
        )
        event_account = event_data.get("account_name")
        matched: list[Workflow] = []
        for wf in workflows:
            trigger_cred = _get_trigger_credential(wf.nodes)
            if trigger_cred and event_account and trigger_cred != event_account:
                continue

            trigger_filters = _get_trigger_filters(wf.nodes)
            if trigger_filters and not _passes_trigger_filters(trigger_filters, event_data):
                await logger.ainfo(
                    "workflow_trigger_filtered",
                    workflow_id=str(wf.id),
                    workflow_name=wf.name,
                    connector=connector_name,
                    event_name=event,
                )
                continue

            matched.append(wf)

        executions = []
        for wf in matched:
            execution = await self._execute_with_sync(db, wf, connector_name, event, event_data)
            executions.append(execution)
        return [e for e in executions if e is not None]

    async def _execute_with_sync(
        self,
        db: AsyncSession,
        workflow: Workflow,
        connector_name: str,
        event: str,
        event_data: dict[str, Any],
    ) -> WorkflowExecution | None:
        """Execute a workflow with optional sync state tracking."""
        sync_cfg = workflow.sync_config
        if not sync_cfg or not sync_cfg.get("enabled"):
            return await self.execute_workflow(db, workflow, event_data)

        from core.sync_state import (
            SyncDecision,
            SyncStateManager,
            compute_content_hash,
            resolve_entity_key,
        )

        key_field = sync_cfg.get("entity_key_field")
        if not key_field:
            return await self.execute_workflow(db, workflow, event_data)

        entity_key = resolve_entity_key(event_data, key_field)
        if not entity_key:
            return await self.execute_workflow(db, workflow, event_data)

        hash_fields = sync_cfg.get("content_hash_fields")
        content_hash = compute_content_hash(event_data, hash_fields)
        mode = sync_cfg.get("mode", "incremental")
        max_retries = sync_cfg.get("max_retries", 3)

        sync_mgr = SyncStateManager()

        if mode == "force":
            execution = await self.execute_workflow(db, workflow, event_data)
            await sync_mgr.record_success(
                db,
                tenant_id=workflow.tenant_id,
                workflow_id=workflow.id,
                source_connector=connector_name,
                source_event=event,
                entity_key=entity_key,
                content_hash=content_hash,
            )
            return execution

        check = await sync_mgr.should_sync(
            db, workflow.id, entity_key, content_hash, max_retries=max_retries,
        )

        if check.decision == SyncDecision.SKIP:
            await logger.ainfo(
                "sync_skipped",
                workflow_id=str(workflow.id),
                entity_key=entity_key,
                reason="already_synced_same_hash",
            )
            return None

        on_dup = sync_cfg.get("on_duplicate", "skip")
        if check.decision == SyncDecision.UPDATE and on_dup == "skip":
            await logger.ainfo(
                "sync_skipped",
                workflow_id=str(workflow.id),
                entity_key=entity_key,
                reason="duplicate_skip_policy",
            )
            return None

        execution = await self.execute_workflow(db, workflow, event_data)

        if execution.status == "success":
            await sync_mgr.record_success(
                db,
                tenant_id=workflow.tenant_id,
                workflow_id=workflow.id,
                source_connector=connector_name,
                source_event=event,
                entity_key=entity_key,
                content_hash=content_hash,
                ledger_id=check.ledger_id,
            )
        else:
            await sync_mgr.record_failure(
                db,
                tenant_id=workflow.tenant_id,
                workflow_id=workflow.id,
                source_connector=connector_name,
                source_event=event,
                entity_key=entity_key,
                content_hash=content_hash,
                error=execution.error or "unknown error",
                ledger_id=check.ledger_id,
            )

        return execution


_PII_PLACEHOLDER = "[RODO_REDACTED]"

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PESEL_RE = re.compile(r"\b\d{11}\b")
_NIP_RE = re.compile(r"\b\d{3}[-]?\d{3}[-]?\d{2}[-]?\d{2}\b")
_IBAN_RE = re.compile(
    r"\b[A-Z]{2}\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}\b"
)
_CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3}[\s.-]?\d{2,4}(?!\d)"
)
_IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

_PII_CLASSIFY_PROMPT = (
    "You are a GDPR/RODO compliance classifier. "
    "Given the following JSON field paths, return ONLY a JSON array of paths "
    "that may contain personal data (PII). "
    "PII includes: names, surnames, emails, phones, addresses, "
    "national IDs, bank accounts, birth dates, IP addresses, "
    "login credentials, biometric data, health data. "
    "Work in ANY language. Return [] if none found. "
    "Respond with ONLY the JSON array, no explanation.\n\n"
    "Field paths:\n{field_paths}"
)


def _collect_field_paths(data: Any, prefix: str = "", depth: int = 0) -> list[str]:
    """Collect all leaf-level field paths from a nested dict/list."""
    if depth > 15:
        return []
    paths: list[str] = []
    if isinstance(data, dict):
        for key in data:
            p = f"{prefix}.{key}" if prefix else key
            child = data[key]
            if isinstance(child, (dict, list)):
                paths.extend(_collect_field_paths(child, p, depth + 1))
            else:
                paths.append(p)
    elif isinstance(data, list) and data:
        paths.extend(_collect_field_paths(data[0], f"{prefix}[]", depth + 1))
    return paths


def _is_pii_value(value: Any) -> bool:
    """Detect PII by universal value patterns (language-independent)."""
    if not isinstance(value, str) or len(value) < 5 or len(value) > 500:
        return False
    if _EMAIL_RE.search(value):
        return True
    if _PESEL_RE.fullmatch(value.strip()):
        return True
    if _NIP_RE.fullmatch(value.strip().replace(" ", "")):
        return True
    if _IBAN_RE.search(value):
        return True
    if _IP_RE.fullmatch(value.strip()):
        return True
    v = re.sub(r"[\s\-]", "", value)
    if _CREDIT_CARD_RE.fullmatch(v) and len(v) >= 13:
        return True
    return False


def _redact_by_paths(data: Any, pii_paths: set[str], current: str = "", depth: int = 0) -> Any:
    """Redact fields whose path is in the PII set, plus value-based detection."""
    if depth > 20:
        return _PII_PLACEHOLDER
    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for key, value in data.items():
            p = f"{current}.{key}" if current else key
            if p in pii_paths:
                result[key] = [_PII_PLACEHOLDER] * len(value) if isinstance(value, list) else _PII_PLACEHOLDER
            elif _is_pii_value(value):
                result[key] = _PII_PLACEHOLDER
            else:
                result[key] = _redact_by_paths(value, pii_paths, p, depth + 1)
        return result
    if isinstance(data, list):
        arr_path = f"{current}[]"
        if arr_path in pii_paths:
            return [_PII_PLACEHOLDER] * len(data)
        return [_redact_by_paths(item, pii_paths, current, depth + 1) for item in data]
    if isinstance(data, str) and _is_pii_value(data):
        return _PII_PLACEHOLDER
    return data


async def _classify_pii_fields(
    field_paths: list[str],
    action_executor: ExecuteActionFn,
    tenant_id: Any,
    credential_name: str,
) -> set[str]:
    """Ask AI to classify which field paths contain PII. Only keys are sent, never values."""
    if not field_paths:
        return set()
    import json as _json

    prompt = _PII_CLASSIFY_PROMPT.format(field_paths=_json.dumps(field_paths))
    try:
        result = await action_executor(
            connector_name="ai-agent",
            action="agent.analyze",
            payload={
                "prompt": prompt,
                "data": {"_task": "field_classification", "field_count": len(field_paths)},
                "temperature": 0.0,
                "output_schema": {"pii_fields": "string[]"},
            },
            tenant_id=tenant_id,
            credential_name=credential_name,
        )
        ai_out = result
        if isinstance(ai_out, dict) and "result" in ai_out:
            ai_out = ai_out["result"]
        pii_list: list[str] = []
        if isinstance(ai_out, dict):
            pii_list = ai_out.get("pii_fields", [])
        elif isinstance(ai_out, list):
            pii_list = ai_out
        elif isinstance(ai_out, str):
            pii_list = _json.loads(ai_out)
        return {p for p in pii_list if isinstance(p, str) and p in set(field_paths)}
    except Exception:
        await logger.awarning("pii_classify_fallback", reason="AI classification failed, using value-only detection")
        return set()


async def _redact_pii(
    data: Any,
    action_executor: ExecuteActionFn | None,
    tenant_id: Any,
    credential_name: str,
) -> Any:
    """Two-layer PII redaction: AI classifies field names + regex detects value patterns."""
    pii_paths: set[str] = set()
    if action_executor:
        field_paths = _collect_field_paths(data)
        if field_paths:
            pii_paths = await _classify_pii_fields(
                field_paths, action_executor, tenant_id, credential_name
            )
    return _redact_by_paths(data, pii_paths)


def _get_trigger_credential(nodes: list[dict]) -> str | None:
    """Extract credential_name from the trigger node config."""
    for node in nodes:
        if node.get("type") == "trigger":
            cred = node.get("config", {}).get("credential_name")
            if cred and cred != "default":
                return cred
    return None


def _get_trigger_filters(nodes: list[dict]) -> dict | None:
    """Extract filter config from the trigger node."""
    for node in nodes:
        if node.get("type") == "trigger":
            return node.get("config", {}).get("filters")
    return None


def _evaluate_trigger_filter(
    condition: dict[str, Any],
    data: dict[str, Any],
) -> bool:
    """Evaluate a single filter condition against raw event data.

    Supports the same operators as the workflow condition node but operates
    on flat event data without requiring a WorkflowContext.
    """
    field = condition.get("field", "")
    op = condition.get("operator", "eq")
    expected = condition.get("value")

    actual = _get_nested(data, field)

    if op in ("equals", "eq"):
        try:
            if actual == expected:
                return True
        except TypeError:
            pass
        a, b = _coerce_types(actual, expected)
        try:
            return a == b
        except TypeError:
            return False
    elif op in ("not_equals", "neq"):
        try:
            return actual != expected
        except TypeError:
            return True
    elif op == "contains":
        return expected in actual if actual else False
    elif op == "not_contains":
        return expected not in actual if actual else True
    elif op == "starts_with":
        return str(actual).startswith(str(expected)) if actual else False
    elif op == "ends_with":
        return str(actual).endswith(str(expected)) if actual else False
    elif op == "gt":
        a, b = _coerce_types(actual, expected)
        try:
            return a > b
        except TypeError:
            return False
    elif op == "lt":
        a, b = _coerce_types(actual, expected)
        try:
            return a < b
        except TypeError:
            return False
    elif op == "gte":
        a, b = _coerce_types(actual, expected)
        try:
            return a >= b
        except TypeError:
            return False
    elif op == "lte":
        a, b = _coerce_types(actual, expected)
        try:
            return a <= b
        except TypeError:
            return False
    elif op == "exists":
        return actual is not None
    elif op == "not_exists":
        return actual is None
    elif op == "in":
        values = condition.get("values", expected if isinstance(expected, list) else [expected])
        return actual in values
    elif op == "not_in":
        values = condition.get("values", expected if isinstance(expected, list) else [expected])
        return actual not in values
    elif op == "regex":
        return bool(re.search(str(expected), str(actual))) if actual is not None else False
    elif op == "is_empty":
        return not actual
    elif op == "is_not_empty":
        return bool(actual)
    return False


def _passes_trigger_filters(
    filters: dict[str, Any],
    event_data: dict[str, Any],
) -> bool:
    """Evaluate trigger filter conditions against event data."""
    conditions = filters.get("conditions", [])
    if not conditions:
        return True
    logic = filters.get("logic", "and")
    results = [_evaluate_trigger_filter(c, event_data) for c in conditions]
    return all(results) if logic == "and" else any(results)


class WorkflowGraph:
    """In-memory representation of a workflow graph for traversal."""

    def __init__(self, nodes: list[dict], edges: list[dict]) -> None:
        self._nodes = {n["id"]: n for n in nodes}
        self._edges = edges
        self._adjacency: dict[str, list[dict]] = {}
        for edge in edges:
            src = edge["source"]
            if src not in self._adjacency:
                self._adjacency[src] = []
            self._adjacency[src].append(edge)

    def find_trigger(self) -> dict[str, Any] | None:
        for node in self._nodes.values():
            if node.get("type") == "trigger":
                return node
        return None

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        return self._nodes.get(node_id)

    def get_successors(
        self, node_id: str, handle: str | None = None
    ) -> list[dict[str, Any]]:
        edges = self._adjacency.get(node_id, [])
        result = []
        for edge in edges:
            if handle is not None:
                edge_handle = edge.get("sourceHandle", "default")
                if edge_handle != handle:
                    continue
            target = self._nodes.get(edge["target"])
            if target:
                result.append(target)
        return result


class WorkflowError(Exception):
    node_id: str | None = None


def _get_nested(data: dict | Any, key: str) -> Any:
    if "[]" in key:
        return _get_nested_array(data, key)
    parts = key.split(".")
    current = data
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


def _get_nested_array(data: dict | Any, key: str) -> Any:
    """Handle ``[]`` array iteration in field paths.

    ``positions[].product_symbol`` extracts ``product_symbol`` from every
    element of the ``positions`` array, returning a list of values.
    Nested ``[]`` (e.g. ``orders[].items[].sku``) is supported recursively.
    """
    bracket_pos = key.index("[]")
    array_path = key[:bracket_pos]
    rest = key[bracket_pos + 2:]
    if rest.startswith("."):
        rest = rest[1:]

    arr = _get_nested(data, array_path) if array_path else data
    if not isinstance(arr, list):
        return None

    if not rest:
        return arr

    return [_get_nested(item, rest) for item in arr]


def _set_nested(data: dict, key: str, value: Any, concat: bool = True) -> None:
    if "[]" in key:
        _set_nested_array(data, key, value)
        return
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    final_key = parts[-1]
    if concat and final_key in current:
        existing = current[final_key]
        if isinstance(existing, list):
            if isinstance(value, list):
                current[final_key] = existing + value
            else:
                current[final_key] = existing + [value]
        else:
            current[final_key] = f"{value} {existing}"
    else:
        current[final_key] = value


def _set_nested_array(data: dict, key: str, value: Any) -> None:
    """Handle ``[]`` array iteration when setting target fields.

    When ``value`` is a list, each element is assigned to the corresponding
    array item.  If the target array already exists, fields are merged into
    the existing objects by index so that multiple mapping rules can build
    up array items together (e.g. ``items[].sku`` + ``items[].qty``).
    """
    bracket_pos = key.index("[]")
    array_path = key[:bracket_pos]
    rest = key[bracket_pos + 2:]
    if rest.startswith("."):
        rest = rest[1:]

    parts = array_path.split(".") if array_path else []
    current: Any = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    arr_key = parts[-1] if parts else ""
    if not arr_key:
        return

    if arr_key not in current or not isinstance(current[arr_key], list):
        current[arr_key] = []
    arr = current[arr_key]

    if not isinstance(value, list):
        value = [value]

    while len(arr) < len(value):
        arr.append({})

    for i, v in enumerate(value):
        if rest:
            if not isinstance(arr[i], dict):
                arr[i] = {}
            _set_nested(arr[i], rest, v, concat=False)
        else:
            arr[i] = v


def _safe_truncate(value: Any, max_len: int = 2000) -> Any:
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len] + "..."
    if isinstance(value, dict):
        s = str(value)
        if len(s) > max_len:
            return {"_truncated": True, "_preview": s[:max_len]}
    return value


def _html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

"""Kafka Event Bridge — consumes events from Kafka topics and routes them
to the Workflow Engine and Flow Engine for all active tenants.

This bridges Kafka-based data sync (AGENTS.md section 2.3) with the
platform's event-driven workflow/flow execution.
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from pinquark_common.kafka import KafkaMessageConsumer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Any]


class KafkaEventBridge:
    """Consumes Kafka event envelopes and triggers matching workflows/flows."""

    _RECONNECT_BASE_DELAY = 2.0
    _RECONNECT_MAX_DELAY = 60.0

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        security_protocol: str,
        session_factory: SessionFactory,
        workflow_engine: Any,
        flow_engine: Any,
        registry: Any,
        execute_action_fn_factory: Callable[..., Coroutine[Any, Any, Any]] | None = None,
        *,
        sasl_mechanism: str = "PLAIN",
        sasl_username: str = "",
        sasl_password: str = "",
        ssl_cafile: str = "",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._topics = topics
        self._security_protocol = security_protocol
        self._sasl_mechanism = sasl_mechanism
        self._sasl_username = sasl_username
        self._sasl_password = sasl_password
        self._ssl_cafile = ssl_cafile
        self._session_factory = session_factory
        self._workflow_engine = workflow_engine
        self._flow_engine = flow_engine
        self._registry = registry
        self._execute_action_fn_factory = execute_action_fn_factory
        self._consumer: KafkaMessageConsumer | None = None
        self._task: asyncio.Task[None] | None = None
        self._stopping = False

        from core.credential_vault import CredentialVault

        self._vault = CredentialVault()

    def _build_sasl_args(self) -> dict[str, Any]:
        sasl_args: dict[str, Any] = {}
        if self._security_protocol != "PLAINTEXT":
            sasl_args["sasl_mechanism"] = self._sasl_mechanism
            if self._sasl_username:
                sasl_args["sasl_username"] = self._sasl_username
            if self._sasl_password:
                sasl_args["sasl_password"] = self._sasl_password
            if self._ssl_cafile:
                sasl_args["ssl_cafile"] = self._ssl_cafile
        return sasl_args

    async def start(self) -> None:
        if not self._topics:
            logger.warning("kafka_event_bridge: no topics configured, skipping start")
            return

        if self._security_protocol == "PLAINTEXT":
            logger.warning(
                "Kafka security protocol is PLAINTEXT — this is insecure and "
                "MUST NOT be used in production. Set KAFKA_SECURITY_PROTOCOL=SASL_SSL."
            )

        self._stopping = False
        await self._create_consumer_and_start()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(
            "kafka_event_bridge started, topics=%s, group=%s",
            self._topics,
            self._group_id,
        )

    async def _create_consumer_and_start(self) -> None:
        self._consumer = KafkaMessageConsumer(
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            topics=self._topics,
            security_protocol=self._security_protocol,
            **self._build_sasl_args(),
        )
        for topic in self._topics:
            self._consumer.register_handler(topic, self._handle_message)
        await self._consumer.start()

    async def stop(self) -> None:
        self._stopping = True
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._consumer:
            await self._consumer.stop()
        logger.info("kafka_event_bridge stopped")

    async def _consume_loop(self) -> None:
        """Consume with automatic reconnect on failure."""
        delay = self._RECONNECT_BASE_DELAY
        while not self._stopping:
            try:
                if self._consumer:
                    await self._consumer.consume()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "kafka_event_bridge consume loop crashed, reconnecting in %.0fs",
                    delay,
                )
                if self._stopping:
                    break
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._RECONNECT_MAX_DELAY)
                try:
                    if self._consumer:
                        await self._consumer.stop()
                    await self._create_consumer_and_start()
                    delay = self._RECONNECT_BASE_DELAY
                except Exception:
                    logger.exception("kafka_event_bridge reconnect failed")

    async def _handle_message(self, message: dict[str, Any], key: str | None) -> None:
        connector_name = message.get("connector_name", "")
        event = message.get("event", "")
        data = message.get("data", {})
        account_name = message.get("account_name", "")

        if not connector_name or not event:
            logger.warning(
                "kafka_event_bridge: message missing connector_name or event, key=%s",
                key,
            )
            return

        logger.info(
            "kafka_event_bridge processing event: connector=%s event=%s account=%s",
            connector_name,
            event,
            account_name,
        )

        from db.base import set_rls_bypass
        from db.models import Tenant

        async with self._session_factory() as db:
            await set_rls_bypass(db)
            target_tenant_id = data.get("_tenant_id")
            if target_tenant_id:
                import uuid as _uuid

                try:
                    tid = _uuid.UUID(str(target_tenant_id))
                except (ValueError, AttributeError):
                    logger.warning("kafka_event_bridge: invalid _tenant_id=%s", target_tenant_id)
                    return
                result = await db.execute(select(Tenant).where(Tenant.is_active.is_(True), Tenant.id == tid))
            else:
                result = await db.execute(select(Tenant).where(Tenant.is_active.is_(True)))
            tenants = list(result.scalars().all())

            if not tenants:
                logger.warning("kafka_event_bridge: no active tenants")
                return

            for tenant in tenants:
                try:
                    async with db.begin_nested():
                        await self._process_for_tenant(db, tenant, connector_name, event, data)
                except Exception:
                    logger.exception(
                        "kafka_event_bridge: tenant processing failed — DLQ event tenant=%s connector=%s event=%s key=%s",
                        tenant.id,
                        connector_name,
                        event,
                        key,
                    )

            await db.commit()

    async def _process_for_tenant(
        self,
        db: AsyncSession,
        tenant: Any,
        connector_name: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        from core.action_dispatcher import dispatch_action

        async def execute_action_for_flow(
            connector_name: str,
            action: str,
            payload: dict,
            tenant_id: Any,
            credential_name: str = "default",
        ) -> dict:
            credentials: dict[str, str] | None = None
            try:
                credentials = await self._vault.retrieve_all(
                    db, tenant_id, connector_name, credential_name=credential_name
                )
            except Exception:
                logger.warning(
                    "kafka_event_bridge: failed to retrieve credentials for connector=%s tenant=%s",
                    connector_name,
                    tenant_id,
                )
            return await dispatch_action(
                connector_name=connector_name,
                action=action,
                payload=payload,
                tenant_id=tenant_id,
                credentials=credentials,
                registry=self._registry,
            )

        try:
            workflow_executions = await self._workflow_engine.process_event(
                db=db,
                tenant_id=tenant.id,
                connector_name=connector_name,
                event=event,
                event_data=data,
            )
            if workflow_executions:
                logger.info(
                    "kafka_event_bridge: triggered %d workflow(s) for tenant=%s connector=%s event=%s",
                    len(workflow_executions),
                    tenant.id,
                    connector_name,
                    event,
                )
        except Exception:
            logger.exception(
                "kafka_event_bridge: workflow error tenant=%s connector=%s event=%s",
                tenant.id,
                connector_name,
                event,
            )

        try:
            flow_executions = await self._flow_engine.process_event(
                db=db,
                tenant_id=tenant.id,
                connector_name=connector_name,
                event=event,
                event_data=data,
                execute_action_fn=execute_action_for_flow,
            )
            if flow_executions:
                logger.info(
                    "kafka_event_bridge: triggered %d flow(s) for tenant=%s connector=%s event=%s",
                    len(flow_executions),
                    tenant.id,
                    connector_name,
                    event,
                )
        except Exception:
            logger.exception(
                "kafka_event_bridge: flow error tenant=%s connector=%s event=%s",
                tenant.id,
                connector_name,
                event,
            )

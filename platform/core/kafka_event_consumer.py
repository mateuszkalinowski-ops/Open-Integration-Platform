"""Kafka Event Bridge — consumes events from Kafka topics and routes them
to the Workflow Engine and Flow Engine for all active tenants.

This bridges Kafka-based data sync (AGENTS.md section 2.3) with the
platform's event-driven workflow/flow execution.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pinquark_common.kafka import KafkaMessageConsumer

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Any]


class KafkaEventBridge:
    """Consumes Kafka event envelopes and triggers matching workflows/flows."""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        security_protocol: str,
        session_factory: SessionFactory,
        workflow_engine: Any,
        flow_engine: Any,
        execute_action_fn_factory: Callable[..., Coroutine[Any, Any, Any]] | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._topics = topics
        self._security_protocol = security_protocol
        self._session_factory = session_factory
        self._workflow_engine = workflow_engine
        self._flow_engine = flow_engine
        self._execute_action_fn_factory = execute_action_fn_factory
        self._consumer: KafkaMessageConsumer | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if not self._topics:
            logger.warning("kafka_event_bridge: no topics configured, skipping start")
            return

        sasl_args: dict[str, Any] = {}
        if self._security_protocol != "PLAINTEXT":
            sasl_args["sasl_mechanism"] = "PLAIN"

        self._consumer = KafkaMessageConsumer(
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            topics=self._topics,
            security_protocol=self._security_protocol,
            **sasl_args,
        )
        self._consumer.register_handler("__default__", self._handle_message)

        for topic in self._topics:
            self._consumer.register_handler(topic, self._handle_message)

        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(
            "kafka_event_bridge started, topics=%s, group=%s",
            self._topics, self._group_id,
        )

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            await self._consumer.stop()
        logger.info("kafka_event_bridge stopped")

    async def _consume_loop(self) -> None:
        if not self._consumer:
            return
        try:
            await self._consumer.consume()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("kafka_event_bridge consume loop crashed")

    async def _handle_message(self, message: dict[str, Any], key: str | None) -> None:
        connector_name = message.get("connector_name", "")
        event = message.get("event", "")
        data = message.get("data", message)
        account_name = message.get("account_name", "")

        if not connector_name or not event:
            logger.warning(
                "kafka_event_bridge: message missing connector_name or event, key=%s",
                key,
            )
            return

        logger.info(
            "kafka_event_bridge processing event: connector=%s event=%s account=%s",
            connector_name, event, account_name,
        )

        from db.models import Tenant

        try:
            async with self._session_factory() as db:
                result = await db.execute(
                    select(Tenant).where(Tenant.is_active.is_(True))
                )
                tenants = list(result.scalars().all())

                if not tenants:
                    logger.warning("kafka_event_bridge: no active tenants")
                    return

                for tenant in tenants:
                    await self._process_for_tenant(db, tenant, connector_name, event, data)

                await db.commit()
        except Exception:
            logger.exception(
                "kafka_event_bridge: error processing event connector=%s event=%s",
                connector_name, event,
            )

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
            from core.credential_vault import CredentialVault
            from core.connector_registry import ConnectorRegistry
            from config import settings as platform_settings

            vault = CredentialVault()
            registry = ConnectorRegistry(platform_settings.connector_discovery_path)

            credentials: dict[str, str] | None = None
            try:
                credentials = await vault.retrieve_all(
                    db, tenant_id, connector_name, credential_name=credential_name
                )
            except Exception:
                pass
            return await dispatch_action(
                connector_name=connector_name,
                action=action,
                payload=payload,
                tenant_id=tenant_id,
                credentials=credentials,
                registry=registry,
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
                    len(workflow_executions), tenant.id, connector_name, event,
                )
        except Exception:
            logger.exception(
                "kafka_event_bridge: workflow error tenant=%s connector=%s event=%s",
                tenant.id, connector_name, event,
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
                    len(flow_executions), tenant.id, connector_name, event,
                )
        except Exception:
            logger.exception(
                "kafka_event_bridge: flow error tenant=%s connector=%s event=%s",
                tenant.id, connector_name, event,
            )

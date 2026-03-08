"""Kafka consumer with single-message and batch processing support."""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

MessageHandler = Callable[[dict[str, Any], str], Awaitable[None]]
BatchMessageHandler = Callable[[list[tuple[dict[str, Any], str]], str], Awaitable[None]]


class KafkaMessageConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        security_protocol: str = "SASL_SSL",
        sasl_mechanism: str = "PLAIN",
        sasl_username: str | None = None,
        sasl_password: str | None = None,
        ssl_cafile: str | None = None,
        max_poll_records: int = 500,
        fetch_max_bytes: int = 52_428_800,
        enable_auto_commit: bool = False,
    ):
        self._topics = topics
        self._max_poll_records = max_poll_records
        def _safe_value_deserializer(v: bytes) -> dict[str, Any] | None:
            try:
                return json.loads(v.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.error("Failed to deserialize Kafka message value: %s", exc)
                return None

        def _safe_key_deserializer(k: bytes | None) -> str | None:
            if k is None:
                return None
            try:
                return k.decode("utf-8")
            except UnicodeDecodeError:
                return k.hex()

        self._config: dict[str, Any] = {
            "bootstrap_servers": bootstrap_servers,
            "group_id": group_id,
            "auto_offset_reset": "earliest",
            "enable_auto_commit": enable_auto_commit,
            "max_poll_records": max_poll_records,
            "fetch_max_bytes": fetch_max_bytes,
            "value_deserializer": _safe_value_deserializer,
            "key_deserializer": _safe_key_deserializer,
        }
        if security_protocol != "PLAINTEXT":
            self._config["security_protocol"] = security_protocol
            self._config["sasl_mechanism"] = sasl_mechanism
            self._config["sasl_plain_username"] = sasl_username
            self._config["sasl_plain_password"] = sasl_password
        if ssl_cafile:
            self._config["ssl_cafile"] = ssl_cafile

        self._consumer: AIOKafkaConsumer | None = None
        self._handlers: dict[str, MessageHandler] = {}
        self._batch_handlers: dict[str, BatchMessageHandler] = {}

    def register_handler(self, topic: str, handler: MessageHandler) -> None:
        self._handlers[topic] = handler

    def register_batch_handler(self, topic: str, handler: BatchMessageHandler) -> None:
        self._batch_handlers[topic] = handler

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(*self._topics, **self._config)
        await self._consumer.start()
        logger.info(
            "Kafka consumer started, topics=%s, max_poll_records=%d",
            self._topics,
            self._max_poll_records,
        )

    async def stop(self) -> None:
        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(self) -> None:
        """Single-message consumption (backward compatible)."""
        if not self._consumer:
            raise RuntimeError("Consumer not started. Call start() first.")
        async for msg in self._consumer:
            topic = msg.topic
            if msg.value is None:
                logger.warning("Skipping poison message on topic=%s (deserialization failed)", topic)
                await self._consumer.commit()
                continue
            handler = self._handlers.get(topic)
            if handler:
                try:
                    await handler(msg.value, msg.key)
                except Exception:
                    logger.exception("Error processing message from topic=%s, offset will NOT be committed", topic)
                    continue
                await self._consumer.commit()
            else:
                logger.warning("No handler for topic=%s", topic)

    async def consume_batches(self, timeout_ms: int = 1000) -> None:
        """Batch consumption -- fetches up to max_poll_records at once."""
        if not self._consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        while True:
            batch = await self._consumer.getmany(timeout_ms=timeout_ms)
            if not batch:
                continue

            has_error = False
            for tp, messages in batch.items():
                topic = tp.topic
                batch_handler = self._batch_handlers.get(topic)

                if batch_handler:
                    items = [(msg.value, msg.key) for msg in messages]
                    try:
                        await batch_handler(items, topic)
                    except Exception:
                        logger.exception(
                            "Error processing batch from topic=%s, size=%d",
                            topic,
                            len(messages),
                        )
                        has_error = True
                        continue
                else:
                    handler = self._handlers.get(topic)
                    if handler:
                        for msg in messages:
                            try:
                                await handler(msg.value, msg.key)
                            except Exception:
                                logger.exception(
                                    "Error processing message from topic=%s", topic
                                )
                                has_error = True
                    else:
                        logger.warning("No handler for topic=%s", topic)
                        continue

            if not has_error:
                await self._consumer.commit()

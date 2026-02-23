"""Kafka producer with single-message and batch send, lz4 compression."""

import asyncio
import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


class KafkaMessageProducer:
    def __init__(
        self,
        bootstrap_servers: str,
        security_protocol: str = "SASL_SSL",
        sasl_mechanism: str = "PLAIN",
        sasl_username: str | None = None,
        sasl_password: str | None = None,
        ssl_cafile: str | None = None,
        compression_type: str = "lz4",
        linger_ms: int = 50,
        batch_size: int = 65_536,
        max_request_size: int = 10_485_760,
    ):
        self._bootstrap_servers = bootstrap_servers
        self._config: dict[str, Any] = {
            "bootstrap_servers": bootstrap_servers,
            "value_serializer": lambda v: json.dumps(v, default=str).encode("utf-8"),
            "key_serializer": lambda k: k.encode("utf-8") if k else None,
            "compression_type": compression_type,
            "linger_ms": linger_ms,
            "batch_size": batch_size,
            "max_request_size": max_request_size,
            "acks": "all",
        }
        if security_protocol != "PLAINTEXT":
            self._config["security_protocol"] = security_protocol
            self._config["sasl_mechanism"] = sasl_mechanism
            self._config["sasl_plain_username"] = sasl_username
            self._config["sasl_plain_password"] = sasl_password
        if ssl_cafile:
            self._config["ssl_cafile"] = ssl_cafile

        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(**self._config)
        await self._producer.start()
        logger.info("Kafka producer started: %s (compression=%s)", self._bootstrap_servers, self._config.get("compression_type"))

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def send(self, topic: str, value: dict, key: str | None = None) -> None:
        if not self._producer:
            raise RuntimeError("Producer not started. Call start() first.")
        await self._producer.send_and_wait(topic, value=value, key=key)
        logger.debug("Message sent to topic=%s key=%s", topic, key)

    async def send_batch(
        self,
        topic: str,
        messages: list[tuple[dict, str | None]],
    ) -> int:
        """Send multiple messages concurrently, returning the count of successful sends."""
        if not self._producer:
            raise RuntimeError("Producer not started. Call start() first.")

        futures = []
        for value, key in messages:
            fut = await self._producer.send(topic, value=value, key=key)
            futures.append(fut)

        results = await asyncio.gather(
            *[asyncio.ensure_future(_await_future(f)) for f in futures],
            return_exceptions=True,
        )

        succeeded = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - succeeded
        if failed:
            logger.warning(
                "Batch send to topic=%s: %d succeeded, %d failed",
                topic, succeeded, failed,
            )
        else:
            logger.debug("Batch send to topic=%s: %d messages", topic, succeeded)
        return succeeded


async def _await_future(fut: Any) -> Any:
    return await fut

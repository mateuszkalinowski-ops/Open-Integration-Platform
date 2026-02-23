"""Async circuit breaker for protecting external API calls.

States:
  CLOSED   -- requests pass through normally
  OPEN     -- requests fail immediately (CircuitBreakerOpen raised)
  HALF_OPEN -- one test request allowed; success resets, failure re-opens

Transitions:
  CLOSED -> OPEN: when failure_count >= failure_threshold within window
  OPEN -> HALF_OPEN: after reset_timeout_seconds
  HALF_OPEN -> CLOSED: on success
  HALF_OPEN -> OPEN: on failure
"""

from __future__ import annotations

import asyncio
import enum
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

T = TypeVar("T")

_cb_state_gauge = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["name"],
)
_cb_trips_total = Counter(
    "circuit_breaker_trips_total",
    "Times circuit breaker tripped open",
    ["name"],
)


class CircuitBreakerOpen(Exception):
    def __init__(self, name: str, remaining_seconds: float) -> None:
        self.name = name
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Circuit breaker '{name}' is OPEN, retry after {remaining_seconds:.1f}s"
        )


class _State(enum.Enum):
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout_seconds: float = 30.0,
        half_open_max_calls: int = 1,
        excluded_exceptions: tuple[type[Exception], ...] = (),
    ) -> None:
        self.name = name
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout_seconds
        self._half_open_max_calls = half_open_max_calls
        self._excluded_exceptions = excluded_exceptions

        self._state = _State.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        _cb_state_gauge.labels(name=name).set(0)

    @property
    def state(self) -> str:
        return self._state.name

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        async with self._lock:
            self._maybe_transition_to_half_open()
            self._check_state()

        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            if isinstance(exc, self._excluded_exceptions):
                raise
            await self._on_failure()
            raise
        else:
            await self._on_success()
            return result

    def _maybe_transition_to_half_open(self) -> None:
        if self._state == _State.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._reset_timeout:
                self._state = _State.HALF_OPEN
                self._half_open_calls = 0
                _cb_state_gauge.labels(name=self.name).set(2)
                logger.info("Circuit breaker '%s': OPEN -> HALF_OPEN", self.name)

    def _check_state(self) -> None:
        if self._state == _State.OPEN:
            remaining = self._reset_timeout - (time.monotonic() - self._last_failure_time)
            raise CircuitBreakerOpen(self.name, max(0, remaining))
        if self._state == _State.HALF_OPEN:
            if self._half_open_calls >= self._half_open_max_calls:
                remaining = self._reset_timeout - (time.monotonic() - self._last_failure_time)
                raise CircuitBreakerOpen(self.name, max(0, remaining))
            self._half_open_calls += 1

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == _State.HALF_OPEN:
                logger.info("Circuit breaker '%s': HALF_OPEN -> CLOSED", self.name)
            self._state = _State.CLOSED
            self._failure_count = 0
            _cb_state_gauge.labels(name=self.name).set(0)

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == _State.HALF_OPEN:
                self._state = _State.OPEN
                _cb_state_gauge.labels(name=self.name).set(1)
                _cb_trips_total.labels(name=self.name).inc()
                logger.warning("Circuit breaker '%s': HALF_OPEN -> OPEN", self.name)

            elif self._state == _State.CLOSED and self._failure_count >= self._failure_threshold:
                self._state = _State.OPEN
                _cb_state_gauge.labels(name=self.name).set(1)
                _cb_trips_total.labels(name=self.name).inc()
                logger.warning(
                    "Circuit breaker '%s': CLOSED -> OPEN (failures=%d)",
                    self.name,
                    self._failure_count,
                )

    async def reset(self) -> None:
        async with self._lock:
            self._state = _State.CLOSED
            self._failure_count = 0
            _cb_state_gauge.labels(name=self.name).set(0)

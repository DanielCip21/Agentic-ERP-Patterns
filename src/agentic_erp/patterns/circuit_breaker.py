"""Circuit breaker for platform agent resilience."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"  # Normal — calls flow through
    OPEN = "open"  # Tripped — calls blocked until recovery_timeout elapses
    HALF_OPEN = "half_open"  # Probing — one call allowed to test recovery


@dataclass
class CircuitBreaker:
    """Per-platform circuit breaker with three-state machine.

    State transitions::

        CLOSED ──(failures >= threshold)──► OPEN
        OPEN   ──(recovery_timeout elapsed)──► HALF_OPEN
        HALF_OPEN ──(success)──► CLOSED
        HALF_OPEN ──(failure)──► OPEN  (threshold resets to 1)

    Usage::

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

        if breaker.is_available:
            try:
                result = call_platform()
                breaker.record_success()
            except Exception:
                breaker.record_failure()
                raise
        else:
            # circuit is OPEN — skip or return cached value
    """

    failure_threshold: int = 3
    recovery_timeout: float = 60.0

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _failure_count: int = field(default=0, init=False, repr=False)
    _opened_at: float | None = field(default=None, init=False, repr=False)

    @property
    def state(self) -> CircuitState:
        """Current state, transitioning OPEN → HALF_OPEN if timeout elapsed."""
        if self._state is CircuitState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def is_available(self) -> bool:
        """True when the breaker allows calls (CLOSED or HALF_OPEN)."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def record_success(self) -> None:
        """Call after a successful platform response — resets to CLOSED."""
        self._failure_count = 0
        self._opened_at = None
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Call after a platform error — may trip the breaker to OPEN."""
        self._failure_count += 1
        if (
            self._state is CircuitState.HALF_OPEN
            or self._failure_count >= self.failure_threshold
        ):
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()

    def reset(self) -> None:
        """Force the breaker back to CLOSED — for manual recovery or tests."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None

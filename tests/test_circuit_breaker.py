"""Tests for the CircuitBreaker pattern."""

import time
from agentic_erp.patterns.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_available is True
        assert breaker.failure_count == 0

    def test_single_failure_stays_closed(self):
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

    def test_failures_below_threshold_stay_closed(self):
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 2

    def test_at_threshold_trips_to_open(self):
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert breaker.is_available is False

    def test_open_blocks_further_recording(self):
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        # Additional failures when OPEN don't change state
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    def test_open_transitions_to_half_open_after_timeout(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        # Force _opened_at to past the timeout
        breaker._opened_at = time.monotonic() - 61
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.is_available is True

    def test_success_in_half_open_resets_to_closed(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        # Force HALF_OPEN
        breaker._opened_at = time.monotonic() - 61
        _ = breaker.state  # trigger transition
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_failure_in_half_open_reopens(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        # Force HALF_OPEN
        breaker._opened_at = time.monotonic() - 61
        _ = breaker.state  # trigger transition
        assert breaker._state == CircuitState.HALF_OPEN
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    def test_reset_forces_closed(self):
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_available is True
        assert breaker.failure_count == 0

    def test_custom_threshold(self):
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert breaker.is_available is False

    def test_success_after_failures_clears_count(self):
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

    def test_state_property_returns_string_value(self):
        breaker = CircuitBreaker()
        assert breaker.state.value in ("closed", "open", "half_open")

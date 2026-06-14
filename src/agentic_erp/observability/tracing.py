"""Lightweight in-process tracer with thread-safe span collection."""

from __future__ import annotations

import json
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator


@dataclass
class Span:
    """A single unit of work within a trace."""

    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    parent_id: str | None = None
    start_time: float = field(default_factory=time.monotonic)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"  # "ok" | "error"

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.monotonic()
        self.status = status

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "duration_ms": round(self.duration_ms, 3) if self.duration_ms is not None else None,
            "status": self.status,
            "attributes": self.attributes,
        }


class Tracer:
    """Collects spans for all agent runs in the current process.

    Thread-safe: each thread maintains its own active trace/span context via
    ``threading.local``, so concurrent async agents don't clobber each other.

    Usage::

        from agentic_erp.observability.tracing import Tracer

        tracer = Tracer()

        with tracer.span("agent.run", agent="SalesforceCRMAgent") as span:
            with tracer.span("tool.call", tool="soql_query"):
                ...

        print(tracer.export_json())
        tracer.clear()
    """

    def __init__(self) -> None:
        self._spans: list[Span] = []
        self._lock = threading.Lock()
        self._local = threading.local()

    # --- Thread-local trace/span state ---

    def _get_trace_id(self) -> str | None:
        return getattr(self._local, "trace_id", None)

    def _set_trace_id(self, value: str | None) -> None:
        self._local.trace_id = value

    def _get_span_id(self) -> str | None:
        return getattr(self._local, "span_id", None)

    def _set_span_id(self, value: str | None) -> None:
        self._local.span_id = value

    # --- Public API ---

    def start_trace(self) -> str:
        """Begin a new trace on the current thread. Returns the trace_id."""
        trace_id = uuid.uuid4().hex
        self._set_trace_id(trace_id)
        self._set_span_id(None)
        return trace_id

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Generator[Span, None, None]:
        """Context manager that records a span within the current trace.

        Starts a new trace automatically if none is active on this thread.
        """
        if self._get_trace_id() is None:
            self.start_trace()

        s = Span(
            name=name,
            trace_id=self._get_trace_id(),  # type: ignore[arg-type]
            parent_id=self._get_span_id(),
            attributes=dict(attributes),
        )
        prev_span_id = self._get_span_id()
        self._set_span_id(s.span_id)
        try:
            yield s
            s.finish("ok")
        except Exception as exc:
            s.finish("error")
            s.attributes["error"] = str(exc)
            raise
        finally:
            with self._lock:
                self._spans.append(s)
            self._set_span_id(prev_span_id)

    def get_spans(self) -> list[Span]:
        """Return a snapshot of all collected spans."""
        with self._lock:
            return list(self._spans)

    def get_spans_for_trace(self, trace_id: str) -> list[Span]:
        """Return spans belonging to a specific trace."""
        with self._lock:
            return [s for s in self._spans if s.trace_id == trace_id]

    def clear(self) -> None:
        """Reset all collected spans and thread-local state."""
        with self._lock:
            self._spans.clear()
        self._set_trace_id(None)
        self._set_span_id(None)

    def export_json(self, indent: int = 2) -> str:
        """Serialise all spans to a JSON string."""
        return json.dumps([s.to_dict() for s in self.get_spans()], indent=indent)

    @property
    def span_count(self) -> int:
        with self._lock:
            return len(self._spans)

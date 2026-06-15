"""Shared server state and FastAPI dependency helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import Request

from agentic_erp.cache.response_cache import ResponseCache
from agentic_erp.observability.tracing import Tracer
from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator


@dataclass
class ServerState:
    """Holds shared singletons injected into every request handler."""

    orchestrator: LivePlatformOrchestrator
    cache: ResponseCache = field(
        default_factory=lambda: ResponseCache(default_ttl=300.0)
    )
    tracer: Tracer = field(default_factory=Tracer)


def get_state(request: Request) -> ServerState:
    """FastAPI dependency — pulls ServerState from app.state."""
    return request.app.state.server_state

"""FastAPI application factory for the Agentic ERP REST API.

Quickstart::

    from agentic_erp.server.app import create_app
    from agentic_erp.server.deps import ServerState
    from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator

    orchestrator = LivePlatformOrchestrator(salesforce_config=..., dynamics365_config=...)
    app = create_app(ServerState(orchestrator=orchestrator))

    # Run with: uvicorn agentic_erp.server.app:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from agentic_erp.server.deps import ServerState
from agentic_erp.server.routes.agents import router as agents_router
from agentic_erp.server.routes.cache import router as cache_router
from agentic_erp.server.routes.health import router as health_router
from agentic_erp.server.routes.orchestrator import router as orchestrator_router


def create_app(state: ServerState) -> FastAPI:
    """Build and return a configured FastAPI application.

    Parameters
    ----------
    state:
        Pre-built :class:`~agentic_erp.server.deps.ServerState` containing the
        orchestrator, cache, and tracer singletons shared across requests.
    """
    app = FastAPI(
        title="Agentic ERP API",
        description=(
            "REST interface for the Agentic ERP multi-platform orchestrator. "
            "Exposes per-platform agent runs, SSE streaming, multi-platform "
            "dispatch with synthesis, and cache/health observability."
        ),
        version="0.1.0",
    )
    app.state.server_state = state

    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(orchestrator_router)
    app.include_router(cache_router)

    return app

"""FastAPI application factory for the Agentic ERP REST API.

Quickstart::

    from agentic_erp.server.app import create_app
    from agentic_erp.server.deps import ServerState
    from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator

    orchestrator = LivePlatformOrchestrator(salesforce_config=..., dynamics365_config=...)
    app = create_app(
        ServerState(orchestrator=orchestrator),
        api_key="change-me",
        rate_limit_rpm=60,
    )

    # Run with: uvicorn agentic_erp.server.app:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from agentic_erp.server.deps import ServerState
from agentic_erp.server.middleware.auth import APIKeyMiddleware
from agentic_erp.server.middleware.rate_limit import RateLimiter, RateLimitMiddleware
from agentic_erp.server.routes.agents import router as agents_router
from agentic_erp.server.routes.cache import router as cache_router
from agentic_erp.server.routes.health import router as health_router
from agentic_erp.server.routes.orchestrator import router as orchestrator_router


def create_app(
    state: ServerState,
    api_key: str | None = None,
    rate_limit_rpm: int | None = None,
) -> FastAPI:
    """Build and return a configured FastAPI application.

    Parameters
    ----------
    state:
        Pre-built :class:`~agentic_erp.server.deps.ServerState` containing the
        orchestrator, cache, and tracer singletons shared across requests.
    api_key:
        When set, all non-exempt routes require the ``X-API-Key`` header to
        match this value.  Pass ``None`` to disable auth (development).
    rate_limit_rpm:
        Sliding-window request limit per key per minute.  Pass ``None`` to
        disable rate limiting (development).  When auth is also enabled, the
        rate-limit key is the ``X-API-Key`` value so each tenant has its own
        independent quota.
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

    # Middleware is applied in LIFO order: last added = outermost = first to run.
    # We want: auth → rate-limit → route handler.
    # So: add rate-limit first (innermost), then auth (outermost).
    if rate_limit_rpm is not None:
        limiter = RateLimiter(requests_per_minute=rate_limit_rpm)
        app.add_middleware(RateLimitMiddleware, limiter=limiter)

    if api_key is not None:
        app.add_middleware(APIKeyMiddleware, api_key=api_key)

    return app


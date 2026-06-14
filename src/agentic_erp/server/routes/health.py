"""GET /health — liveness + platform circuit-breaker status."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from agentic_erp.server.deps import ServerState, get_state
from agentic_erp.server.models import HealthResponse

router = APIRouter(tags=["health"])

State = Annotated[ServerState, Depends(get_state)]


@router.get("/health", response_model=HealthResponse)
async def health(state: State) -> HealthResponse:
    """Return liveness status and per-platform circuit-breaker state."""
    return HealthResponse(
        status="ok",
        configured_platforms=state.orchestrator.configured_platforms,
        platform_status=state.orchestrator.platform_status,
        cache_stats=state.cache.stats,
    )

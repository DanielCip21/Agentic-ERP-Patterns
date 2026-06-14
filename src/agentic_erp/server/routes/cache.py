"""GET /cache/stats, POST /cache/clear."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from agentic_erp.server.deps import ServerState, get_state
from agentic_erp.server.models import CacheClearResponse, CacheStatsResponse

router = APIRouter(prefix="/cache", tags=["cache"])

State = Annotated[ServerState, Depends(get_state)]


@router.get("/stats", response_model=CacheStatsResponse)
async def cache_stats(state: State) -> CacheStatsResponse:
    """Return hit/miss counters and current cache size."""
    return CacheStatsResponse(**state.cache.stats)


@router.post("/clear", response_model=CacheClearResponse)
async def cache_clear(state: State) -> CacheClearResponse:
    """Flush all cached entries and reset counters."""
    state.cache.clear()
    return CacheClearResponse(cleared=True)

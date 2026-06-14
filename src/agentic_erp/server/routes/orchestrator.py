"""POST /orchestrator/run  —  POST /orchestrator/synthesize."""

from __future__ import annotations

import asyncio
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from agentic_erp.server.deps import ServerState, get_state
from agentic_erp.server.models import (
    OrchestratorRunRequest,
    OrchestratorRunResponse,
    OrchestratorSynthesizeResponse,
)

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

State = Annotated[ServerState, Depends(get_state)]


@router.post("/run", response_model=OrchestratorRunResponse)
async def orchestrator_run(req: OrchestratorRunRequest, state: State) -> OrchestratorRunResponse:
    """Route *task* to matched platform agents and return per-platform responses.

    With ``parallel=true`` (default) agents run concurrently via ``run_async``.
    """
    t0 = time.monotonic()
    try:
        if req.parallel:
            results = await state.orchestrator.run_async(req.task)
        else:
            results = await asyncio.to_thread(state.orchestrator.run, req.task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return OrchestratorRunResponse(
        results=results,
        platforms=list(results.keys()),
        duration_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.post("/synthesize", response_model=OrchestratorSynthesizeResponse)
async def orchestrator_synthesize(
    req: OrchestratorRunRequest, state: State
) -> OrchestratorSynthesizeResponse:
    """Run across platforms then ask Claude to merge the responses into one answer.

    With ``parallel=true`` (default) platform agents run concurrently before synthesis.
    """
    t0 = time.monotonic()
    try:
        if req.parallel:
            platform_results = await state.orchestrator.run_async(req.task)
        else:
            platform_results = await asyncio.to_thread(state.orchestrator.run, req.task)

        synthesized = await state.orchestrator.run_and_synthesize_async(req.task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return OrchestratorSynthesizeResponse(
        result=synthesized,
        platform_results=platform_results,
        duration_ms=round((time.monotonic() - t0) * 1000, 2),
    )

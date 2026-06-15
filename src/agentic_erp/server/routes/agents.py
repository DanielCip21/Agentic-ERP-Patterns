"""POST /agents/{platform}/run  —  POST /agents/{platform}/stream (SSE)."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from agentic_erp.server.deps import ServerState, get_state
from agentic_erp.server.models import (
    AgentRunRequest,
    AgentRunResponse,
    AgentStreamRequest,
)

router = APIRouter(prefix="/agents", tags=["agents"])

State = Annotated[ServerState, Depends(get_state)]


@router.post("/{platform}/run", response_model=AgentRunResponse)
async def run_agent(
    platform: str, req: AgentRunRequest, state: State
) -> AgentRunResponse:
    """Run a single platform agent and return the complete response."""
    _check_platform(platform, state)
    t0 = time.monotonic()
    try:
        result = await asyncio.to_thread(
            state.orchestrator.run_platform, platform, req.message
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AgentRunResponse(
        platform=platform,
        result=result,
        duration_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.post("/{platform}/stream")
async def stream_agent(
    platform: str, req: AgentStreamRequest, state: State
) -> StreamingResponse:
    """Stream a platform agent response as Server-Sent Events.

    Each SSE event carries ``{"text": "<chunk>"}``; the final event is ``[DONE]``.
    """
    _check_platform(platform, state)

    async def _sse() -> AsyncGenerator[str, None]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _run_sync() -> None:
            try:
                for chunk in state.orchestrator.stream_platform(platform, req.message):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, f"[ERROR] {exc}")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        task = asyncio.ensure_future(asyncio.to_thread(_run_sync))
        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(_sse(), media_type="text/event-stream")


def _check_platform(platform: str, state: ServerState) -> None:
    if platform not in state.orchestrator.configured_platforms:
        raise HTTPException(
            status_code=404,
            detail=f"Platform {platform!r} not configured. "
            f"Available: {state.orchestrator.configured_platforms}",
        )

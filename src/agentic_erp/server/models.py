"""Pydantic request/response models for the ERP REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    message: str = Field(..., description="Natural-language task for the agent.")
    model: str | None = Field(None, description="Override the default Claude model.")


class AgentRunResponse(BaseModel):
    platform: str
    result: str
    duration_ms: float


class AgentStreamRequest(BaseModel):
    message: str = Field(..., description="Natural-language task for the agent.")


class OrchestratorRunRequest(BaseModel):
    task: str = Field(
        ..., description="Natural-language task routed to matched platforms."
    )
    parallel: bool = Field(
        True, description="Dispatch matched agents in parallel (async)."
    )


class OrchestratorRunResponse(BaseModel):
    results: dict[str, str]
    platforms: list[str]
    duration_ms: float


class OrchestratorSynthesizeResponse(BaseModel):
    result: str
    platform_results: dict[str, str]
    duration_ms: float


class HealthResponse(BaseModel):
    status: str
    configured_platforms: list[str]
    platform_status: dict[str, str]
    cache_stats: dict[str, Any] | None = None


class CacheStatsResponse(BaseModel):
    hits: int
    misses: int
    size: int
    hit_rate: float
    max_size: int
    default_ttl: float


class CacheClearResponse(BaseModel):
    cleared: bool


class ErrorResponse(BaseModel):
    detail: str

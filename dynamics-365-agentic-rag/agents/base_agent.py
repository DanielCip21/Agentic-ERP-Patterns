"""Base agent class for all Dynamics 365 RAG agents — provides tool-use loop and D365 client wiring."""
from __future__ import annotations

import json
from typing import Any

import anthropic

from config.settings import settings
from rag.vector_store import vector_store


class BaseD365Agent:
    """Foundation for all 10 Dynamics 365 Agentic RAG agents."""

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    def _rag_context(self, collection: str, query: str, k: int = 8) -> str:
        results = vector_store.query(collection, query, n_results=k)
        if not results:
            return "No historical RAG context available."
        lines = ["=== Historical CRM RAG Context ==="]
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] (similarity={r['similarity']}) {r['document']}")
        return "\n".join(lines)

    async def reason(self, system: str, prompt: str) -> str:
        """High-effort adaptive reasoning via Claude Opus 4.8."""
        async with self._client.messages.stream(
            model=settings.anthropic_model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"output_config": {"effort": "high"}},
        ) as stream:
            msg = await stream.get_final_message()
        parts = [b.text for b in msg.content if hasattr(b, "text")]
        return "\n".join(parts)

    async def quick_analyze(self, system: str, prompt: str) -> str:
        """Medium-effort analysis for lighter queries."""
        async with self._client.messages.stream(
            model=settings.anthropic_model,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"output_config": {"effort": "medium"}},
        ) as stream:
            msg = await stream.get_final_message()
        parts = [b.text for b in msg.content if hasattr(b, "text")]
        return "\n".join(parts)

    @staticmethod
    def fmt(data: Any) -> str:
        return json.dumps(data, indent=2, default=str)

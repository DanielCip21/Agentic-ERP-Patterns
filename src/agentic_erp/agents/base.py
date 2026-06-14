"""Base agent implementing the Claude tool-use agentic loop."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Generator

import anthropic

from agentic_erp.cache.response_cache import ResponseCache

if TYPE_CHECKING:
    from agentic_erp.observability.tracing import Tracer


class BaseERPAgent:
    """Drives a Claude model through a tool-use loop until the task is complete."""

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"
    MAX_ITERATIONS = 10

    def __init__(
        self,
        tools: list[dict],
        system_prompt: str,
        model: str = DEFAULT_MODEL,
        client: anthropic.Anthropic | None = None,
        tracer: "Tracer | None" = None,
        cache: "ResponseCache | None" = None,
        enable_prompt_cache: bool = False,
    ) -> None:
        self.tools = tools
        self.system_prompt = system_prompt
        self.model = model
        self.client = client or anthropic.Anthropic()
        self._tracer = tracer
        self._cache = cache
        self._enable_prompt_cache = enable_prompt_cache

    def run(self, user_message: str) -> str:
        """Run the agentic loop and return the final text response.

        Checks the response cache first (if configured). Wraps execution in a
        tracer span (if configured). Caches the result before returning.
        """
        if self._cache is not None:
            cache_key = ResponseCache.make_key(type(self).__name__, user_message)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        if self._tracer is not None:
            with self._tracer.span("agent.run", agent=type(self).__name__):
                result = self._run_loop(user_message)
        else:
            result = self._run_loop(user_message)

        if self._cache is not None:
            self._cache.set(cache_key, result)  # type: ignore[possibly-undefined]

        return result

    def _system_param(self) -> str | list:
        if self._enable_prompt_cache:
            return [{"type": "text", "text": self.system_prompt, "cache_control": {"type": "ephemeral"}}]
        return self.system_prompt

    def _extra_headers(self) -> dict:
        if self._enable_prompt_cache:
            return {"anthropic-beta": "prompt-caching-2024-07-31"}
        return {}

    def _run_loop(self, user_message: str) -> str:
        """Inner tool-use loop — extracted so run() can wrap it cleanly."""
        messages: list[dict] = [{"role": "user", "content": user_message}]
        extra_headers = self._extra_headers()

        for _ in range(self.MAX_ITERATIONS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._system_param(),
                tools=self.tools,
                messages=messages,
                **({"extra_headers": extra_headers} if extra_headers else {}),
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                return ""

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        if self._tracer is not None:
                            with self._tracer.span("tool.call", tool=block.name):
                                result = self._dispatch_tool(block.name, block.input)
                        else:
                            result = self._dispatch_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result),
                            }
                        )
                messages.append({"role": "user", "content": tool_results})

        raise RuntimeError("Agent exceeded maximum iterations without completing the task.")

    def stream(self, user_message: str) -> Generator[str, None, None]:
        """Stream the final text response token by token.

        Tool calls are processed synchronously without streaming — only the
        final assistant text turn is yielded chunk by chunk as it arrives.

        Usage::

            for chunk in agent.stream("List active orders"):
                print(chunk, end="", flush=True)
        """
        messages: list[dict] = [{"role": "user", "content": user_message}]
        extra_headers = self._extra_headers()

        for _ in range(self.MAX_ITERATIONS):
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self._system_param(),
                tools=self.tools,
                messages=messages,
                **({"extra_headers": extra_headers} if extra_headers else {}),
            ) as stream:
                for text_chunk in stream.text_stream:
                    yield text_chunk
                final = stream.get_final_message()

            messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason == "end_turn":
                return

            if final.stop_reason == "tool_use":
                tool_results = []
                for block in final.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        result = self._dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})

        raise RuntimeError("Agent exceeded maximum iterations without completing the task.")

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        """Override in subclasses to handle tool calls."""
        raise NotImplementedError(f"Tool not implemented: {name}")

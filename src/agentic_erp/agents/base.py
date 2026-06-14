"""Base agent implementing the Claude tool-use agentic loop."""

from __future__ import annotations

import json
from typing import Any, Generator

import anthropic


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
    ) -> None:
        self.tools = tools
        self.system_prompt = system_prompt
        self.model = model
        self.client = client or anthropic.Anthropic()

    def run(self, user_message: str) -> str:
        """Run the agentic loop and return the final text response."""
        messages: list[dict] = [{"role": "user", "content": user_message}]

        for _ in range(self.MAX_ITERATIONS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages,
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

        for _ in range(self.MAX_ITERATIONS):
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages,
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

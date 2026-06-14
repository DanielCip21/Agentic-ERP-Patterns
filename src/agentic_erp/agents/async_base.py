"""Async Claude tool-use loop using AsyncAnthropic."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import anthropic


class AsyncBaseERPAgent:
    """Async version of BaseERPAgent — awaits Claude API calls end-to-end.

    Subclasses implement ``_dispatch_tool`` as ``async def`` so connector I/O
    can also be awaited when using async HTTP clients.

    Usage::

        class MyAgent(AsyncBaseERPAgent):
            async def _dispatch_tool(self, name, inputs):
                if name == "search":
                    return await self._connector.search(inputs["query"])

        agent = MyAgent(tools=[...], system_prompt="...")
        result = await agent.run("Find all open orders")
    """

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"
    MAX_ITERATIONS = 10

    def __init__(
        self,
        tools: list[dict],
        system_prompt: str,
        model: str = DEFAULT_MODEL,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        self.tools = tools
        self.system_prompt = system_prompt
        self.model = model
        self.client = client or anthropic.AsyncAnthropic()

    async def run(self, user_message: str) -> str:
        """Drive the async tool-use loop and return the final text response."""
        messages: list[dict] = [{"role": "user", "content": user_message}]

        for _ in range(self.MAX_ITERATIONS):
            response = await self.client.messages.create(
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
                        result = await self._dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})

        raise RuntimeError("Agent exceeded maximum iterations without completing the task.")

    async def astream(self, user_message: str) -> AsyncGenerator[str, None]:
        """Async streaming version — yields text tokens as they arrive from Claude.

        Tool calls are awaited silently; only the final text turn is streamed.

        Usage::

            async for chunk in agent.astream("Summarise open orders"):
                print(chunk, end="", flush=True)
        """
        messages: list[dict] = [{"role": "user", "content": user_message}]

        for _ in range(self.MAX_ITERATIONS):
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages,
            ) as stream:
                async for text_chunk in stream.text_stream:
                    yield text_chunk
                final = await stream.get_final_message()

            messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason == "end_turn":
                return

            if final.stop_reason == "tool_use":
                tool_results = []
                for block in final.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        result = await self._dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})

        raise RuntimeError("Agent exceeded maximum iterations without completing the task.")

    async def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        """Override in subclasses to handle tool calls."""
        raise NotImplementedError(f"Tool not implemented: {name}")

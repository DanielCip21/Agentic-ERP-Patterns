"""Tests for AsyncBaseERPAgent — all Claude calls are AsyncMock."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agentic_erp.agents.async_base import AsyncBaseERPAgent


# ---------------------------------------------------------------------------
# Concrete subclass used in tests
# ---------------------------------------------------------------------------

class _GreetAgent(AsyncBaseERPAgent):
    """Minimal agent that handles one tool: greet."""

    async def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        if name == "greet":
            return {"message": f"Hello, {inputs.get('name', 'World')}!"}
        return {"error": f"unknown tool: {name}"}


_GREET_TOOL = {
    "name": "greet",
    "description": "Greet someone by name.",
    "input_schema": {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text_response(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


def _tool_response(name: str, inputs: dict, tool_id: str = "tu_001") -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.input = inputs
    block.id = tool_id
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    resp.content = [block]
    return resp


def _make_client(*side_effects) -> MagicMock:
    client = MagicMock()
    client.messages.create = AsyncMock(side_effect=list(side_effects))
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAsyncBaseERPAgentEndTurn:
    def test_end_turn_immediately_returns_text(self):
        client = _make_client(_text_response("all done"))
        agent = _GreetAgent(tools=[_GREET_TOOL], system_prompt="s", client=client)
        result = asyncio.run(agent.run("Hello"))
        assert result == "all done"

    def test_end_turn_with_no_text_block_returns_empty(self):
        resp = MagicMock()
        resp.stop_reason = "end_turn"
        resp.content = []
        client = _make_client(resp)
        agent = _GreetAgent(tools=[], system_prompt="s", client=client)
        result = asyncio.run(agent.run("Hello"))
        assert result == ""

    def test_messages_create_called_once_on_end_turn(self):
        client = _make_client(_text_response("done"))
        agent = _GreetAgent(tools=[_GREET_TOOL], system_prompt="s", client=client)
        asyncio.run(agent.run("Hello"))
        client.messages.create.assert_awaited_once()


class TestAsyncBaseERPAgentToolUse:
    def test_single_tool_call_then_end_turn(self):
        client = _make_client(
            _tool_response("greet", {"name": "Alice"}),
            _text_response("Hello, Alice!"),
        )
        agent = _GreetAgent(tools=[_GREET_TOOL], system_prompt="s", client=client)
        result = asyncio.run(agent.run("Greet Alice"))
        assert result == "Hello, Alice!"
        assert client.messages.create.await_count == 2

    def test_tool_result_injected_into_messages(self):
        client = _make_client(
            _tool_response("greet", {"name": "Bob"}, tool_id="tu_99"),
            _text_response("Hi Bob"),
        )
        agent = _GreetAgent(tools=[_GREET_TOOL], system_prompt="s", client=client)
        asyncio.run(agent.run("Greet Bob"))

        # Messages list is a live reference; after run() it has 4 entries:
        # [user_prompt, assistant(tool_use), user(tool_result), assistant(text)]
        # The tool_result turn is the third entry (index 2 / second-to-last).
        second_call_messages = client.messages.create.await_args_list[1][1]["messages"]
        tool_result_turn = second_call_messages[-2]
        assert tool_result_turn["role"] == "user"
        tool_result = tool_result_turn["content"][0]
        assert tool_result["tool_use_id"] == "tu_99"
        assert "Hello, Bob!" in tool_result["content"]

    def test_two_sequential_tool_calls(self):
        client = _make_client(
            _tool_response("greet", {"name": "X"}, "tu_1"),
            _tool_response("greet", {"name": "Y"}, "tu_2"),
            _text_response("Done"),
        )
        agent = _GreetAgent(tools=[_GREET_TOOL], system_prompt="s", client=client)
        result = asyncio.run(agent.run("Greet X then Y"))
        assert result == "Done"
        assert client.messages.create.await_count == 3


class TestAsyncBaseERPAgentErrors:
    def test_exceeds_max_iterations_raises(self):
        client = MagicMock()
        client.messages.create = AsyncMock(
            return_value=_tool_response("greet", {"name": "loop"})
        )
        agent = _GreetAgent(tools=[_GREET_TOOL], system_prompt="s", client=client)
        agent.MAX_ITERATIONS = 3

        with pytest.raises(RuntimeError, match="exceeded maximum iterations"):
            asyncio.run(agent.run("loop forever"))

    def test_dispatch_unknown_tool_returns_error_dict(self):
        client = _make_client(
            _tool_response("unknown_tool", {}, "tu_x"),
            _text_response("handled"),
        )
        agent = _GreetAgent(tools=[], system_prompt="s", client=client)
        result = asyncio.run(agent.run("call unknown"))
        assert result == "handled"


class TestAsyncBaseERPAgentDefaults:
    def test_default_model(self):
        agent = _GreetAgent(tools=[], system_prompt="s", client=MagicMock())
        assert agent.model == AsyncBaseERPAgent.DEFAULT_MODEL

    def test_custom_model(self):
        agent = _GreetAgent(
            tools=[], system_prompt="s", model="claude-opus-4-8", client=MagicMock()
        )
        assert agent.model == "claude-opus-4-8"

    def test_system_prompt_passed_to_claude(self):
        client = _make_client(_text_response("ok"))
        agent = _GreetAgent(tools=[], system_prompt="Be terse.", client=client)
        asyncio.run(agent.run("hi"))
        call_kwargs = client.messages.create.await_args[1]
        assert call_kwargs["system"] == "Be terse."

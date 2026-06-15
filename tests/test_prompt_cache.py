"""Tests for prompt-cache optimisation on BaseERPAgent and AsyncBaseERPAgent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agentic_erp.agents.async_base import AsyncBaseERPAgent
from agentic_erp.agents.base import BaseERPAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sync_agent(enable_prompt_cache: bool) -> tuple[BaseERPAgent, MagicMock]:
    mock_client = MagicMock()
    end_response = MagicMock()
    end_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "done"
    end_response.content = [text_block]
    mock_client.messages.create.return_value = end_response

    agent = BaseERPAgent(
        tools=[],
        system_prompt="You are a helpful ERP assistant.",
        client=mock_client,
        enable_prompt_cache=enable_prompt_cache,
    )
    return agent, mock_client


def _make_async_agent(enable_prompt_cache: bool) -> tuple[AsyncBaseERPAgent, MagicMock]:
    mock_client = MagicMock()
    end_response = MagicMock()
    end_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "done"
    end_response.content = [text_block]
    mock_client.messages.create = AsyncMock(return_value=end_response)

    agent = AsyncBaseERPAgent(
        tools=[],
        system_prompt="You are a helpful ERP assistant.",
        client=mock_client,
        enable_prompt_cache=enable_prompt_cache,
    )
    return agent, mock_client


# ---------------------------------------------------------------------------
# BaseERPAgent — prompt cache disabled (default)
# ---------------------------------------------------------------------------


class TestBaseERPAgentPromptCacheDisabled:
    def test_system_is_string_by_default(self):
        agent, mock_client = _make_sync_agent(enable_prompt_cache=False)
        agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert isinstance(kwargs["system"], str)

    def test_no_extra_headers_by_default(self):
        agent, mock_client = _make_sync_agent(enable_prompt_cache=False)
        agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert "extra_headers" not in kwargs

    def test_default_enable_prompt_cache_is_false(self):
        mock_client = MagicMock()
        resp = MagicMock(stop_reason="end_turn", content=[MagicMock(text="x")])
        mock_client.messages.create.return_value = resp
        agent = BaseERPAgent(tools=[], system_prompt="hi", client=mock_client)
        assert agent._enable_prompt_cache is False


# ---------------------------------------------------------------------------
# BaseERPAgent — prompt cache enabled
# ---------------------------------------------------------------------------


class TestBaseERPAgentPromptCacheEnabled:
    def test_system_sent_as_list(self):
        agent, mock_client = _make_sync_agent(enable_prompt_cache=True)
        agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert isinstance(kwargs["system"], list)

    def test_system_block_has_cache_control(self):
        agent, mock_client = _make_sync_agent(enable_prompt_cache=True)
        agent.run("hello")
        system = mock_client.messages.create.call_args.kwargs["system"]
        assert system[0]["cache_control"] == {"type": "ephemeral"}

    def test_system_block_text_matches_prompt(self):
        agent, mock_client = _make_sync_agent(enable_prompt_cache=True)
        agent.run("hello")
        system = mock_client.messages.create.call_args.kwargs["system"]
        assert system[0]["text"] == "You are a helpful ERP assistant."
        assert system[0]["type"] == "text"

    def test_beta_header_present(self):
        agent, mock_client = _make_sync_agent(enable_prompt_cache=True)
        agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert "extra_headers" in kwargs
        assert kwargs["extra_headers"]["anthropic-beta"] == "prompt-caching-2024-07-31"

    def test_prompt_cache_applied_on_every_loop_iteration(self):
        """Verify cache_control is passed even when tool calls occur mid-loop."""
        mock_client = MagicMock()

        tool_response = MagicMock()
        tool_response.stop_reason = "tool_use"
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "t1"
        tool_block.name = "noop"
        tool_block.input = {}
        tool_response.content = [tool_block]

        end_response = MagicMock()
        end_response.stop_reason = "end_turn"
        end_response.content = [MagicMock(text="done")]

        mock_client.messages.create.side_effect = [tool_response, end_response]

        agent = BaseERPAgent(
            tools=[
                {
                    "name": "noop",
                    "description": "no-op",
                    "input_schema": {"type": "object", "properties": {}},
                }
            ],
            system_prompt="You are helpful.",
            client=mock_client,
            enable_prompt_cache=True,
        )
        agent._dispatch_tool = lambda name, inputs: {}
        agent.run("do something")

        for call in mock_client.messages.create.call_args_list:
            kwargs = call.kwargs
            assert isinstance(kwargs["system"], list)
            assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


# ---------------------------------------------------------------------------
# AsyncBaseERPAgent — prompt cache
# ---------------------------------------------------------------------------


class TestAsyncBaseERPAgentPromptCache:
    @pytest.mark.asyncio
    async def test_system_is_string_when_disabled(self):
        agent, mock_client = _make_async_agent(enable_prompt_cache=False)
        await agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert isinstance(kwargs["system"], str)

    @pytest.mark.asyncio
    async def test_system_sent_as_list_when_enabled(self):
        agent, mock_client = _make_async_agent(enable_prompt_cache=True)
        await agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert isinstance(kwargs["system"], list)
        assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}

    @pytest.mark.asyncio
    async def test_beta_header_present_when_enabled(self):
        agent, mock_client = _make_async_agent(enable_prompt_cache=True)
        await agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs["extra_headers"]["anthropic-beta"] == "prompt-caching-2024-07-31"

    @pytest.mark.asyncio
    async def test_no_extra_headers_when_disabled(self):
        agent, mock_client = _make_async_agent(enable_prompt_cache=False)
        await agent.run("hello")
        kwargs = mock_client.messages.create.call_args.kwargs
        assert "extra_headers" not in kwargs


# ---------------------------------------------------------------------------
# _system_param / _extra_headers helpers
# ---------------------------------------------------------------------------


class TestHelperMethods:
    def test_system_param_disabled(self):
        mock_client = MagicMock()
        agent = BaseERPAgent(tools=[], system_prompt="hello", client=mock_client)
        assert agent._system_param() == "hello"

    def test_system_param_enabled(self):
        mock_client = MagicMock()
        agent = BaseERPAgent(
            tools=[],
            system_prompt="hello",
            client=mock_client,
            enable_prompt_cache=True,
        )
        result = agent._system_param()
        assert result == [
            {"type": "text", "text": "hello", "cache_control": {"type": "ephemeral"}}
        ]

    def test_extra_headers_disabled(self):
        mock_client = MagicMock()
        agent = BaseERPAgent(tools=[], system_prompt="hi", client=mock_client)
        assert agent._extra_headers() == {}

    def test_extra_headers_enabled(self):
        mock_client = MagicMock()
        agent = BaseERPAgent(
            tools=[], system_prompt="hi", client=mock_client, enable_prompt_cache=True
        )
        assert agent._extra_headers() == {"anthropic-beta": "prompt-caching-2024-07-31"}

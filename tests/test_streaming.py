"""Tests for BaseERPAgent.stream() and AsyncBaseERPAgent.astream()."""

import asyncio
from typing import Any
from unittest.mock import MagicMock, AsyncMock

import pytest

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.agents.async_base import AsyncBaseERPAgent


# ---------------------------------------------------------------------------
# Concrete subclasses
# ---------------------------------------------------------------------------


class _SyncAgent(BaseERPAgent):
    def _dispatch_tool(self, name: str, inputs: dict) -> Any:
        return {"result": f"tool:{name}"}


class _AsyncAgent(AsyncBaseERPAgent):
    async def _dispatch_tool(self, name: str, inputs: dict) -> Any:
        return {"result": f"async_tool:{name}"}


# ---------------------------------------------------------------------------
# Sync stream helpers
# ---------------------------------------------------------------------------


def _make_sync_stream_mock(text_chunks, stop_reason="end_turn", tool_blocks=None):
    """Build a mock that satisfies ``with client.messages.stream(...) as s``."""
    final_content = []
    if tool_blocks:
        final_content.extend(tool_blocks)
    else:
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "".join(text_chunks)
        final_content.append(text_block)

    final_message = MagicMock()
    final_message.stop_reason = stop_reason
    final_message.content = final_content

    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter(text_chunks)
    stream.get_final_message.return_value = final_message

    client = MagicMock()
    client.messages.stream.return_value = stream
    return client, stream, final_message


# ---------------------------------------------------------------------------
# Async stream helpers
# ---------------------------------------------------------------------------


class _AsyncIter:
    def __init__(self, items):
        self._items = list(items)
        self._idx = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._idx >= len(self._items):
            raise StopAsyncIteration
        val = self._items[self._idx]
        self._idx += 1
        return val


def _make_async_stream_mock(text_chunks, stop_reason="end_turn"):
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "".join(text_chunks)

    final_message = MagicMock()
    final_message.stop_reason = stop_reason
    final_message.content = [text_block]

    stream = MagicMock()
    stream.__aenter__ = AsyncMock(return_value=stream)
    stream.__aexit__ = AsyncMock(return_value=False)
    stream.text_stream = _AsyncIter(text_chunks)
    stream.get_final_message = AsyncMock(return_value=final_message)

    client = MagicMock()
    client.messages.stream.return_value = stream
    return client, stream


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestSyncStream:
    def _make_agent(self, client):
        return _SyncAgent(tools=[], system_prompt="test", client=client)

    def test_yields_text_chunks(self):
        client, _, _ = _make_sync_stream_mock(["Hello", " ", "World"])
        agent = self._make_agent(client)
        result = list(agent.stream("hi"))
        assert result == ["Hello", " ", "World"]

    def test_joined_chunks_form_complete_response(self):
        client, _, _ = _make_sync_stream_mock(["Hello", " ", "World"])
        agent = self._make_agent(client)
        assert "".join(agent.stream("hi")) == "Hello World"

    def test_empty_stream_yields_nothing(self):
        client, _, _ = _make_sync_stream_mock([])
        agent = self._make_agent(client)
        assert list(agent.stream("hi")) == []

    def test_tool_use_then_end_turn(self):
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "echo"
        tool_block.input = {}
        tool_block.id = "tu_1"

        # First stream: stop_reason=tool_use, no text chunks
        first_client, first_stream, first_final = _make_sync_stream_mock(
            [], stop_reason="tool_use", tool_blocks=[tool_block]
        )
        # Second stream: stop_reason=end_turn, yields "done"
        _, second_stream, _ = _make_sync_stream_mock(["done"], stop_reason="end_turn")

        # Wire both streams onto the same client
        client = first_client
        client.messages.stream.side_effect = [first_stream, second_stream]

        agent = self._make_agent(client)
        result = list(agent.stream("hi"))

        assert "done" in result
        assert client.messages.stream.call_count == 2

    def test_exceeds_max_iterations_raises(self):
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "echo"
        tool_block.input = {}
        tool_block.id = "tu_loop"

        def _always_tool_stream():
            _, stream, _ = _make_sync_stream_mock(
                [], stop_reason="tool_use", tool_blocks=[tool_block]
            )
            return stream

        client = MagicMock()
        client.messages.stream.side_effect = lambda **_: _always_tool_stream()

        agent = self._make_agent(client)
        agent.MAX_ITERATIONS = 2

        with pytest.raises(RuntimeError):
            list(agent.stream("hi"))


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


async def _collect(agent, msg):
    chunks = []
    async for chunk in agent.astream(msg):
        chunks.append(chunk)
    return chunks


class TestAsyncStream:
    def _make_agent(self, client):
        return _AsyncAgent(tools=[], system_prompt="test", client=client)

    def test_yields_text_chunks_async(self):
        client, _ = _make_async_stream_mock(["Hi", " there"])
        agent = self._make_agent(client)
        result = asyncio.run(_collect(agent, "hi"))
        assert result == ["Hi", " there"]

    def test_joined_chunks_async(self):
        client, _ = _make_async_stream_mock(["Hi", " there"])
        agent = self._make_agent(client)
        result = asyncio.run(_collect(agent, "hi"))
        assert "".join(result) == "Hi there"

    def test_empty_async_stream_yields_nothing(self):
        client, _ = _make_async_stream_mock([])
        agent = self._make_agent(client)
        result = asyncio.run(_collect(agent, "hi"))
        assert result == []

    def test_tool_use_then_end_turn_async(self):
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "echo"
        tool_block.input = {}
        tool_block.id = "tu_1"

        # First async stream: stop_reason=tool_use, no text
        first_text_block = MagicMock()
        first_text_block.type = "text"
        first_text_block.text = ""

        first_final = MagicMock()
        first_final.stop_reason = "tool_use"
        first_final.content = [tool_block]

        first_stream = MagicMock()
        first_stream.__aenter__ = AsyncMock(return_value=first_stream)
        first_stream.__aexit__ = AsyncMock(return_value=False)
        first_stream.text_stream = _AsyncIter([])
        first_stream.get_final_message = AsyncMock(return_value=first_final)

        # Second async stream: stop_reason=end_turn, yields "done"
        second_client, second_stream = _make_async_stream_mock(
            ["done"], stop_reason="end_turn"
        )

        client = MagicMock()
        client.messages.stream.side_effect = [first_stream, second_stream]

        agent = self._make_agent(client)
        result = asyncio.run(_collect(agent, "hi"))

        assert "done" in result
        assert client.messages.stream.call_count == 2

    def test_exceeds_max_iterations_raises_async(self):
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "echo"
        tool_block.input = {}
        tool_block.id = "tu_loop"

        def _always_tool_stream():
            tool_final = MagicMock()
            tool_final.stop_reason = "tool_use"
            tool_final.content = [tool_block]

            stream = MagicMock()
            stream.__aenter__ = AsyncMock(return_value=stream)
            stream.__aexit__ = AsyncMock(return_value=False)
            stream.text_stream = _AsyncIter([])
            stream.get_final_message = AsyncMock(return_value=tool_final)
            return stream

        client = MagicMock()
        client.messages.stream.side_effect = lambda **_: _always_tool_stream()

        agent = self._make_agent(client)
        agent.MAX_ITERATIONS = 2

        with pytest.raises(RuntimeError):
            asyncio.run(_collect(agent, "hi"))

"""Tests showing BaseERPAgent with tracer and cache wired in, plus connector GET caching."""

from unittest.mock import MagicMock

import httpx
import respx

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.cache.response_cache import ResponseCache
from agentic_erp.connectors.base import BaseHTTPConnector
from agentic_erp.observability.tracing import Tracer


# ---------------------------------------------------------------------------
# Concrete agent
# ---------------------------------------------------------------------------


class _EchoAgent(BaseERPAgent):
    def _dispatch_tool(self, name, inputs):
        return {"echo": inputs.get("text", "")}


# ---------------------------------------------------------------------------
# Mock response helpers
# ---------------------------------------------------------------------------


def _text_resp(text):
    block = MagicMock()
    block.text = text
    block.type = "text"
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


def _tool_resp(name, inputs, tool_id="tu_1"):
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.input = inputs
    block.id = tool_id
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    resp.content = [block]
    return resp


# ---------------------------------------------------------------------------
# TestAgentWithTracer
# ---------------------------------------------------------------------------


class TestAgentWithTracer:
    def _make_agent(self, tracer=None, cache=None):
        client = MagicMock()
        client.messages.create.return_value = _text_resp("done")
        agent = _EchoAgent(
            tools=[],
            system_prompt="test",
            client=client,
            tracer=tracer,
            cache=cache,
        )
        return agent, client

    def test_agent_run_records_agent_span(self):
        tracer = Tracer()
        agent, _ = self._make_agent(tracer=tracer)
        agent.run("hello")
        assert tracer.span_count >= 1
        spans = tracer.get_spans()
        assert spans[0].name == "agent.run"

    def test_agent_span_has_agent_attribute(self):
        tracer = Tracer()
        agent, _ = self._make_agent(tracer=tracer)
        agent.run("hello")
        spans = tracer.get_spans()
        assert spans[0].attributes["agent"] == "_EchoAgent"

    def test_tool_call_recorded_as_child_span(self):
        tracer = Tracer()
        client = MagicMock()
        # First response triggers a tool call, second ends the turn
        client.messages.create.side_effect = [
            _tool_resp("echo", {"text": "hi"}),
            _text_resp("result"),
        ]
        agent = _EchoAgent(
            tools=[],
            system_prompt="test",
            client=client,
            tracer=tracer,
        )
        agent.run("trigger tool")
        spans = tracer.get_spans()
        tool_spans = [s for s in spans if s.name == "tool.call"]
        assert len(tool_spans) >= 1
        assert tool_spans[0].attributes["tool"] == "echo"

    def test_agent_span_status_ok_on_success(self):
        tracer = Tracer()
        agent, _ = self._make_agent(tracer=tracer)
        agent.run("hello")
        spans = tracer.get_spans()
        agent_spans = [s for s in spans if s.name == "agent.run"]
        assert agent_spans[0].status == "ok"

    def test_no_tracer_still_works(self):
        agent, _ = self._make_agent(tracer=None)
        result = agent.run("hello")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# TestAgentWithCache
# ---------------------------------------------------------------------------


class TestAgentWithCache:
    def _make_agent_with_cache(self):
        cache = ResponseCache()
        client = MagicMock()
        client.messages.create.return_value = _text_resp("cached result")
        agent = _EchoAgent(
            tools=[],
            system_prompt="test",
            client=client,
            cache=cache,
        )
        return agent, client, cache

    def test_cache_hit_skips_claude_call(self):
        agent, client, _ = self._make_agent_with_cache()
        agent.run("same message")
        agent.run("same message")
        # Claude should only be called once; second call is a cache hit
        assert client.messages.create.call_count == 1

    def test_cache_miss_calls_claude(self):
        agent, client, _ = self._make_agent_with_cache()
        agent.run("first call")
        assert client.messages.create.call_count == 1

    def test_cache_stores_result(self):
        agent, _, cache = self._make_agent_with_cache()
        agent.run("populate cache")
        assert cache.size == 1

    def test_different_messages_create_separate_cache_entries(self):
        agent, _, cache = self._make_agent_with_cache()
        agent.run("msg1")
        agent.run("msg2")
        assert cache.size == 2

    def test_no_cache_still_works(self):
        client = MagicMock()
        client.messages.create.return_value = _text_resp("no cache")
        agent = _EchoAgent(
            tools=[],
            system_prompt="test",
            client=client,
            cache=None,
        )
        result = agent.run("hello")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# TestConnectorGetCaching
# ---------------------------------------------------------------------------


class _TestConnector(BaseHTTPConnector):
    _base_url = "https://api.example.com"

    def _auth_headers(self):
        return {"Authorization": "Bearer test"}


class TestConnectorGetCaching:
    @respx.mock
    def test_get_cached_on_second_call(self):
        route = respx.get("https://api.example.com/items").mock(
            return_value=httpx.Response(200, json={"items": []})
        )
        connector = _TestConnector()
        connector._cache = ResponseCache()
        connector._get("items")
        connector._get("items")
        # Network should only be hit once; second call served from cache
        assert route.call_count == 1

    @respx.mock
    def test_post_bypasses_cache(self):
        route = respx.post("https://api.example.com/items").mock(
            return_value=httpx.Response(201, json={"id": "new-1"})
        )
        connector = _TestConnector()
        connector._cache = ResponseCache()
        connector._post("items", json={"name": "item1"})
        connector._post("items", json={"name": "item1"})
        # POST is never cached — both calls should hit the network
        assert route.call_count == 2

    def test_cache_disabled_by_default(self):
        connector = _TestConnector()
        assert connector._cache is None

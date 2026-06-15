"""Tests for the FastAPI REST server (agents, orchestrator, health, cache endpoints)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from agentic_erp.cache.response_cache import ResponseCache
from agentic_erp.observability.tracing import Tracer
from agentic_erp.server.app import create_app
from agentic_erp.server.deps import ServerState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mock_orchestrator(platforms=("salesforce", "dynamics365")):
    orch = MagicMock()
    orch.configured_platforms = list(platforms)
    orch.platform_status = {p: "closed" for p in platforms}
    orch.run.return_value = {p: f"{p} result" for p in platforms}
    orch.run_async = _async_return({p: f"{p} result" for p in platforms})
    orch.run_platform.return_value = "platform response"
    orch.run_platform_async = _async_return("platform response")
    orch.run_and_synthesize.return_value = "synthesized"
    orch.run_and_synthesize_async = _async_return("synthesized")
    return orch


def _async_return(value):
    """Return an async mock that resolves to *value*."""

    async def _coro(*args, **kwargs):
        return value

    return _coro


@pytest.fixture
def mock_orchestrator():
    return _make_mock_orchestrator()


@pytest.fixture
def server_state(mock_orchestrator):
    cache = ResponseCache(default_ttl=60.0, max_size=10)
    return ServerState(orchestrator=mock_orchestrator, cache=cache, tracer=Tracer())


@pytest.fixture
def app(server_state):
    return create_app(server_state)


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_lists_platforms(self, client):
        data = (await client.get("/health")).json()
        assert set(data["configured_platforms"]) == {"salesforce", "dynamics365"}

    @pytest.mark.asyncio
    async def test_health_includes_platform_status(self, client):
        data = (await client.get("/health")).json()
        assert data["platform_status"]["salesforce"] == "closed"

    @pytest.mark.asyncio
    async def test_health_includes_cache_stats(self, client):
        data = (await client.get("/health")).json()
        assert "cache_stats" in data
        assert "hits" in data["cache_stats"]

    @pytest.mark.asyncio
    async def test_health_status_is_ok_string(self, client):
        data = (await client.get("/health")).json()
        assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# Cache endpoints
# ---------------------------------------------------------------------------


class TestCacheEndpoints:
    @pytest.mark.asyncio
    async def test_stats_returns_200(self, client):
        resp = await client.get("/cache/stats")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_stats_shape(self, client):
        data = (await client.get("/cache/stats")).json()
        for key in ("hits", "misses", "size", "hit_rate", "max_size", "default_ttl"):
            assert key in data

    @pytest.mark.asyncio
    async def test_clear_returns_cleared_true(self, client):
        resp = await client.post("/cache/clear")
        assert resp.status_code == 200
        assert resp.json() == {"cleared": True}

    @pytest.mark.asyncio
    async def test_clear_flushes_cache(self, client, server_state):
        server_state.cache.set("x", 42)
        assert server_state.cache.size == 1
        await client.post("/cache/clear")
        assert server_state.cache.size == 0


# ---------------------------------------------------------------------------
# Agent endpoints — /agents/{platform}/run
# ---------------------------------------------------------------------------


class TestAgentRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_returns_200(self, client):
        resp = await client.post(
            "/agents/salesforce/run", json={"message": "List leads"}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_run_response_shape(self, client):
        data = (
            await client.post("/agents/salesforce/run", json={"message": "List leads"})
        ).json()
        assert data["platform"] == "salesforce"
        assert data["result"] == "platform response"
        assert "duration_ms" in data

    @pytest.mark.asyncio
    async def test_run_calls_run_platform(self, client, mock_orchestrator):
        await client.post("/agents/salesforce/run", json={"message": "hello"})
        mock_orchestrator.run_platform.assert_called_once_with("salesforce", "hello")

    @pytest.mark.asyncio
    async def test_run_unknown_platform_returns_404(self, client):
        resp = await client.post("/agents/unknown/run", json={"message": "test"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_run_404_detail_lists_available(self, client):
        data = (
            await client.post("/agents/unknown/run", json={"message": "test"})
        ).json()
        assert "salesforce" in data["detail"] or "dynamics365" in data["detail"]

    @pytest.mark.asyncio
    async def test_run_missing_message_returns_422(self, client):
        resp = await client.post("/agents/salesforce/run", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_run_agent_exception_returns_500(self, client, mock_orchestrator):
        mock_orchestrator.run_platform.side_effect = RuntimeError("connector down")
        resp = await client.post("/agents/salesforce/run", json={"message": "hi"})
        assert resp.status_code == 500
        assert "connector down" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Agent endpoints — /agents/{platform}/stream
# ---------------------------------------------------------------------------


class TestAgentStreamEndpoint:
    @pytest.mark.asyncio
    async def test_stream_returns_200(self, client, mock_orchestrator):
        mock_orchestrator.stream_platform.return_value = iter(["Hello", " world"])
        resp = await client.post("/agents/salesforce/stream", json={"message": "go"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_stream_content_type_is_sse(self, client, mock_orchestrator):
        mock_orchestrator.stream_platform.return_value = iter(["chunk"])
        resp = await client.post("/agents/salesforce/stream", json={"message": "go"})
        assert "text/event-stream" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_stream_yields_data_events(self, client, mock_orchestrator):
        mock_orchestrator.stream_platform.return_value = iter(["Hello", " world"])
        resp = await client.post("/agents/salesforce/stream", json={"message": "go"})
        text = resp.text
        assert 'data: {"text": "Hello"}' in text
        assert 'data: {"text": " world"}' in text

    @pytest.mark.asyncio
    async def test_stream_ends_with_done(self, client, mock_orchestrator):
        mock_orchestrator.stream_platform.return_value = iter(["x"])
        resp = await client.post("/agents/salesforce/stream", json={"message": "go"})
        assert "data: [DONE]" in resp.text

    @pytest.mark.asyncio
    async def test_stream_unknown_platform_returns_404(self, client):
        resp = await client.post("/agents/nobody/stream", json={"message": "go"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Orchestrator endpoints
# ---------------------------------------------------------------------------


class TestOrchestratorRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_returns_200(self, client):
        resp = await client.post(
            "/orchestrator/run", json={"task": "List all open orders"}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_run_response_shape(self, client):
        data = (
            await client.post(
                "/orchestrator/run", json={"task": "List all open orders"}
            )
        ).json()
        assert "results" in data
        assert "platforms" in data
        assert "duration_ms" in data

    @pytest.mark.asyncio
    async def test_run_parallel_uses_run_async(self, client, mock_orchestrator):
        # Track calls via a flag
        called = {}

        async def _fake_run_async(task):
            called["async"] = True
            return {"salesforce": "ok"}

        mock_orchestrator.run_async = _fake_run_async

        await client.post("/orchestrator/run", json={"task": "test", "parallel": True})
        assert called.get("async") is True

    @pytest.mark.asyncio
    async def test_run_sequential_uses_run_sync(self, client, mock_orchestrator):
        called = {}

        def _fake_run(task):
            called["sync"] = True
            return {"salesforce": "ok"}

        mock_orchestrator.run = _fake_run

        await client.post("/orchestrator/run", json={"task": "test", "parallel": False})
        assert called.get("sync") is True

    @pytest.mark.asyncio
    async def test_run_missing_task_returns_422(self, client):
        resp = await client.post("/orchestrator/run", json={})
        assert resp.status_code == 422


class TestOrchestratorSynthesizeEndpoint:
    @pytest.mark.asyncio
    async def test_synthesize_returns_200(self, client):
        resp = await client.post(
            "/orchestrator/synthesize", json={"task": "Compare CRM data"}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_synthesize_response_shape(self, client):
        data = (
            await client.post(
                "/orchestrator/synthesize", json={"task": "Compare CRM data"}
            )
        ).json()
        assert "result" in data
        assert "platform_results" in data
        assert "duration_ms" in data

    @pytest.mark.asyncio
    async def test_synthesize_result_is_synthesized(self, client):
        data = (
            await client.post(
                "/orchestrator/synthesize", json={"task": "Compare CRM data"}
            )
        ).json()
        assert data["result"] == "synthesized"


# ---------------------------------------------------------------------------
# ServerState / app factory
# ---------------------------------------------------------------------------


class TestAppFactory:
    def test_create_app_sets_state(self, server_state):
        from agentic_erp.server.app import create_app

        a = create_app(server_state)
        assert a.state.server_state is server_state

    def test_create_app_registers_health_route(self, server_state):
        from agentic_erp.server.app import create_app

        a = create_app(server_state)
        # url_path_for confirms the named route exists
        path = a.url_path_for("health")
        assert str(path) == "/health"

    def test_server_state_default_cache(self, mock_orchestrator):
        state = ServerState(orchestrator=mock_orchestrator)
        assert state.cache is not None
        assert isinstance(state.cache, ResponseCache)

    def test_server_state_default_tracer(self, mock_orchestrator):
        state = ServerState(orchestrator=mock_orchestrator)
        assert isinstance(state.tracer, Tracer)

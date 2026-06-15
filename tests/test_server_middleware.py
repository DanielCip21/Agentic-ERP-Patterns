"""Tests for APIKeyMiddleware and RateLimitMiddleware."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from agentic_erp.cache.response_cache import ResponseCache
from agentic_erp.observability.tracing import Tracer
from agentic_erp.server.app import create_app
from agentic_erp.server.deps import ServerState
from agentic_erp.server.middleware.rate_limit import RateLimiter

_SECRET = "test-api-key-secret"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_orchestrator():
    orch = MagicMock()
    orch.configured_platforms = ["salesforce"]
    orch.platform_status = {"salesforce": "closed"}
    orch.run_platform.return_value = "ok"
    return orch


@pytest.fixture
def base_state():
    return ServerState(
        orchestrator=_make_orchestrator(),
        cache=ResponseCache(default_ttl=60.0),
        tracer=Tracer(),
    )


@pytest.fixture
async def auth_client(base_state):
    app = create_app(base_state, api_key=_SECRET)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def rate_client(base_state):
    """Client with a tight 3 rpm limit for threshold tests."""
    app = create_app(base_state, rate_limit_rpm=3)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def both_client(base_state):
    """Client with both auth and rate limiting (5 rpm)."""
    app = create_app(base_state, api_key=_SECRET, rate_limit_rpm=5)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# RateLimiter unit tests
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def test_allows_requests_within_limit(self):
        rl = RateLimiter(requests_per_minute=3)
        for _ in range(3):
            allowed, _ = rl.is_allowed("k")
            assert allowed

    def test_blocks_request_exceeding_limit(self):
        rl = RateLimiter(requests_per_minute=3)
        for _ in range(3):
            rl.is_allowed("k")
        allowed, remaining = rl.is_allowed("k")
        assert not allowed
        assert remaining == 0

    def test_remaining_decrements_correctly(self):
        rl = RateLimiter(requests_per_minute=5)
        _, r1 = rl.is_allowed("k")
        _, r2 = rl.is_allowed("k")
        _, r3 = rl.is_allowed("k")
        assert r1 == 4
        assert r2 == 3
        assert r3 == 2

    def test_different_keys_are_independent(self):
        rl = RateLimiter(requests_per_minute=1)
        rl.is_allowed("key_a")
        allowed, _ = rl.is_allowed("key_b")
        assert allowed  # key_b not affected by key_a

    def test_reset_specific_key_clears_window(self):
        rl = RateLimiter(requests_per_minute=1)
        rl.is_allowed("k")
        rl.reset("k")
        allowed, _ = rl.is_allowed("k")
        assert allowed

    def test_reset_all_clears_every_key(self):
        rl = RateLimiter(requests_per_minute=1)
        for k in ("a", "b", "c"):
            rl.is_allowed(k)
        rl.reset()
        for k in ("a", "b", "c"):
            allowed, _ = rl.is_allowed(k)
            assert allowed

    def test_limit_property_returns_rpm(self):
        rl = RateLimiter(requests_per_minute=42)
        assert rl.limit == 42


# ---------------------------------------------------------------------------
# APIKeyMiddleware integration tests
# ---------------------------------------------------------------------------

class TestAPIKeyMiddleware:
    @pytest.mark.asyncio
    async def test_missing_key_returns_401(self, auth_client):
        resp = await auth_client.get("/cache/stats")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_key_returns_401(self, auth_client):
        resp = await auth_client.get("/cache/stats", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_correct_key_returns_200(self, auth_client):
        resp = await auth_client.get("/cache/stats", headers={"X-API-Key": _SECRET})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_401_has_www_authenticate_header(self, auth_client):
        resp = await auth_client.get("/cache/stats")
        assert "WWW-Authenticate" in resp.headers

    @pytest.mark.asyncio
    async def test_401_body_has_detail(self, auth_client):
        resp = await auth_client.get("/cache/stats")
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_health_exempt_from_auth(self, auth_client):
        resp = await auth_client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_docs_exempt_from_auth(self, auth_client):
        resp = await auth_client.get("/openapi.json")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_agent_endpoint_requires_key(self, auth_client):
        resp = await auth_client.post("/agents/salesforce/run", json={"message": "hi"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_agent_endpoint_works_with_key(self, auth_client):
        resp = await auth_client.post(
            "/agents/salesforce/run",
            json={"message": "hi"},
            headers={"X-API-Key": _SECRET},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# RateLimitMiddleware integration tests
# ---------------------------------------------------------------------------

class TestRateLimitMiddleware:
    @pytest.mark.asyncio
    async def test_requests_within_limit_succeed(self, rate_client):
        for _ in range(3):
            resp = await rate_client.get("/cache/stats")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_request_exceeding_limit_returns_429(self, rate_client):
        for _ in range(3):
            await rate_client.get("/cache/stats")
        resp = await rate_client.get("/cache/stats")
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_429_has_retry_after_header(self, rate_client):
        for _ in range(4):
            resp = await rate_client.get("/cache/stats")
        assert resp.headers.get("Retry-After") == "60"

    @pytest.mark.asyncio
    async def test_429_body_has_detail(self, rate_client):
        for _ in range(4):
            resp = await rate_client.get("/cache/stats")
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_response_includes_ratelimit_remaining(self, rate_client):
        resp = await rate_client.get("/cache/stats")
        assert "X-RateLimit-Remaining" in resp.headers

    @pytest.mark.asyncio
    async def test_response_includes_ratelimit_limit(self, rate_client):
        resp = await rate_client.get("/cache/stats")
        assert resp.headers["X-RateLimit-Limit"] == "3"

    @pytest.mark.asyncio
    async def test_remaining_decrements_on_each_request(self, rate_client):
        r1 = (await rate_client.get("/cache/stats")).headers["X-RateLimit-Remaining"]
        r2 = (await rate_client.get("/cache/stats")).headers["X-RateLimit-Remaining"]
        assert int(r1) > int(r2)

    @pytest.mark.asyncio
    async def test_health_exempt_from_rate_limit(self, base_state):
        # Limit of 1 rpm — health should still always succeed.
        app = create_app(base_state, rate_limit_rpm=1)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            for _ in range(5):
                resp = await c.get("/health")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_429_ratelimit_remaining_is_zero(self, rate_client):
        for _ in range(4):
            resp = await rate_client.get("/cache/stats")
        assert resp.headers.get("X-RateLimit-Remaining") == "0"


# ---------------------------------------------------------------------------
# Auth + rate-limit combined
# ---------------------------------------------------------------------------

class TestCombinedMiddleware:
    @pytest.mark.asyncio
    async def test_missing_key_blocked_before_rate_limit(self, both_client):
        """Auth is the outermost middleware — unauthenticated requests never
        touch the rate limiter, so they consume no quota."""
        resp = await both_client.get("/cache/stats")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_requests_are_rate_limited(self, both_client):
        headers = {"X-API-Key": _SECRET}
        for _ in range(5):
            await both_client.get("/cache/stats", headers=headers)
        resp = await both_client.get("/cache/stats", headers=headers)
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_health_exempt_from_both(self, both_client):
        for _ in range(10):
            resp = await both_client.get("/health")
            assert resp.status_code == 200

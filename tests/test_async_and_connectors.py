"""Tests for AsyncMultiAgentOrchestrator, TeamsApprovalCallback, and D365Connector."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentic_erp.patterns.async_orchestrator import AsyncMultiAgentOrchestrator
from agentic_erp.patterns.teams_approval import TeamsApprovalCallback
from agentic_erp.connectors.d365 import D365Connector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _async_text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


# ---------------------------------------------------------------------------
# AsyncMultiAgentOrchestrator
# ---------------------------------------------------------------------------

class TestAsyncMultiAgentOrchestrator:
    def _make_async_client(self, text: str):
        client = MagicMock()
        client.messages = MagicMock()
        client.messages.create = AsyncMock(return_value=_async_text_response(text))
        return client

    def test_routes_order_task(self):
        client = self._make_async_client("Order processed.")
        orch = AsyncMultiAgentOrchestrator(client=client)
        results = asyncio.get_event_loop().run_until_complete(
            orch.run("Process order ORD-001")
        )
        assert "order_agent" in results
        assert "inventory_agent" not in results

    def test_routes_inventory_task(self):
        client = self._make_async_client("Stock replenished.")
        orch = AsyncMultiAgentOrchestrator(client=client)
        results = asyncio.get_event_loop().run_until_complete(
            orch.run("Check stock levels and reorder")
        )
        assert "inventory_agent" in results
        assert "order_agent" not in results

    def test_routes_ambiguous_task_to_both(self):
        client = self._make_async_client("Done.")
        orch = AsyncMultiAgentOrchestrator(client=client)
        results = asyncio.get_event_loop().run_until_complete(
            orch.run("Run daily ERP summary")
        )
        assert "order_agent" in results
        assert "inventory_agent" in results

    def test_returns_string_results(self):
        client = self._make_async_client("All good.")
        orch = AsyncMultiAgentOrchestrator(client=client)
        results = asyncio.get_event_loop().run_until_complete(
            orch.run("Check everything")
        )
        for v in results.values():
            assert isinstance(v, str)


# ---------------------------------------------------------------------------
# TeamsApprovalCallback
# ---------------------------------------------------------------------------

class TestTeamsApprovalCallback:
    def _make_callback(self, webhook_url="http://teams.example/webhook", response_url="http://pa.example/response"):
        return TeamsApprovalCallback(
            webhook_url=webhook_url,
            response_url=response_url,
            timeout_s=1,
            poll_interval_s=0,
        )

    def test_approved_returns_true(self):
        cb = self._make_callback()

        def fake_urlopen(req, timeout=None):
            resp = MagicMock()
            url = req if isinstance(req, str) else req.full_url
            if "teams" in url or "webhook" in url:
                resp.status = 200
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                resp.read = lambda: b""
            else:
                resp.status = 200
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                resp.read = lambda: json.dumps({"approved": True}).encode()
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = cb("update_order_status", {"order_id": "ORD-001", "status": "shipped"})
        assert result is True

    def test_rejected_returns_false(self):
        cb = self._make_callback()

        def fake_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.status = 200
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            resp.read = lambda: json.dumps({"approved": False}).encode()
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = cb("create_purchase_order", {"sku": "SKU-A", "quantity": 200})
        assert result is False

    def test_timeout_auto_rejects(self):
        cb = TeamsApprovalCallback(
            webhook_url="http://teams.example/webhook",
            response_url="http://pa.example/response",
            timeout_s=0,
            poll_interval_s=0,
        )

        def fake_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.status = 200
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            resp.read = lambda: b"{}"
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = cb("update_order_status", {"order_id": "ORD-002", "status": "cancelled"})
        assert result is False

    def test_build_card_contains_tool_name(self):
        cb = self._make_callback()
        card = cb._build_card("create_purchase_order", {"sku": "SKU-B", "quantity": 50})
        card_str = json.dumps(card)
        assert "create_purchase_order" in card_str
        assert "SKU-B" in card_str

    def test_build_card_has_approve_and_reject_actions(self):
        cb = self._make_callback()
        card = cb._build_card("update_order_status", {"status": "shipped"})
        actions = card["attachments"][0]["content"]["actions"]
        titles = [a["title"] for a in actions]
        assert "Approve" in titles
        assert "Reject" in titles


# ---------------------------------------------------------------------------
# D365Connector
# ---------------------------------------------------------------------------

class TestD365Connector:
    def _make_connector(self):
        return D365Connector(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
            environment_url="https://test.crm.dynamics.com",
        )

    def _mock_token_response(self):
        resp = MagicMock()
        resp.status = 200
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        resp.read = lambda: json.dumps({"access_token": "tok123", "expires_in": 3600}).encode()
        return resp

    def _mock_api_response(self, body: dict):
        resp = MagicMock()
        resp.status = 200
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        resp.read = lambda: json.dumps(body).encode()
        return resp

    def test_get_record(self):
        conn = self._make_connector()
        order_data = {"salesorderid": "ORD-001", "name": "Test Order"}
        with patch("urllib.request.urlopen", side_effect=[
            self._mock_token_response(),
            self._mock_api_response(order_data),
        ]):
            result = conn.get_record("salesorders", "ORD-001")
        assert result["salesorderid"] == "ORD-001"

    def test_list_records(self):
        conn = self._make_connector()
        with patch("urllib.request.urlopen", side_effect=[
            self._mock_token_response(),
            self._mock_api_response({"value": [{"sku": "SKU-A"}]}),
        ]):
            result = conn.list_records("products", filter_="productnumber eq 'SKU-A'")
        assert result[0]["sku"] == "SKU-A"

    def test_create_record(self):
        conn = self._make_connector()
        with patch("urllib.request.urlopen", side_effect=[
            self._mock_token_response(),
            self._mock_api_response({"po_id": "PO-9999"}),
        ]):
            result = conn.create_record("purchaseorders", {"sku": "SKU-B", "quantity": 50})
        assert result["po_id"] == "PO-9999"

    def test_token_is_cached(self):
        conn = self._make_connector()
        with patch("urllib.request.urlopen", side_effect=[
            self._mock_token_response(),
            self._mock_api_response({"id": "A"}),
            self._mock_api_response({"id": "B"}),
        ]) as mock_open:
            conn.get_record("salesorders", "A")
            conn.get_record("salesorders", "B")
            # Token fetched once, then reused — total calls: 1 token + 2 API = 3
            assert mock_open.call_count == 3

    def test_convenience_get_order(self):
        conn = self._make_connector()
        with patch("urllib.request.urlopen", side_effect=[
            self._mock_token_response(),
            self._mock_api_response({"salesorderid": "ORD-002"}),
        ]):
            result = conn.get_order("ORD-002")
        assert result["salesorderid"] == "ORD-002"

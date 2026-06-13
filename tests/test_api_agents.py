"""Unit tests for API agents: ApiGatewayAgent, WebhookProcessorAgent, DataSyncAgent."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentic_erp.api.gateway_agent import ApiGatewayAgent
from agentic_erp.api.webhook_processor_agent import WebhookProcessorAgent
from agentic_erp.api.data_sync_agent import DataSyncAgent


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _make_text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_tool_then_text_response(tool_name: str, tool_inputs: dict, tool_use_id: str, final_text: str):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_inputs
    tool_block.id = tool_use_id

    tool_response = MagicMock()
    tool_response.stop_reason = "tool_use"
    tool_response.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = final_text

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_response.content = [text_block]

    return tool_response, text_response


# ---------------------------------------------------------------------------
# ApiGatewayAgent
# ---------------------------------------------------------------------------

class TestApiGatewayAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("All services healthy. Payment service latency 45ms.")
        agent = ApiGatewayAgent(client=client)
        result = agent.run("Check all service health")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "check_api_health",
            {"service_name": "payment_service"},
            "tu_gw_001",
            "Payment service is healthy with 45ms latency.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ApiGatewayAgent(client=client)
        result = agent.run("Is the payment service healthy?")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_call_api(self):
        agent = ApiGatewayAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "call_api",
            {"endpoint": "https://payments.internal/api/v2/charge", "method": "POST", "payload": {"amount": 100}},
        )
        assert isinstance(result, dict)
        assert "status_code" in result

    def test_dispatch_call_api_no_payload(self):
        agent = ApiGatewayAgent(client=MagicMock())
        result = agent._dispatch_tool("call_api", {"endpoint": "https://api.example.com/health", "method": "GET"})
        assert isinstance(result, dict)

    def test_dispatch_check_api_health(self):
        agent = ApiGatewayAgent(client=MagicMock())
        result = agent._dispatch_tool("check_api_health", {"service_name": "inventory_service"})
        assert isinstance(result, dict)
        assert "status" in result

    def test_dispatch_check_api_health_unknown_service(self):
        agent = ApiGatewayAgent(client=MagicMock())
        result = agent._dispatch_tool("check_api_health", {"service_name": "nonexistent_service"})
        assert "error" in result

    def test_dispatch_log_api_event(self):
        agent = ApiGatewayAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "log_api_event",
            {"service": "payment_service", "event_type": "success", "details": "Charge processed"},
        )
        assert isinstance(result, dict)
        assert "event_id" in result

    def test_dispatch_trigger_fallback(self):
        agent = ApiGatewayAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "trigger_fallback",
            {"service_name": "notification_service", "payload": {"message": "Hello"}},
        )
        assert isinstance(result, dict)
        assert result.get("fallback_triggered") is True

    def test_dispatch_unknown_tool(self):
        agent = ApiGatewayAgent(client=MagicMock())
        result = agent._dispatch_tool("nonexistent_op", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# WebhookProcessorAgent
# ---------------------------------------------------------------------------

class TestWebhookProcessorAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Webhook classified as order.created and routed.")
        agent = WebhookProcessorAgent(client=client)
        result = agent.run("Process incoming order webhook")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        payload = {"event_type": "order.created", "source": "shopify", "order_id": "ORD-1001"}
        tool_resp, text_resp = _make_tool_then_text_response(
            "classify_webhook",
            {"payload": payload},
            "tu_wh_001",
            "Webhook classified as order.created — routing to order_processing_workflow.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = WebhookProcessorAgent(client=client)
        result = agent.run("Classify and route this webhook")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_classify_webhook_known_event(self):
        agent = WebhookProcessorAgent(client=MagicMock())
        result = agent._dispatch_tool("classify_webhook", {"payload": {"event_type": "payment.received"}})
        assert isinstance(result, dict)
        assert result["is_known_event"] is True

    def test_dispatch_classify_webhook_unknown_event(self):
        agent = WebhookProcessorAgent(client=MagicMock())
        result = agent._dispatch_tool("classify_webhook", {"payload": {"event_type": "unknown.event"}})
        assert isinstance(result, dict)
        assert result["is_known_event"] is False

    def test_dispatch_route_to_workflow(self):
        agent = WebhookProcessorAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "route_to_workflow",
            {"event_type": "order.created", "payload": {"order_id": "ORD-001"}},
        )
        assert isinstance(result, dict)
        assert "webhook_id" in result

    def test_dispatch_acknowledge_webhook(self):
        agent = WebhookProcessorAgent(client=MagicMock())
        # First create a webhook to acknowledge
        route_result = agent._dispatch_tool(
            "route_to_workflow",
            {"event_type": "payment.received", "payload": {"amount": 500}},
        )
        webhook_id = route_result["webhook_id"]
        ack_result = agent._dispatch_tool("acknowledge_webhook", {"webhook_id": webhook_id})
        assert ack_result["status"] == "acknowledged"

    def test_dispatch_dead_letter(self):
        agent = WebhookProcessorAgent(client=MagicMock())
        result = agent._dispatch_tool("dead_letter", {"webhook_id": "WH-999999", "reason": "No handler found"})
        assert isinstance(result, dict)
        assert result["status"] == "dead_lettered"

    def test_dispatch_unknown_tool(self):
        agent = WebhookProcessorAgent(client=MagicMock())
        result = agent._dispatch_tool("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# DataSyncAgent
# ---------------------------------------------------------------------------

class TestDataSyncAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Sync complete: 2 records applied from Salesforce.")
        agent = DataSyncAgent(client=client)
        result = agent.run("Sync changes from Salesforce to Dynamics 365")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_sync_delta",
            {"source_system": "salesforce", "since_timestamp": "2026-06-12T00:00:00Z"},
            "tu_sync_001",
            "Retrieved 2 changed records from Salesforce.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = DataSyncAgent(client=client)
        result = agent.run("Get delta from Salesforce")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_get_sync_delta(self):
        agent = DataSyncAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "get_sync_delta",
            {"source_system": "salesforce", "since_timestamp": "2026-06-01T00:00:00Z"},
        )
        assert isinstance(result, dict)
        assert "changes" in result

    def test_dispatch_get_sync_delta_unknown_source(self):
        agent = DataSyncAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "get_sync_delta",
            {"source_system": "unknown_system", "since_timestamp": "2026-06-01T00:00:00Z"},
        )
        assert "error" in result

    def test_dispatch_apply_changes(self):
        agent = DataSyncAgent(client=MagicMock())
        changes = [
            {"record_id": "REC-001", "entity": "Contact", "operation": "update", "fields": {"email": "a@b.com"}},
            {"record_id": "REC-002", "entity": "Lead", "operation": "create", "fields": {"name": "Test"}},
        ]
        result = agent._dispatch_tool("apply_changes", {"target_system": "dynamics365", "changes": changes})
        assert isinstance(result, dict)
        assert "applied" in result

    def test_dispatch_resolve_conflict(self):
        agent = DataSyncAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "resolve_conflict",
            {"record_id": "REC-001", "strategy": "latest_timestamp_wins"},
        )
        assert isinstance(result, dict)
        assert "strategy_applied" in result

    def test_dispatch_resolve_conflict_invalid_strategy(self):
        agent = DataSyncAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "resolve_conflict",
            {"record_id": "REC-001", "strategy": "bad_strategy"},
        )
        assert "error" in result

    def test_dispatch_log_sync_result(self):
        agent = DataSyncAgent(client=MagicMock())
        stats = {"applied": 10, "failed": 1, "conflicts": 0, "duration_ms": 450}
        result = agent._dispatch_tool(
            "log_sync_result",
            {"source": "salesforce", "target": "dynamics365", "stats": stats},
        )
        assert isinstance(result, dict)
        assert "sync_id" in result

    def test_dispatch_unknown_tool(self):
        agent = DataSyncAgent(client=MagicMock())
        result = agent._dispatch_tool("noop", {})
        assert "error" in result

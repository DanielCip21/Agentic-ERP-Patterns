"""Tests for API agents — tool dispatch and agent smoke tests (mocked client)."""

from unittest.mock import MagicMock

from agentic_erp.api.gateway_agent import ApiGatewayAgent
from agentic_erp.api.webhook_processor_agent import WebhookProcessorAgent
from agentic_erp.api.data_sync_agent import DataSyncAgent


def _text_response(text="Done."):
    block = MagicMock(); block.type = "text"; block.text = text
    resp = MagicMock(); resp.stop_reason = "end_turn"; resp.content = [block]
    return resp


def _agent(cls):
    return cls(client=MagicMock())


# --- Tool dispatch tests ---

class TestApiGatewayTools:
    def test_check_api_health_found(self):
        result = _agent(ApiGatewayAgent)._dispatch_tool(
            "check_api_health", {"service_name": "payment_service"})
        assert "status" in result
        assert "latency_ms" in result

    def test_check_api_health_not_found(self):
        result = _agent(ApiGatewayAgent)._dispatch_tool(
            "check_api_health", {"service_name": "nonexistent_svc"})
        assert "error" in result

    def test_call_api_returns_result(self):
        result = _agent(ApiGatewayAgent)._dispatch_tool(
            "call_api", {"endpoint": "https://example.com/api/v1/status", "method": "GET"})
        assert "status_code" in result
        assert "endpoint" in result

    def test_log_api_event(self):
        result = _agent(ApiGatewayAgent)._dispatch_tool(
            "log_api_event", {"service": "payment_service", "event_type": "success", "details": "200 OK"})
        assert result.get("event_type") == "success" or "logged" in str(result)

    def test_trigger_fallback_configured(self):
        result = _agent(ApiGatewayAgent)._dispatch_tool(
            "trigger_fallback", {"service_name": "notification_service", "payload": {"msg": "hello"}})
        assert "fallback" in str(result).lower() or "triggered" in str(result).lower()


class TestWebhookProcessorTools:
    def test_classify_known_event(self):
        result = _agent(WebhookProcessorAgent)._dispatch_tool(
            "classify_webhook", {"payload": {"event_type": "order.created", "source": "dynamics365"}})
        assert result.get("event_type") == "order.created"
        assert result.get("is_known_event") is True or result.get("known") is True

    def test_classify_unknown_event(self):
        result = _agent(WebhookProcessorAgent)._dispatch_tool(
            "classify_webhook", {"payload": {"event_type": "foo.bar"}})
        known = result.get("is_known_event", result.get("known", True))
        assert known is False

    def test_classify_no_type(self):
        result = _agent(WebhookProcessorAgent)._dispatch_tool(
            "classify_webhook", {"payload": {"data": "something"}})
        assert "error" in result

    def test_route_to_workflow_valid(self):
        result = _agent(WebhookProcessorAgent)._dispatch_tool(
            "route_to_workflow", {"event_type": "order.created", "payload": {"order_id": "ORD-001"}})
        assert "order_processing" in str(result).lower() or "workflow" in str(result).lower()

    def test_route_to_workflow_unmapped(self):
        result = _agent(WebhookProcessorAgent)._dispatch_tool(
            "route_to_workflow", {"event_type": "unknown.event", "payload": {}})
        assert "error" in result

    def test_dead_letter(self):
        result = _agent(WebhookProcessorAgent)._dispatch_tool(
            "dead_letter", {"webhook_id": "WHK-001", "reason": "Unrecognised type"})
        assert result["webhook_id"] == "WHK-001"


class TestDataSyncTools:
    def test_get_sync_delta(self):
        result = _agent(DataSyncAgent)._dispatch_tool(
            "get_sync_delta", {"source_system": "salesforce", "since_timestamp": "2026-06-12T00:00:00"})
        assert "changes" in result or "records" in result
        assert result.get("source_system") == "salesforce" or result.get("source") == "salesforce"

    def test_get_sync_delta_unknown_source(self):
        result = _agent(DataSyncAgent)._dispatch_tool(
            "get_sync_delta", {"source_system": "unknownsystem", "since_timestamp": "2026-01-01T00:00:00"})
        assert "error" in result

    def test_apply_changes(self):
        changes = [{"record_id": "SF-001", "operation": "update", "fields": {"name": "Updated"}}]
        result = _agent(DataSyncAgent)._dispatch_tool(
            "apply_changes", {"target_system": "dynamics365", "changes": changes})
        assert "applied" in result

    def test_resolve_conflict_valid(self):
        result = _agent(DataSyncAgent)._dispatch_tool(
            "resolve_conflict", {"record_id": "SF-001", "strategy": "source_wins"})
        assert "error" not in result

    def test_resolve_conflict_invalid_strategy(self):
        result = _agent(DataSyncAgent)._dispatch_tool(
            "resolve_conflict", {"record_id": "SF-001", "strategy": "flip_a_coin"})
        assert "error" in result

    def test_log_sync_result(self):
        result = _agent(DataSyncAgent)._dispatch_tool(
            "log_sync_result", {"source": "salesforce", "target": "dynamics365",
                                "stats": {"applied": 5, "failed": 0}})
        assert "sync_id" in result or "logged" in str(result)


# --- Agent smoke tests ---

class TestAPIAgentRuns:
    def test_gateway_run(self):
        client = MagicMock()
        client.messages.create.return_value = _text_response("API calls completed.")
        assert isinstance(ApiGatewayAgent(client=client).run("Check health of payment_service"), str)

    def test_webhook_run(self):
        client = MagicMock()
        client.messages.create.return_value = _text_response("Webhook routed to order_processing_workflow.")
        assert isinstance(WebhookProcessorAgent(client=client).run(
            'Process webhook: {"event_type": "order.created", "order_id": "ORD-001"}'), str)

    def test_data_sync_run(self):
        client = MagicMock()
        client.messages.create.return_value = _text_response("Sync complete: 2 records applied.")
        assert isinstance(DataSyncAgent(client=client).run(
            "Sync salesforce to dynamics365 since 2026-06-12"), str)

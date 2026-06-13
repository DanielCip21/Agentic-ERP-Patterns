"""Unit tests for AI agents: DocumentIntelligenceAgent, SentimentAgent, KnowledgeBaseAgent, ForecastingAgent."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentic_erp.ai.document_intelligence_agent import DocumentIntelligenceAgent
from agentic_erp.ai.sentiment_agent import SentimentAgent
from agentic_erp.ai.knowledge_base_agent import KnowledgeBaseAgent
from agentic_erp.ai.forecasting_agent import ForecastingAgent


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
# DocumentIntelligenceAgent
# ---------------------------------------------------------------------------

class TestDocumentIntelligenceAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Invoice DOC-001 extracted successfully.")
        agent = DocumentIntelligenceAgent(client=client)
        result = agent.run("Extract fields from DOC-001")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "extract_invoice_fields",
            {"document_id": "DOC-001"},
            "tu_doc_001",
            "Fields extracted: vendor=Acme Corp, total=$4250.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = DocumentIntelligenceAgent(client=client)
        result = agent.run("Process DOC-001")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_extract_invoice_fields(self):
        agent = DocumentIntelligenceAgent(client=MagicMock())
        result = agent._dispatch_tool("extract_invoice_fields", {"document_id": "DOC-001"})
        assert isinstance(result, dict)
        assert "extracted_fields" in result

    def test_dispatch_validate_extracted_data(self):
        agent = DocumentIntelligenceAgent(client=MagicMock())
        fields = {"vendor": "Acme Corp", "invoice_number": "INV-001", "date": "2026-06-01", "total": 500.0, "confidence": 0.95}
        result = agent._dispatch_tool("validate_extracted_data", {"document_id": "DOC-001", "fields": fields})
        assert isinstance(result, dict)
        assert "is_valid" in result

    def test_dispatch_route_document(self):
        agent = DocumentIntelligenceAgent(client=MagicMock())
        result = agent._dispatch_tool("route_document", {"document_id": "DOC-001", "destination": "accounts_payable"})
        assert isinstance(result, dict)
        assert "routed_to" in result

    def test_dispatch_flag_for_review(self):
        agent = DocumentIntelligenceAgent(client=MagicMock())
        result = agent._dispatch_tool("flag_for_review", {"document_id": "DOC-003", "reason": "Low confidence extraction"})
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = DocumentIntelligenceAgent(client=MagicMock())
        result = agent._dispatch_tool("mystery", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# SentimentAgent
# ---------------------------------------------------------------------------

class TestSentimentAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("2 negative feedback items found and escalated.")
        agent = SentimentAgent(client=client)
        result = agent.run("Analyse support ticket sentiment")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_feedback_batch",
            {"source": "support_tickets"},
            "tu_sent_001",
            "Retrieved 3 feedback items from support_tickets.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = SentimentAgent(client=client)
        result = agent.run("Get feedback from support tickets")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_get_feedback_batch(self):
        agent = SentimentAgent(client=MagicMock())
        result = agent._dispatch_tool("get_feedback_batch", {"source": "support_tickets"})
        assert isinstance(result, dict)
        assert "feedback" in result

    def test_dispatch_get_feedback_batch_with_limit(self):
        agent = SentimentAgent(client=MagicMock())
        result = agent._dispatch_tool("get_feedback_batch", {"source": "nps_survey", "limit": 2})
        assert isinstance(result, dict)

    def test_dispatch_analyze_sentiment_positive(self):
        agent = SentimentAgent(client=MagicMock())
        result = agent._dispatch_tool("analyze_sentiment", {"text": "Great product, love it!"})
        assert result["sentiment"] == "positive"

    def test_dispatch_analyze_sentiment_negative(self):
        agent = SentimentAgent(client=MagicMock())
        result = agent._dispatch_tool("analyze_sentiment", {"text": "Totally unacceptable service."})
        assert result["sentiment"] == "negative"

    def test_dispatch_tag_feedback(self):
        agent = SentimentAgent(client=MagicMock())
        result = agent._dispatch_tool("tag_feedback", {"feedback_id": "FB-001", "tags": ["onboarding", "positive"]})
        assert isinstance(result, dict)
        assert result["tags"] == ["onboarding", "positive"]

    def test_dispatch_escalate_negative_feedback(self):
        agent = SentimentAgent(client=MagicMock())
        result = agent._dispatch_tool("escalate_negative_feedback", {"feedback_id": "FB-002", "priority": "high"})
        assert isinstance(result, dict)
        assert "escalation_id" in result

    def test_dispatch_unknown_tool(self):
        agent = SentimentAgent(client=MagicMock())
        result = agent._dispatch_tool("nonexistent", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# KnowledgeBaseAgent
# ---------------------------------------------------------------------------

class TestKnowledgeBaseAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Found 2 articles about password reset.")
        agent = KnowledgeBaseAgent(client=client)
        result = agent.run("Search for password reset articles")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "search_knowledge_base",
            {"query": "SSO Azure", "top_k": 3},
            "tu_kb_001",
            "Found ART-002: Configuring SSO with Azure AD.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = KnowledgeBaseAgent(client=client)
        result = agent.run("Find SSO documentation")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_search_knowledge_base(self):
        agent = KnowledgeBaseAgent(client=MagicMock())
        result = agent._dispatch_tool("search_knowledge_base", {"query": "password"})
        assert isinstance(result, dict)
        assert "results" in result

    def test_dispatch_search_with_top_k(self):
        agent = KnowledgeBaseAgent(client=MagicMock())
        result = agent._dispatch_tool("search_knowledge_base", {"query": "sso azure", "top_k": 1})
        assert isinstance(result, dict)
        assert len(result["results"]) <= 1

    def test_dispatch_get_article(self):
        agent = KnowledgeBaseAgent(client=MagicMock())
        result = agent._dispatch_tool("get_article", {"article_id": "ART-001"})
        assert isinstance(result, dict)
        assert "title" in result

    def test_dispatch_create_article(self):
        agent = KnowledgeBaseAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "create_article",
            {"title": "Test Article", "content": "This is test content.", "tags": ["test", "docs"]},
        )
        assert isinstance(result, dict)
        assert result["title"] == "Test Article"

    def test_dispatch_mark_article_outdated(self):
        agent = KnowledgeBaseAgent(client=MagicMock())
        result = agent._dispatch_tool("mark_article_outdated", {"article_id": "ART-003"})
        assert isinstance(result, dict)
        assert result["status"] == "outdated"

    def test_dispatch_unknown_tool(self):
        agent = KnowledgeBaseAgent(client=MagicMock())
        result = agent._dispatch_tool("fake_op", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# ForecastingAgent
# ---------------------------------------------------------------------------

class TestForecastingAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Forecast for PROD-001: 1200 units over 90 days.")
        agent = ForecastingAgent(client=client)
        result = agent.run("Forecast demand for PROD-001")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_historical_sales",
            {"product_id": "PROD-001", "periods": 5},
            "tu_fc_001",
            "Historical data retrieved. Average 368 units/month.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ForecastingAgent(client=client)
        result = agent.run("Get historical sales for PROD-001")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_get_historical_sales(self):
        agent = ForecastingAgent(client=MagicMock())
        result = agent._dispatch_tool("get_historical_sales", {"product_id": "PROD-001"})
        assert isinstance(result, dict)
        assert "history" in result

    def test_dispatch_get_historical_sales_with_periods(self):
        agent = ForecastingAgent(client=MagicMock())
        result = agent._dispatch_tool("get_historical_sales", {"product_id": "PROD-001", "periods": 3})
        assert isinstance(result, dict)
        assert len(result["history"]) <= 3

    def test_dispatch_run_demand_forecast(self):
        agent = ForecastingAgent(client=MagicMock())
        result = agent._dispatch_tool("run_demand_forecast", {"product_id": "PROD-001", "horizon_days": 30})
        assert isinstance(result, dict)
        assert "forecasted_units" in result

    def test_dispatch_detect_anomalies(self):
        agent = ForecastingAgent(client=MagicMock())
        data = [100.0, 105.0, 102.0, 98.0, 500.0, 101.0]
        result = agent._dispatch_tool("detect_anomalies", {"metric": "daily_orders", "data_points": data})
        assert isinstance(result, dict)
        assert "anomalies_detected" in result
        assert result["anomalies_detected"] >= 1  # 500.0 should be flagged

    def test_dispatch_publish_forecast(self):
        agent = ForecastingAgent(client=MagicMock())
        forecast = {"forecasted_units": 400, "horizon_days": 30}
        result = agent._dispatch_tool("publish_forecast", {"product_id": "PROD-001", "forecast": forecast})
        assert isinstance(result, dict)
        assert result["status"] == "published"

    def test_dispatch_unknown_tool(self):
        agent = ForecastingAgent(client=MagicMock())
        result = agent._dispatch_tool("unknown_method", {})
        assert "error" in result

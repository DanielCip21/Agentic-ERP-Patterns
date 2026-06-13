"""Unit tests for CRM agents: LeadScoringAgent, CustomerSuccessAgent, SalesPipelineAgent, ChurnPredictionAgent."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentic_erp.crm.lead_scoring_agent import LeadScoringAgent
from agentic_erp.crm.customer_success_agent import CustomerSuccessAgent
from agentic_erp.crm.sales_pipeline_agent import SalesPipelineAgent
from agentic_erp.crm.churn_prediction_agent import ChurnPredictionAgent


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
# LeadScoringAgent
# ---------------------------------------------------------------------------

class TestLeadScoringAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("LEAD-001 scored 85/100 — hot lead.")
        agent = LeadScoringAgent(client=client)
        result = agent.run("Score lead LEAD-001")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_lead",
            {"lead_id": "LEAD-001"},
            "tu_ls_001",
            "Lead LEAD-001 retrieved. Assigning score of 80.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = LeadScoringAgent(client=client)
        result = agent.run("Get details for LEAD-001")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_get_lead(self):
        agent = LeadScoringAgent(client=MagicMock())
        result = agent._dispatch_tool("get_lead", {"lead_id": "LEAD-001"})
        assert isinstance(result, dict)
        assert "error" not in result

    def test_dispatch_get_lead_not_found(self):
        agent = LeadScoringAgent(client=MagicMock())
        result = agent._dispatch_tool("get_lead", {"lead_id": "LEAD-999"})
        assert "error" in result

    def test_dispatch_get_engagement_history(self):
        agent = LeadScoringAgent(client=MagicMock())
        result = agent._dispatch_tool("get_engagement_history", {"lead_id": "LEAD-001"})
        assert isinstance(result, dict)

    def test_dispatch_score_lead(self):
        agent = LeadScoringAgent(client=MagicMock())
        result = agent._dispatch_tool("score_lead", {"lead_id": "LEAD-001", "score": 85, "reasoning": "High engagement"})
        assert isinstance(result, dict)

    def test_dispatch_assign_lead(self):
        agent = LeadScoringAgent(client=MagicMock())
        # Use IDs that exist in the agent's simulated data
        result = agent._dispatch_tool("assign_lead", {"lead_id": "LEAD-001", "rep_id": "REP-01"})
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = LeadScoringAgent(client=MagicMock())
        result = agent._dispatch_tool("mystery_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# CustomerSuccessAgent
# ---------------------------------------------------------------------------

class TestCustomerSuccessAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("2 accounts are at risk with health < 60.")
        agent = CustomerSuccessAgent(client=client)
        result = agent.run("Find all at-risk accounts")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_account_health",
            {"account_id": "ACC-002"},
            "tu_cs_001",
            "ACC-002 health score is 41 — at risk.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = CustomerSuccessAgent(client=client)
        result = agent.run("Check health of ACC-002")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_get_account_health(self):
        agent = CustomerSuccessAgent(client=MagicMock())
        result = agent._dispatch_tool("get_account_health", {"account_id": "ACC-001"})
        assert isinstance(result, dict)

    def test_dispatch_list_at_risk_accounts(self):
        agent = CustomerSuccessAgent(client=MagicMock())
        result = agent._dispatch_tool("list_at_risk_accounts", {"threshold": 60})
        assert isinstance(result, list)

    def test_dispatch_list_at_risk_accounts_no_args(self):
        agent = CustomerSuccessAgent(client=MagicMock())
        result = agent._dispatch_tool("list_at_risk_accounts", {})
        assert isinstance(result, list)

    def test_dispatch_create_success_plan(self):
        agent = CustomerSuccessAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "create_success_plan",
            {"account_id": "ACC-002", "actions": ["Schedule EBR", "Enable feature X"]},
        )
        assert isinstance(result, dict)

    def test_dispatch_log_customer_interaction(self):
        agent = CustomerSuccessAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "log_customer_interaction",
            {"account_id": "ACC-001", "notes": "Discussed renewal options"},
        )
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = CustomerSuccessAgent(client=MagicMock())
        result = agent._dispatch_tool("not_real", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# SalesPipelineAgent
# ---------------------------------------------------------------------------

class TestSalesPipelineAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("3 open opportunities found in the pipeline.")
        agent = SalesPipelineAgent(client=client)
        result = agent.run("Show all open opportunities")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "list_open_opportunities",
            {},
            "tu_sp_001",
            "3 open opportunities: OPP-001, OPP-002, OPP-003.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = SalesPipelineAgent(client=client)
        result = agent.run("List pipeline")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_list_open_opportunities_no_filter(self):
        agent = SalesPipelineAgent(client=MagicMock())
        result = agent._dispatch_tool("list_open_opportunities", {})
        assert isinstance(result, list)

    def test_dispatch_list_open_opportunities_with_stage(self):
        agent = SalesPipelineAgent(client=MagicMock())
        result = agent._dispatch_tool("list_open_opportunities", {"stage": "proposal"})
        assert isinstance(result, list)

    def test_dispatch_list_open_opportunities_with_min_value(self):
        agent = SalesPipelineAgent(client=MagicMock())
        result = agent._dispatch_tool("list_open_opportunities", {"min_value": 50000})
        assert isinstance(result, list)
        assert all(o["value"] >= 50000 for o in result)

    def test_dispatch_advance_opportunity_stage(self):
        agent = SalesPipelineAgent(client=MagicMock())
        result = agent._dispatch_tool("advance_opportunity_stage", {"opp_id": "OPP-001", "new_stage": "negotiation"})
        assert isinstance(result, dict)

    def test_dispatch_generate_forecast(self):
        agent = SalesPipelineAgent(client=MagicMock())
        result = agent._dispatch_tool("generate_forecast", {"period": "Q3-2026"})
        assert "period" in result

    def test_dispatch_recommend_next_action(self):
        agent = SalesPipelineAgent(client=MagicMock())
        result = agent._dispatch_tool("recommend_next_action", {"opp_id": "OPP-001"})
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = SalesPipelineAgent(client=MagicMock())
        result = agent._dispatch_tool("bogus_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# ChurnPredictionAgent
# ---------------------------------------------------------------------------

class TestChurnPredictionAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("2 accounts at high churn risk detected.")
        agent = ChurnPredictionAgent(client=client)
        result = agent.run("Identify high churn risk accounts")
        assert isinstance(result, str)

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_churn_risk_scores",
            {},
            "tu_ch_001",
            "Woodgrove Bank has 85% churn risk.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = ChurnPredictionAgent(client=client)
        result = agent.run("Get churn risk scores")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_dispatch_get_churn_risk_scores(self):
        agent = ChurnPredictionAgent(client=MagicMock())
        result = agent._dispatch_tool("get_churn_risk_scores", {})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_dispatch_analyze_churn_signals(self):
        agent = ChurnPredictionAgent(client=MagicMock())
        result = agent._dispatch_tool("analyze_churn_signals", {"account_id": "ACC-003"})
        assert isinstance(result, dict)
        assert "signals" in result

    def test_dispatch_trigger_retention_playbook(self):
        agent = ChurnPredictionAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "trigger_retention_playbook",
            {"account_id": "ACC-003", "playbook_type": "executive_outreach"},
        )
        assert isinstance(result, dict)
        assert "actions" in result

    def test_dispatch_trigger_invalid_playbook(self):
        agent = ChurnPredictionAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "trigger_retention_playbook",
            {"account_id": "ACC-001", "playbook_type": "nonexistent_playbook"},
        )
        assert "error" in result

    def test_dispatch_log_retention_action(self):
        agent = ChurnPredictionAgent(client=MagicMock())
        result = agent._dispatch_tool(
            "log_retention_action",
            {"account_id": "ACC-002", "action": "Sent renewal discount offer"},
        )
        assert isinstance(result, dict)

    def test_dispatch_unknown_tool(self):
        agent = ChurnPredictionAgent(client=MagicMock())
        result = agent._dispatch_tool("who_am_i", {})
        assert "error" in result

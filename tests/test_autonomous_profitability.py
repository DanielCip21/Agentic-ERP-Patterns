"""Tests for AutonomousProfitabilityAgent and the prompts module."""

import pytest
from unittest.mock import MagicMock

from agentic_erp.agents.autonomous_profitability_agent import (
    AutonomousProfitabilityAgent,
    _analyze_profitability,
    _audit_codebase_quality,
    _optimize_performance,
    _run_security_audit,
    _assess_devops_readiness,
    _generate_profitability_report,
)
from agentic_erp.prompts.autonomous_prompts import (
    AUTONOMOUS_PROFITABILITY_SYSTEM,
    get_persona_prompt,
    _PERSONA_MAP,
)


# ── Prompt library ───────────────────────────────────────────────────────────

class TestPromptLibrary:
    def test_all_personas_registered(self):
        expected = {
            "startup_engineer",
            "codebase_auditor",
            "production_debugger",
            "performance_optimizer",
            "architecture_rebuilder",
            "systems_architect",
            "technical_lead",
            "security_auditor",
            "devops_engineer",
            "autonomous_profitability",
        }
        assert expected == set(_PERSONA_MAP.keys())

    def test_get_persona_prompt_returns_string(self):
        prompt = get_persona_prompt("security_auditor")
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_get_persona_prompt_raises_on_unknown(self):
        with pytest.raises(KeyError):
            get_persona_prompt("nonexistent_persona")

    def test_autonomous_system_prompt_contains_all_personas(self):
        for keyword in [
            "STARTUP ENGINEER",
            "CODEBASE AUDITOR",
            "PRODUCTION DEBUGGER",
            "PERFORMANCE OPTIMIZER",
            "ARCHITECTURE REBUILDER",
            "SYSTEMS ARCHITECT",
            "TECHNICAL LEAD",
            "SECURITY AUDITOR",
            "DEVOPS ENGINEER",
            "PROFITABILITY ANALYST",
        ]:
            assert keyword in AUTONOMOUS_PROFITABILITY_SYSTEM, (
                f"Expected '{keyword}' in AUTONOMOUS_PROFITABILITY_SYSTEM"
            )

    def test_autonomous_system_prompt_mentions_profitability(self):
        assert "profitability" in AUTONOMOUS_PROFITABILITY_SYSTEM.lower()


# ── Tool stub functions ──────────────────────────────────────────────────────

class TestToolStubs:
    def test_analyze_profitability_returns_levers(self):
        result = _analyze_profitability("overall")
        assert "top_levers" in result
        assert len(result["top_levers"]) >= 1
        assert result["top_levers"][0]["rank"] == 1

    def test_analyze_profitability_custom_horizon(self):
        result = _analyze_profitability("revenue", time_horizon_days=7)
        assert result["time_horizon_days"] == 7

    def test_audit_codebase_quality_includes_findings(self):
        result = _audit_codebase_quality("codebase_auditor")
        assert "findings" in result
        assert len(result["findings"]) >= 1

    def test_audit_codebase_quality_applies_persona_directive(self):
        result = _audit_codebase_quality("technical_lead", module="agents/base.py")
        assert result["persona_applied"] == "technical_lead"
        assert result["module"] == "agents/base.py"
        assert "persona_directive" in result

    def test_optimize_performance_returns_bottlenecks(self):
        result = _optimize_performance("inventory_sync", "latency")
        assert "bottlenecks" in result
        assert result["bottlenecks"][0]["gain_percent"] > 0

    def test_security_audit_has_severity_levels(self):
        result = _run_security_audit("full")
        severities = {v["severity"] for v in result["vulnerabilities"]}
        assert "critical" in severities or "high" in severities

    def test_devops_readiness_has_checklist(self):
        result = _assess_devops_readiness("production")
        assert "checklist" in result
        assert "readiness_score" in result
        assert 0 <= result["readiness_score"] <= 100

    def test_generate_report_includes_requested_sections(self):
        sections = ["revenue_levers", "security_risks"]
        result = _generate_profitability_report(sections, "markdown")
        assert result["sections"] == sections
        assert "action_plan" in result
        assert len(result["action_plan"]) >= 1


# ── Agent integration (Anthropic client mocked) ──────────────────────────────

def _make_text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_tool_then_text(tool_name: str, tool_inputs: dict, tool_id: str, final: str):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_inputs
    tool_block.id = tool_id

    tool_resp = MagicMock()
    tool_resp.stop_reason = "tool_use"
    tool_resp.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = final

    text_resp = MagicMock()
    text_resp.stop_reason = "end_turn"
    text_resp.content = [text_block]

    return tool_resp, text_resp


class TestAutonomousProfitabilityAgent:
    def test_system_prompt_is_autonomous(self):
        client = MagicMock()
        agent = AutonomousProfitabilityAgent(client=client)
        assert "profitability" in agent.system_prompt.lower()

    def test_default_model_is_sonnet(self):
        client = MagicMock()
        agent = AutonomousProfitabilityAgent(client=client)
        assert "sonnet" in agent.model.lower()

    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response(
            "Top profit lever: fix overdue receivables ($142k)."
        )
        agent = AutonomousProfitabilityAgent(client=client)
        result = agent.run("What are our top profit levers?")
        assert "profit" in result.lower() or "142" in result

    def test_analyze_profitability_tool_use(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text(
            "analyze_profitability",
            {"focus_area": "cost_reduction"},
            "tu_profit_1",
            "Cost reduction opportunities identified: $83k addressable.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = AutonomousProfitabilityAgent(client=client)
        result = agent.run("Find cost reduction opportunities.")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_security_audit_tool_use(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text(
            "run_security_audit",
            {"scope": "api"},
            "tu_sec_1",
            "Critical: secret logging vulnerability found and remediation plan ready.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = AutonomousProfitabilityAgent(client=client)
        result = agent.run("Audit the API for security vulnerabilities.")
        assert isinstance(result, str)

    def test_full_profitability_report_tool_use(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text(
            "generate_profitability_report",
            {
                "include_sections": ["revenue_levers", "cost_savings", "security_risks"],
                "format": "executive_summary",
            },
            "tu_report_1",
            "Executive summary: $225k in addressable value identified across 4 priority actions.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = AutonomousProfitabilityAgent(client=client)
        result = agent.run("Generate a full profitability report.")
        assert isinstance(result, str)

    def test_unknown_tool_raises(self):
        client = MagicMock()
        agent = AutonomousProfitabilityAgent(client=client)
        with pytest.raises(NotImplementedError):
            agent._dispatch_tool("nonexistent_tool", {})

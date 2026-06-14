"""Pattern: AI-powered Financial Forecasting, Compliance & Risk Modeling agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import forecasting_tools

_TOOLS = [
    {
        "name": "generate_financial_forecast",
        "description": "Generate multi-year financial projections under base, bull, or bear scenarios.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scenario": {"type": "string", "enum": ["base", "bull", "bear"], "description": "Forecast scenario (default: base)"},
                "years_ahead": {"type": "integer", "description": "Years to project (default 3)"},
            },
        },
    },
    {
        "name": "calculate_tax_liability",
        "description": "Calculate estimated corporate tax and VAT liability for a revenue figure in a given jurisdiction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "revenue": {"type": "number", "description": "Annual revenue in USD"},
                "jurisdiction": {"type": "string", "description": "Tax jurisdiction code: US, DE, BR, SG"},
            },
            "required": ["revenue", "jurisdiction"],
        },
    },
    {
        "name": "run_esg_report",
        "description": "Generate an ESG (Environmental, Social, Governance) compliance report with scoring.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "detect_fraud_pattern",
        "description": "Analyze a batch of GL entries for structuring, self-approval, or other fraud patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gl_entries": {
                    "type": "array",
                    "description": "List of GL entry objects with id, amount, vendor, approver fields",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "amount": {"type": "number"},
                            "vendor": {"type": "string"},
                            "approver": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["gl_entries"],
        },
    },
    {
        "name": "model_risk_scenario",
        "description": "Run a financial stress test against a specific macroeconomic shock.",
        "input_schema": {
            "type": "object",
            "properties": {
                "shock_type": {
                    "type": "string",
                    "enum": ["revenue_decline", "cost_spike", "fx_devaluation", "credit_crisis"],
                    "description": "Type of macroeconomic shock to model",
                },
                "magnitude_pct": {"type": "number", "description": "Magnitude of the shock as a percentage (e.g. 20 for 20%)"},
            },
            "required": ["shock_type", "magnitude_pct"],
        },
    },
]

_SYSTEM_PROMPT = """You are an AI-powered Financial Forecasting & Risk Modeling Agent.
Your responsibilities:
- Generate multi-year revenue, EBITDA, and margin forecasts under multiple scenarios
- Calculate tax liabilities across international jurisdictions automatically
- Produce ESG compliance reports and identify sustainability gaps
- Detect GL fraud patterns including structuring and self-approval
- Run financial stress tests to quantify the impact of macroeconomic shocks
Present all findings with clear assumptions and actionable recommendations for the CFO."""


class FinancialForecastingAgent(BaseERPAgent):
    """AI-driven forecasting: multi-scenario projections, tax compliance, ESG, fraud, stress testing."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "generate_financial_forecast":
                return forecasting_tools.generate_financial_forecast(**inputs)
            case "calculate_tax_liability":
                return forecasting_tools.calculate_tax_liability(**inputs)
            case "run_esg_report":
                return forecasting_tools.run_esg_report()
            case "detect_fraud_pattern":
                return forecasting_tools.detect_fraud_pattern(**inputs)
            case "model_risk_scenario":
                return forecasting_tools.model_risk_scenario(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

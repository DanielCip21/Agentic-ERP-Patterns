"""Pattern: AI-powered Sales Pipeline & Project Management agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import sales_tools

_TOOLS = [
    {
        "name": "forecast_revenue_pipeline",
        "description": "Generate an AI-powered revenue forecast from the current sales pipeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "months_ahead": {"type": "integer", "description": "Months ahead to forecast (default 3)"},
            },
        },
    },
    {
        "name": "assess_deal_risk",
        "description": "AI risk assessment for a sales opportunity based on stage, timeline, and customer sentiment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "opportunity_id": {"type": "string", "description": "Opportunity ID (e.g. OPP-001)"},
            },
            "required": ["opportunity_id"],
        },
    },
    {
        "name": "analyze_customer_retention",
        "description": "Analyze customer churn risk using interaction sentiment and behavioral data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "Customer name (e.g. Contoso Ltd)"},
            },
            "required": ["customer_name"],
        },
    },
    {
        "name": "get_project_health",
        "description": "Get health dashboard for an active project: budget utilization, schedule efficiency, and risk flags.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (e.g. PROJ-001)"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "generate_invoice_from_milestone",
        "description": "Auto-generate a project invoice when a milestone is completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "milestone": {"type": "string", "description": "Milestone name (e.g. Phase 1 Completion)"},
                "amount": {"type": "number", "description": "Invoice amount for this milestone"},
            },
            "required": ["project_id", "milestone", "amount"],
        },
    },
]

_SYSTEM_PROMPT = """You are an AI-powered Sales & Project Management Agent.
Your responsibilities:
- Forecast revenue from the current sales pipeline using probability-weighted models
- Identify at-risk deals before they are lost and recommend interventions
- Monitor customer retention signals and escalate churn risks
- Track project health: budget burns, schedule efficiency, and margin risk
- Automatically generate invoices upon milestone completion
Always surface the highest-value, highest-risk items first for management attention."""


class SalesPipelineAgent(BaseERPAgent):
    """AI-driven sales: revenue forecasting, deal risk, customer retention, project health."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "forecast_revenue_pipeline":
                return sales_tools.forecast_revenue_pipeline(**inputs)
            case "assess_deal_risk":
                return sales_tools.assess_deal_risk(**inputs)
            case "analyze_customer_retention":
                return sales_tools.analyze_customer_retention(**inputs)
            case "get_project_health":
                return sales_tools.get_project_health(**inputs)
            case "generate_invoice_from_milestone":
                return sales_tools.generate_invoice_from_milestone(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

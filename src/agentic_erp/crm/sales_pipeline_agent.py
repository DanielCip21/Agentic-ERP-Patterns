"""Pattern: CRM sales pipeline agent managing opportunity stages, forecasting, and next actions."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_OPPORTUNITIES: dict[str, dict] = {
    "OPP-001": {
        "id": "OPP-001",
        "name": "Contoso ERP Expansion",
        "account": "Contoso Ltd",
        "stage": "proposal",
        "value": 75000,
        "close_date": "2026-08-31",
        "rep": "REP-01",
        "probability": 0.6,
    },
    "OPP-002": {
        "id": "OPP-002",
        "name": "Fabrikam CRM Rollout",
        "account": "Fabrikam Inc",
        "stage": "negotiation",
        "value": 130000,
        "close_date": "2026-07-15",
        "rep": "REP-02",
        "probability": 0.8,
    },
    "OPP-003": {
        "id": "OPP-003",
        "name": "Northwind SMB Package",
        "account": "Northwind Traders",
        "stage": "discovery",
        "value": 18000,
        "close_date": "2026-09-30",
        "rep": "REP-01",
        "probability": 0.25,
    },
    "OPP-004": {
        "id": "OPP-004",
        "name": "AdventureWorks Suite",
        "account": "AdventureWorks",
        "stage": "closed_won",
        "value": 95000,
        "close_date": "2026-06-10",
        "rep": "REP-02",
        "probability": 1.0,
    },
}

_STAGE_ORDER = [
    "discovery",
    "qualification",
    "proposal",
    "negotiation",
    "closed_won",
    "closed_lost",
]

_NEXT_ACTIONS: dict[str, str] = {
    "discovery": "Schedule discovery call and send qualification questionnaire",
    "qualification": "Conduct needs assessment and identify decision makers",
    "proposal": "Prepare and deliver tailored proposal with ROI analysis",
    "negotiation": "Address objections, finalise contract terms, loop in legal",
    "closed_won": "Hand off to CSM for onboarding and kickoff scheduling",
    "closed_lost": "Log loss reason and schedule post-mortem review",
}


def _list_open_opportunities(
    stage: str | None = None, min_value: float | None = None
) -> list[dict[str, Any]]:
    results = [
        o
        for o in _OPPORTUNITIES.values()
        if o["stage"] not in ("closed_won", "closed_lost")
    ]
    if stage:
        results = [o for o in results if o["stage"] == stage]
    if min_value is not None:
        results = [o for o in results if o["value"] >= min_value]
    return results


def _advance_opportunity_stage(opp_id: str, new_stage: str) -> dict[str, Any]:
    opp = _OPPORTUNITIES.get(opp_id)
    if not opp:
        return {"error": f"Opportunity {opp_id} not found"}
    if new_stage not in _STAGE_ORDER:
        return {"error": f"Invalid stage '{new_stage}'. Valid: {_STAGE_ORDER}"}
    old_stage = opp["stage"]
    opp["stage"] = new_stage
    opp["updated_at"] = datetime.utcnow().isoformat()
    return {
        "opp_id": opp_id,
        "previous_stage": old_stage,
        "new_stage": new_stage,
        "updated_at": opp["updated_at"],
    }


def _generate_forecast(period: str) -> dict[str, Any]:
    open_opps = [
        o
        for o in _OPPORTUNITIES.values()
        if o["stage"] not in ("closed_won", "closed_lost")
    ]
    weighted_pipeline = sum(o["value"] * o["probability"] for o in open_opps)
    committed = sum(o["value"] for o in open_opps if o["stage"] == "negotiation")
    return {
        "period": period,
        "open_opportunities": len(open_opps),
        "total_pipeline_value": sum(o["value"] for o in open_opps),
        "weighted_forecast": round(weighted_pipeline, 2),
        "committed_revenue": committed,
        "generated_at": datetime.utcnow().isoformat(),
    }


def _recommend_next_action(opp_id: str) -> dict[str, Any]:
    opp = _OPPORTUNITIES.get(opp_id)
    if not opp:
        return {"error": f"Opportunity {opp_id} not found"}
    action = _NEXT_ACTIONS.get(
        opp["stage"], "Review opportunity and consult with manager"
    )
    return {
        "opp_id": opp_id,
        "current_stage": opp["stage"],
        "recommended_action": action,
    }


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "list_open_opportunities",
        "description": "List open (non-closed) opportunities, optionally filtered by stage and minimum value.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "description": "Pipeline stage to filter by (e.g. discovery, proposal)",
                },
                "min_value": {
                    "type": "number",
                    "description": "Minimum opportunity value in USD",
                },
            },
            "required": [],
        },
    },
    {
        "name": "advance_opportunity_stage",
        "description": "Move an opportunity to the next (or specified) pipeline stage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "opp_id": {"type": "string", "description": "Opportunity ID"},
                "new_stage": {"type": "string", "description": "Target stage"},
            },
            "required": ["opp_id", "new_stage"],
        },
    },
    {
        "name": "generate_forecast",
        "description": "Generate a revenue forecast summary for the given period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Forecast period label (e.g. Q3-2026)",
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "recommend_next_action",
        "description": "Recommend the best next sales action for an opportunity given its current stage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "opp_id": {"type": "string", "description": "Opportunity ID"},
            },
            "required": ["opp_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Sales Pipeline Management Agent for a B2B software company.
Your responsibilities:
1. Monitor and review open opportunities across pipeline stages
2. Advance opportunities to appropriate stages based on sales activity
3. Generate revenue forecasts using probability-weighted pipeline data
4. Recommend the best next action for each opportunity

Prioritise high-value deals in negotiation stage. Flag stalled deals (no activity >14 days).
Provide forecasts with both committed and weighted pipeline figures."""


class SalesPipelineAgent(BaseERPAgent):
    """Manages sales pipeline stages, forecasting, and next-action recommendations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "list_open_opportunities":
                return _list_open_opportunities(**inputs)
            case "advance_opportunity_stage":
                return _advance_opportunity_stage(**inputs)
            case "generate_forecast":
                return _generate_forecast(**inputs)
            case "recommend_next_action":
                return _recommend_next_action(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

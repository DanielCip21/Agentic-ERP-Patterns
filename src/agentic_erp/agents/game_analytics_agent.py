"""Pattern: Game revenue & player behaviour analytics agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import analytics_tools

_TOOLS = [
    {
        "name": "get_player_cohort",
        "description": "Retrieve player cohort metrics: retention rates, average LTV, churn rate, and cohort health.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cohort_id": {"type": "string", "description": "Cohort ID (e.g. C-2024Q1)"},
            },
            "required": ["cohort_id"],
        },
    },
    {
        "name": "get_revenue_breakdown",
        "description": "Get a detailed revenue breakdown (IAP, subscriptions, ads, battle pass) for a game in a given period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "game_id": {"type": "string", "description": "Game ID (e.g. GAME-01)"},
                "period": {"type": "string", "description": "Reporting period (e.g. '2026-Q1', '2026-Q2')"},
            },
            "required": ["game_id", "period"],
        },
    },
    {
        "name": "forecast_game_revenue",
        "description": "Generate an AI-driven monthly revenue forecast for a game over a specified horizon.",
        "input_schema": {
            "type": "object",
            "properties": {
                "game_id": {"type": "string"},
                "horizon_months": {"type": "integer", "description": "Number of months to forecast", "default": 12},
            },
            "required": ["game_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Game Revenue & Player Analytics Agent for a global gaming company.
Your responsibilities:
1. Analyse player cohort health: retention, LTV, churn, and total cohort value.
2. Break down revenue by stream (IAP, subscriptions, advertising, battle pass) per game and period.
3. Generate forward-looking revenue forecasts by game title and genre growth rate.
4. Identify underperforming cohorts (WEAK health) and revenue streams declining quarter-over-quarter.
5. Recommend monetisation optimisations based on genre benchmarks and LTV data.
Be specific about dollar amounts and percentages. Flag any cohort with day-30 retention below 20%."""


class GameRevenueAnalyticsAgent(BaseERPAgent):
    """Analyses player behaviour and forecasts game revenue streams."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_player_cohort":
                return analytics_tools.get_player_cohort(**inputs)
            case "get_revenue_breakdown":
                return analytics_tools.get_revenue_breakdown(**inputs)
            case "forecast_game_revenue":
                return analytics_tools.forecast_game_revenue(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

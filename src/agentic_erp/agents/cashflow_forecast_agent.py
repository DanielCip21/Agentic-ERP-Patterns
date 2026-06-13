"""Pattern: AI-driven multi-currency cash flow & FX risk forecasting agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import finance_tools

_TOOLS = [
    {
        "name": "get_account_balances",
        "description": "Retrieve current account balances across all currencies, or for a specific currency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "currency": {"type": "string", "description": "Optional: filter to a specific currency (USD, EUR, SGD, JPY)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_fx_rates",
        "description": "Get current FX exchange rates from a base currency to one or more target currencies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base_currency": {"type": "string", "description": "Source currency (e.g. USD)"},
                "target_currencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of target currencies (e.g. ['EUR', 'SGD', 'JPY'])",
                },
            },
            "required": ["base_currency", "target_currencies"],
        },
    },
    {
        "name": "forecast_cash_flow",
        "description": "Run an AI cash flow forecast for the next N days under a given economic scenario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "horizon_days": {"type": "integer", "description": "Forecast horizon in days (e.g. 90, 180)", "default": 90},
                "scenario": {"type": "string", "description": "Economic scenario: optimistic, base, or pessimistic", "enum": ["optimistic", "base", "pessimistic"]},
            },
            "required": [],
        },
    },
]

_SYSTEM_PROMPT = """You are a Cash Flow & FX Risk Forecasting Agent for a global gaming company
with treasury operations in USD, EUR, SGD, and JPY.
Your responsibilities:
1. Assess current multi-currency account balances and their USD equivalents.
2. Retrieve FX rates to identify currency exposure and hedging needs.
3. Run forward-looking cash flow forecasts under base, optimistic, and pessimistic scenarios.
4. Highlight FX risk positions (large EUR or JPY holdings) and recommend hedging windows.
5. Summarise net cash flow outlook and flag any periods of projected negative cash flow.
Be quantitative. Always express recommendations in USD equivalents."""


class CashFlowForecastAgent(BaseERPAgent):
    """Forecasts multi-currency cash flow and FX risk exposure."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_account_balances":
                return finance_tools.get_account_balances(**inputs)
            case "get_fx_rates":
                return finance_tools.get_fx_rates(**inputs)
            case "forecast_cash_flow":
                return finance_tools.forecast_cash_flow(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

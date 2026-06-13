"""Pattern: AI-powered Accounts Receivable & Collections agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import ar_tools

_TOOLS = [
    {
        "name": "forecast_collections",
        "description": "AI forecast of expected collections for the next N days based on receivables aging.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Days ahead to forecast (default 30)"},
            },
        },
    },
    {
        "name": "score_customer_credit",
        "description": "Score a customer's creditworthiness using payment history and credit data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID (e.g. CUST-001)"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "list_overdue_receivables",
        "description": "List all overdue AR items, optionally filtered by minimum days overdue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_days_overdue": {"type": "integer", "description": "Minimum days overdue to include (default 0)"},
            },
        },
    },
    {
        "name": "apply_cash_payment",
        "description": "Apply a cash payment to an open AR record.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ar_id": {"type": "string", "description": "AR record ID (e.g. AR-001)"},
                "payment_amount": {"type": "number", "description": "Payment amount in USD"},
            },
            "required": ["ar_id", "payment_amount"],
        },
    },
    {
        "name": "generate_collection_reminder",
        "description": "Generate an AI-drafted collection reminder message for a customer with outstanding balances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
            },
            "required": ["customer_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are an AI-powered Accounts Receivable & Collections Agent.
Your responsibilities:
- Forecast expected cash collections and identify high-risk receivables
- Score customer creditworthiness and recommend credit limit adjustments
- Prioritize collection efforts on the highest-risk, longest-overdue accounts
- Apply payments to open invoices and confirm cleared balances
- Draft professional collection reminder messages tailored to urgency level
Always prioritize maintaining customer relationships while protecting cash flow."""


class ARCollectionsAgent(BaseERPAgent):
    """AI-driven AR collections: forecasting, credit scoring, cash application."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "forecast_collections":
                return ar_tools.forecast_collections(**inputs)
            case "score_customer_credit":
                return ar_tools.score_customer_credit(**inputs)
            case "list_overdue_receivables":
                return ar_tools.list_overdue_receivables(**inputs)
            case "apply_cash_payment":
                return ar_tools.apply_cash_payment(**inputs)
            case "generate_collection_reminder":
                return ar_tools.generate_collection_reminder(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

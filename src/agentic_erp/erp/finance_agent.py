"""Pattern: Tool-use agent for finance — AR/AP reconciliation, expense management, payment scheduling."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.erp import finance_tools

_TOOLS = [
    {
        "name": "list_outstanding_invoices",
        "description": "List all outstanding invoices filtered by minimum days overdue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_overdue": {
                    "type": "integer",
                    "description": "Minimum number of days overdue. Default 0 returns all open invoices.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "categorize_expense",
        "description": "Automatically categorize an expense by description and amount using AI-based classification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Expense description or vendor name",
                },
                "amount": {"type": "number", "description": "Expense amount in USD"},
            },
            "required": ["description", "amount"],
        },
    },
    {
        "name": "schedule_payment",
        "description": "Schedule a payment for an outstanding invoice on a specific date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "Invoice ID to pay"},
                "date": {
                    "type": "string",
                    "description": "Payment date in YYYY-MM-DD format",
                },
            },
            "required": ["invoice_id", "date"],
        },
    },
    {
        "name": "reconcile_account",
        "description": "Reconcile a financial account by comparing book balance against bank statement.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "Account ID (e.g. ACC-1001)",
                },
            },
            "required": ["account_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Finance Automation Agent for an enterprise ERP system.
Your responsibilities:
1. Monitor accounts receivable — identify overdue invoices and escalate appropriately
2. Categorize expenses for accurate financial reporting and tax compliance
3. Schedule vendor payments to optimize cash flow and avoid late fees
4. Reconcile financial accounts to ensure book and bank balances match

Prioritize invoices more than 30 days overdue. Flag uncategorized expenses for manual review.
Always present financial data with proper formatting (currency, dates)."""


class FinanceAgent(BaseERPAgent):
    """Handles AR/AP reconciliation, expense categorization, and payment scheduling."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "list_outstanding_invoices":
                return finance_tools.list_outstanding_invoices(**inputs)
            case "categorize_expense":
                return finance_tools.categorize_expense(**inputs)
            case "schedule_payment":
                return finance_tools.schedule_payment(
                    invoice_id=inputs["invoice_id"],
                    payment_date=inputs["date"],
                )
            case "reconcile_account":
                return finance_tools.reconcile_account(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

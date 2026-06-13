"""Pattern: AI-powered General Ledger reconciliation and financial automation agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import gl_tools

_TOOLS = [
    {
        "name": "reconcile_gl_accounts",
        "description": "Run AI-powered GL reconciliation for a given accounting period. Detects mismatches and pending entries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Accounting period in YYYY-MM format (e.g. 2025-01)"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "detect_financial_anomalies",
        "description": "Detect anomalies and fraud signals in GL entries. Optionally filter by account number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "GL account number (optional). Omit to scan all accounts."},
            },
        },
    },
    {
        "name": "categorize_expenses",
        "description": "Use AI to auto-categorize an expense to the correct GL account based on its description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Expense description text"},
                "amount": {"type": "number", "description": "Expense amount in USD"},
            },
            "required": ["description", "amount"],
        },
    },
    {
        "name": "get_budget_vs_actual",
        "description": "Retrieve budget vs actual variance analysis for a given period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Budget period (e.g. 2025-Q1)"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "post_journal_entry",
        "description": "Post a correcting or adjusting journal entry to the GL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account": {"type": "string"},
                "debit": {"type": "number"},
                "credit": {"type": "number"},
                "description": {"type": "string"},
            },
            "required": ["account", "debit", "credit", "description"],
        },
    },
    {
        "name": "get_trial_balance",
        "description": "Retrieve the current trial balance showing all account balances.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

_SYSTEM_PROMPT = """You are an AI-powered General Ledger Agent for an enterprise ERP system.
Your responsibilities:
- Reconcile GL accounts and identify posting mismatches
- Detect anomalies and potential fraud in journal entries
- Auto-categorize expenses to the correct GL accounts using AI classification
- Analyze budget vs actual variances and surface insights
- Post correcting journal entries when needed
Always explain your findings clearly and recommend corrective actions."""


class GLAutomationAgent(BaseERPAgent):
    """AI-driven GL reconciliation, expense categorization, and anomaly detection."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "reconcile_gl_accounts":
                return gl_tools.reconcile_gl_accounts(**inputs)
            case "detect_financial_anomalies":
                return gl_tools.detect_financial_anomalies(**inputs)
            case "categorize_expenses":
                return gl_tools.categorize_expenses(**inputs)
            case "get_budget_vs_actual":
                return gl_tools.get_budget_vs_actual(**inputs)
            case "post_journal_entry":
                return gl_tools.post_journal_entry(**inputs)
            case "get_trial_balance":
                return gl_tools.get_trial_balance()
            case _:
                return {"error": f"Unknown tool: {name}"}

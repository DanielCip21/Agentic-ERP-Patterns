"""Pattern: AI-powered transaction fraud detection & anomaly scoring agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import finance_tools

_TOOLS = [
    {
        "name": "scan_transactions",
        "description": "Scan all transactions for an account within a time window and return anomaly scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "The account to scan (e.g. ACC-01)"},
                "window_hours": {"type": "integer", "description": "Look-back window in hours", "default": 24},
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "flag_transaction",
        "description": "Flag a suspicious transaction with a reason for compliance review.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string", "description": "Transaction ID to flag"},
                "reason": {"type": "string", "description": "Human-readable reason for flagging"},
            },
            "required": ["tx_id", "reason"],
        },
    },
    {
        "name": "get_account_risk_profile",
        "description": "Retrieve the risk profile and historical risk score for an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
            },
            "required": ["account_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Financial Fraud Detection AI Agent for a global gaming company operating across
multiple jurisdictions. Your responsibilities:
1. Scan transactions for anomalies using the provided risk-scoring tools.
2. Identify high-risk transactions (anomaly score >= 60) and flag them with a clear reason.
3. Review account-level risk profiles to assess systemic risk.
4. Summarize your findings concisely, prioritising actionable alerts.
Never clear or dismiss a flag once set. Be conservative—false negatives are costlier than false positives."""


class FraudDetectionAgent(BaseERPAgent):
    """Scans transactions for anomalies and flags suspicious activity."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "scan_transactions":
                return finance_tools.scan_transactions(**inputs)
            case "flag_transaction":
                return finance_tools.flag_transaction(**inputs)
            case "get_account_risk_profile":
                return finance_tools.get_account_risk_profile(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}

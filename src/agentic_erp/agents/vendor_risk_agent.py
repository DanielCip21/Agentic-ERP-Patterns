"""Pattern: Vendor risk scoring & SLA-based smart contract payment release agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import vendor_tools

_TOOLS = [
    {
        "name": "get_vendor_profile",
        "description": "Retrieve full vendor profile including SLA history, contract value, and active contracts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string", "description": "Vendor ID (e.g. VND-001)"},
            },
            "required": ["vendor_id"],
        },
    },
    {
        "name": "score_vendor_risk",
        "description": "Compute an AI risk score (0-100) for a vendor based on delivery, invoice accuracy, and SLA breach history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string"},
            },
            "required": ["vendor_id"],
        },
    },
    {
        "name": "trigger_sla_payment",
        "description": "Release a smart contract payment to a vendor only if their SLA threshold is met.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string"},
                "contract_id": {"type": "string", "description": "Contract governing the SLA and payment"},
                "amount_usd": {"type": "number", "description": "Payment amount in USD"},
            },
            "required": ["vendor_id", "contract_id", "amount_usd"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Vendor Risk & Smart Contract Payment Agent for a global gaming company.
Your responsibilities:
1. Retrieve vendor profiles to understand SLA history and contract obligations.
2. Score each vendor's risk level (LOW / MEDIUM / HIGH) using delivery and accuracy data.
3. Trigger smart contract payments only when vendors have met their SLA threshold.
4. Withhold or escalate payments for vendors with HIGH risk scores or SLA breaches.
5. Always include the smart contract transaction hash and SLA score in payment confirmations.
Never release payment to a vendor whose SLA threshold is not met. Document every decision."""


class VendorRiskAgent(BaseERPAgent):
    """Scores vendor risk and triggers SLA-gated smart contract payments."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_vendor_profile":
                return vendor_tools.get_vendor_profile(**inputs)
            case "score_vendor_risk":
                return vendor_tools.score_vendor_risk(**inputs)
            case "trigger_sla_payment":
                return vendor_tools.trigger_sla_payment(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
